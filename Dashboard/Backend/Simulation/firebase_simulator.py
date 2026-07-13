"""
firebase_simulator.py
─────────────────────
Pushes simulated sensor data to Firebase Realtime Database every 2 seconds.
Run this until your ESP32 is connected to Firebase.

Usage:
    python firebase_simulator.py

Requirements:
    pip install requests
"""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import requests
import json
import time
import random
import math
from datetime import datetime

# ── FIREBASE CONFIG ──────────────────────────────────────────────────────────
# Paste your Firebase Realtime Database URL here (from Firebase console)
# Example: https://nirikshak-default-rtdb.firebaseio.com
FIREBASE_URL = "https://nirikshak-project-default-rtdb.firebaseio.com/"

# If your database rules require auth, paste your Web API key here
# Leave empty string if your rules are set to public read/write
FIREBASE_SECRET = ""

# ── FAULT LIMITS (same as dashboard) ─────────────────────────────────────────
LIMITS = {
    "temperature": 65,    # °C
    "current":     10,    # A
    "voltage":     230,   # V
    "vibration":   10,    # g
    "proximity":   2000,  # rpm
}

# ── SIMULATION CYCLES ─────────────────────────────────────────────────────────
# Every N readings it will spike to simulate a fault, then return to normal
NORMAL_READINGS  = 15   # readings before spike
WARNING_READINGS = 5    # readings at warning level
FAULT_READINGS   = 3    # readings at fault level

# ── BASE VALUES (normal operating range) ────────────────────────────────────
BASE = {
    "temperature": 42.0,   # normal ~40-50°C
    "current":     5.5,    # normal ~4-7A
    "voltage":     218.0,  # normal ~210-225V
    "vibration":   1.2,    # normal ~0.8-2.0g
    "proximity":   1200,   # normal ~900-1400rpm
}

# ── ML PROBABILITY SIMULATION ────────────────────────────────────────────────
def calc_probability(values, cycle_phase):
    """Simulate ML model fault probability based on sensor values."""
    score = 0.0
    for key, limit in LIMITS.items():
        ratio = values[key] / limit
        if ratio >= 1.0:
            score += 35
        elif ratio >= 0.85:
            score += 15
        elif ratio >= 0.70:
            score += 5

    # Add noise
    score += random.uniform(-3, 3)

    # Phase-based boost
    if cycle_phase == "fault":
        score += random.uniform(10, 20)
    elif cycle_phase == "warning":
        score += random.uniform(5, 12)

    return round(min(99.9, max(0.1, score)), 1)


def get_status(probability):
    if probability >= 65:
        return "Fault"
    elif probability >= 35:
        return "Warning"
    return "Normal"


# ── GENERATE ONE READING ─────────────────────────────────────────────────────
def generate_reading(cycle_index):
    """Generate sensor values based on the current cycle phase."""
    total_cycle = NORMAL_READINGS + WARNING_READINGS + FAULT_READINGS
    pos = cycle_index % total_cycle

    if pos < NORMAL_READINGS:
        phase = "normal"
        multiplier = 1.0
        noise_scale = 0.05
    elif pos < NORMAL_READINGS + WARNING_READINGS:
        phase = "warning"
        multiplier = 0.85   # ~85% of limit
        noise_scale = 0.04
    else:
        phase = "fault"
        multiplier = 1.08   # just over limit
        noise_scale = 0.03

    def jitter(base, scale=noise_scale):
        return base + random.gauss(0, base * scale)

    # Sine wave for natural oscillation
    t = time.time()
    wave = math.sin(t * 0.3) * 0.02  # ±2% oscillation

    if phase == "normal":
        values = {
            "temperature": round(jitter(BASE["temperature"]) * (1 + wave), 2),
            "current":     round(jitter(BASE["current"])     * (1 + wave), 2),
            "voltage":     round(jitter(BASE["voltage"])     * (1 + wave * 0.5), 2),
            "vibration":   round(jitter(BASE["vibration"])   * (1 + wave), 4),
            "proximity":   round(jitter(BASE["proximity"])   * (1 + wave)),
            "humidity":    round(random.uniform(42, 58), 1),
        }
    elif phase == "warning":
        values = {
            "temperature": round(LIMITS["temperature"] * multiplier + jitter(2, 0.1), 2),
            "current":     round(LIMITS["current"]     * multiplier + jitter(0.3, 0.05), 2),
            "voltage":     round(LIMITS["voltage"]     * multiplier + jitter(5, 0.02), 2),
            "vibration":   round(LIMITS["vibration"]   * multiplier + jitter(0.3, 0.03), 4),
            "proximity":   round(LIMITS["proximity"]   * multiplier + jitter(50, 0.02)),
            "humidity":    round(random.uniform(55, 70), 1),
        }
    else:  # fault
        values = {
            "temperature": round(LIMITS["temperature"] * multiplier + jitter(3, 0.05), 2),
            "current":     round(LIMITS["current"]     * multiplier + jitter(0.5, 0.05), 2),
            "voltage":     round(LIMITS["voltage"]     * multiplier + jitter(8, 0.03), 2),
            "vibration":   round(LIMITS["vibration"]   * multiplier + jitter(0.5, 0.03), 4),
            "proximity":   round(LIMITS["proximity"]   * multiplier + jitter(80, 0.02)),
            "humidity":    round(random.uniform(68, 85), 1),
        }

    probability = calc_probability(values, phase)
    status      = get_status(probability)

    payload = {
        **values,
        "probability": probability,
        "status":      status,
        "timestamp":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source":      "simulator",
        "cycle_phase": phase,
        "ml_completed_timestamp": time.time() * 1000.0,
        "inference_latency": 0.05
    }
    return payload


