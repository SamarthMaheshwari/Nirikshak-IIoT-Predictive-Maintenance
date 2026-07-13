#!/usr/bin/env python3
# ============================================================
#  firebase_setup.py — One-time Firebase setup + seed data
#  Run ONCE after creating your Firebase project:
#      python firebase_setup.py
#
#  What it does:
#    1. Writes sample sensor reading to /sensors/latest
#    2. Writes same reading into /sensors/history/{auto-id}
#    3. Writes /sensors/config  (limits reference)
#    4. Prints your dashboard polling URL
# ============================================================

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import urllib.request, urllib.error, json
from datetime import datetime

# ── ✏️  FILL THESE IN (from your Firebase project settings) ──
FIREBASE_URL = "https://nirikshak-project-default-rtdb.firebaseio.com/" 

# Leave AUTH_TOKEN blank if you set Rules to public read/write (for dev)
AUTH_TOKEN   = ""          # Firebase Database Secret or empty string
# ──────────────────────────────────────────────────────────────

def fb_url(path):
    base = FIREBASE_URL.rstrip("/")
    auth = f"?auth={AUTH_TOKEN}" if AUTH_TOKEN else ""
    return f"{base}{path}.json{auth}"

def put(path, data):
    req = urllib.request.Request(
        fb_url(path),
        data=json.dumps(data).encode(),
        method="PUT",
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def post(path, data):
    req = urllib.request.Request(
        fb_url(path),
        data=json.dumps(data).encode(),
        method="POST",
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def main():
    if "YOUR-PROJECT-ID" in FIREBASE_URL:
        print("❌  Please edit firebase_setup.py and set your FIREBASE_URL first.")
        print("    Find it in Firebase Console → Project Settings → General → Your apps")
        sys.exit(1)

    print(f"🔥 Connecting to: {FIREBASE_URL}")

    # ── Sample reading (Normal state) ──
    sample = {
        "timestamp":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "temperature": 44.2,
        "current":     5.1,
        "voltage":     219.4,
        "vibration":   0.83,
        "proximity":   1420,
        "humidity":    56.3,
        "probability": 7.5,
        "status":      "Normal",
        "fault":       0
    }

    print("\n📡 Writing sample data to /sensors/latest ...")
    put("/sensors/latest", sample)
    print("   ✅ Done")

    print("📋 Writing sample data to /sensors/history ...")
    result = post("/sensors/history", sample)
    print(f"   ✅ Done (key: {result.get('name','?')})")

    # ── Config / limits node ──
    limits = {
        "temperature": 65,
        "current":     10,
        "voltage":     230,
        "vibration":   10,
        "proximity":   2000
    }
    print("⚙️  Writing fault limits to /sensors/config ...")
    put("/sensors/config", limits)
    print("   ✅ Done")

    print("\n" + "="*60)
    print("🎉  Firebase setup complete!")
    print("="*60)
    print(f"\nDashboard polling URL (paste into Cloud JSON panel):")
    print(f"  {FIREBASE_URL}/sensors/latest.json")
    print(f"\nHistory URL:")
    print(f"  {FIREBASE_URL}/sensors/history.json")
    print("\nSample data written:")
    for k, v in sample.items():
        print(f"  {k:<14}: {v}")

if __name__ == "__main__":
    main()