#!/usr/bin/env python3
# ============================================================
#  firebase_publisher.py — Push sensor data to Firebase RTDB
#  Simulates ESP32 publishing → Firebase instead of MQTT
#
#  Run alongside app.py:
#      python firebase_publisher.py
#
#  ESP32 equivalent: use HTTPClient to PUT the same JSON to
#      https://YOUR-PROJECT.firebaseio.com/sensors/latest.json
# ============================================================

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import urllib.request, json, time, random, os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# ── ✏️  FILL THESE IN ──────────────────────────────────────
FIREBASE_URL = "https://YOUR-PROJECT-ID-default-rtdb.firebaseio.com"
AUTH_TOKEN   = ""   # blank = public rules (dev mode)
# ───────────────────────────────────────────────────────────

# Fault limits (must match config.py)
LIMITS = {
    "temperature": 65,
    "current":     10,
    "voltage":     230,
    "vibration":   10,
    "proximity":   2000
}

def fb_put(path, data):
    url = FIREBASE_URL.rstrip("/") + path + ".json"
    if AUTH_TOKEN:
        url += f"?auth={AUTH_TOKEN}"
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode(),
        method="PUT",
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read())

def fb_post(path, data):
    url = FIREBASE_URL.rstrip("/") + path + ".json"
    if AUTH_TOKEN:
        url += f"?auth={AUTH_TOKEN}"
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode(),
        method="POST",
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read())

def rule_based_status(temp, curr, volt, vib, prox):
    faults = (
        temp  >= LIMITS["temperature"] or
        curr  >= LIMITS["current"]     or
        volt  >= LIMITS["voltage"]     or
        vib   >= LIMITS["vibration"]   or
        prox  >= LIMITS["proximity"]
    )
    warns = (
        temp  >= LIMITS["temperature"] * 0.8 or
        curr  >= LIMITS["current"]     * 0.8 or
        volt  >= LIMITS["voltage"]     * 0.8 or
        vib   >= LIMITS["vibration"]   * 0.8 or
        prox  >= LIMITS["proximity"]   * 0.8
    )
    if faults: return {"fault": 1, "probability": 91.0, "status": "Fault"}
    if warns:  return {"fault": 0, "probability": 48.0, "status": "Warning"}
    return      {"fault": 0, "probability":  6.0, "status": "Normal"}

def main():
    if "YOUR-PROJECT-ID" in FIREBASE_URL:
        print("❌  Set FIREBASE_URL in this file first.")
        sys.exit(1)

    print(f"🔥 Firebase publisher started → {FIREBASE_URL}")
    print("Press Ctrl+C to stop\n")

    cycle = 0
    while True:
        cycle += 1

        # ── Generate readings ──
        if cycle % 30 == 0:
            mode  = "FAULT"
            temp  = round(random.uniform(68, 90),  2)
            curr  = round(random.uniform(11, 15),  2)
            volt  = round(random.uniform(235, 260), 1)
            vib   = round(random.uniform(10.5, 14), 3)
            prox  = round(random.uniform(2100, 2800))
        elif cycle % 15 == 0:
            mode  = "WARNING"
            temp  = round(random.uniform(54, 65),  2)
            curr  = round(random.uniform(8.2, 10), 2)
            volt  = round(random.uniform(190, 230), 1)
            vib   = round(random.uniform(8, 10),   3)
            prox  = round(random.uniform(1620, 2000))
        else:
            mode  = "NORMAL"
            temp  = round(random.uniform(35, 52),  2)
            curr  = round(random.uniform(3.5, 7.5), 2)
            volt  = round(random.uniform(210, 226), 1)
            vib   = round(random.uniform(0.3, 4),  3)
            prox  = round(random.uniform(800, 1600))

        humidity = round(random.uniform(42, 70), 1)
        result   = rule_based_status(temp, curr, volt, vib, prox)

        record = {
            "timestamp":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "temperature": temp,
            "current":     curr,
            "voltage":     volt,
            "vibration":   vib,
            "proximity":   int(prox),
            "humidity":    humidity,
            "probability": result["probability"],
            "status":      result["status"],
            "fault":       result["fault"],
            "ml_completed_timestamp": time.time() * 1000.0,
            "inference_latency": 0.0
        }

        try:
            # Overwrite /sensors/latest  (dashboard polls this)
            fb_put("/sensors/latest", record)

            # Append to /sensors/history (keeps a log)
            fb_post("/sensors/history", record)

            print(f"[{mode:<7}] Temp={temp}°C  Curr={curr}A  Volt={volt}V  "
                  f"Vib={vib}g  Prox={int(prox)}rpm  → Firebase ✅")
        except Exception as e:
            print(f"[ERROR] Firebase write failed: {e}")

        time.sleep(2)

if __name__ == "__main__":
    main()