# ── PUSH TO FIREBASE ─────────────────────────────────────────────────────────
def push_to_firebase(data):
    """
    Writes to TWO locations in Firebase:
      1. /sensors/latest   — always overwritten (dashboard reads this)
      2. /sensors/history  — appended as new child (log/history)
    """
    headers = {"Content-Type": "application/json"}
    params  = {"auth": FIREBASE_SECRET} if FIREBASE_SECRET else {}

    # 1. Overwrite /sensors/latest (PUT)
    latest_url = f"{FIREBASE_URL}/sensors/latest.json"
    r1 = requests.put(latest_url, data=json.dumps(data), headers=headers, params=params, timeout=8)

    # 2. Append to /sensors/history (POST creates unique key)
    history_url = f"{FIREBASE_URL}/sensors/history.json"
    r2 = requests.post(history_url, data=json.dumps(data), headers=headers, params=params, timeout=8)

    return r1.status_code, r2.status_code


# ── MAIN LOOP ────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  Nirikshak — Firebase Sensor Simulator")
    print("=" * 60)

    if "YOUR_PROJECT_ID" in FIREBASE_URL:
        print("\n❌  ERROR: Please update FIREBASE_URL in this file.")
        print("   Go to Firebase Console → Realtime Database → copy URL")
        print("   Example: https://nirikshak-abc12-default-rtdb.firebaseio.com")
        return

    print(f"\n🔥  Target: {FIREBASE_URL}")
    print(f"⏱   Interval: 2 seconds")
    print(f"🔄  Cycle: {NORMAL_READINGS} normal → {WARNING_READINGS} warning → {FAULT_READINGS} fault readings")
    print(f"\n{'─'*60}")
    print(f"{'#':>4}  {'Phase':<10}  {'Temp':>6}  {'Curr':>6}  {'Volt':>7}  {'Vib':>7}  {'Prox':>6}  {'ML%':>6}  Status")
    print(f"{'─'*60}")

    cycle = 0
    pushed = 0
    errors = 0

    try:
        while True:
            data = generate_reading(cycle)

            try:
                s1, s2 = push_to_firebase(data)
                ok = (s1 in [200,201]) and (s2 in [200,201])
                pushed += 1 if ok else 0
                errors += 0 if ok else 1
                status_sym = "✅" if ok else f"❌ ({s1},{s2})"
            except requests.exceptions.ConnectionError:
                status_sym = "❌ No connection"
                errors += 1
            except requests.exceptions.Timeout:
                status_sym = "⏱ Timeout"
                errors += 1
            except Exception as e:
                status_sym = f"❌ {e}"
                errors += 1

            phase_label = data["cycle_phase"].upper()
            phase_color = {"NORMAL":"🟢","WARNING":"🟡","FAULT":"🔴"}.get(phase_label,"⚪")

            print(
                f"{cycle+1:>4}  {phase_color} {phase_label:<8}  "
                f"{data['temperature']:>6.1f}  "
                f"{data['current']:>6.1f}  "
                f"{data['voltage']:>7.1f}  "
                f"{data['vibration']:>7.3f}  "
                f"{data['proximity']:>6}  "
                f"{data['probability']:>5.1f}%  "
                f"{data['status']:<8} {status_sym}",
                flush=True
            )

            cycle += 1
            time.sleep(2)

    except KeyboardInterrupt:
        print(f"\n\n{'─'*60}")
        print(f"  Stopped by user.")
        print(f"  Total pushed : {pushed}")
        print(f"  Total errors : {errors}")
        print(f"{'─'*60}\n")


if __name__ == "__main__":
    main()