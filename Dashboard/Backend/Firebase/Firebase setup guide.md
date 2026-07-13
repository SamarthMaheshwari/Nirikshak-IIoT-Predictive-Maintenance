# 🔥 Nirikshak — Firebase Realtime Database Setup Guide

## What you get after this guide
- Firebase RTDB storing live sensor data at `/sensors/latest`
- History log at `/sensors/history`
- Dashboard auto-polling Firebase every 2–3 seconds
- ESP32 pushing data directly to Firebase over WiFi

---

## Step 1 — Create a Firebase Project

1. Go to **https://console.firebase.google.com**
2. Click **"Add project"**
3. Name it: `nirikshak` (or anything)
4. Disable Google Analytics (not needed) → **Create project**

---

## Step 2 — Enable Realtime Database

1. In the left sidebar → **Build → Realtime Database**
2. Click **"Create Database"**
3. Choose location: **us-central1** (or closest to you)
4. Start in **test mode** (allows open read/write for 30 days)
5. Click **Enable**

Your database URL will look like:
```
https://nirikshak-default-rtdb.firebaseio.com
```
**Copy this URL — you need it in every file.**

---

## Step 3 — Set Database Rules (Development)

In the Firebase Console → Realtime Database → **Rules** tab,
paste this and click **Publish**:

```json
{
  "rules": {
    ".read": true,
    ".write": true
  }
}
```

> ⚠️ This allows anyone to read/write. Fine for development/college project.
> For production use the rules in `firebase_rules.json`.

---

## Step 4 — Seed Sample Data (Python)

Edit `firebase_setup.py` — find this line and replace with your URL:

```python
FIREBASE_URL = "https://nirikshak-default-rtdb.firebaseio.com"
```

Then run:
```bash
pip install urllib3   # already included in Python standard lib
python firebase_setup.py
```

Expected output:
```
🔥 Connecting to: https://nirikshak-default-rtdb.firebaseio.com
📡 Writing sample data to /sensors/latest ... ✅ Done
📋 Writing sample data to /sensors/history ... ✅ Done (key: -Nxyz...)
⚙️  Writing fault limits to /sensors/config ... ✅ Done

🎉  Firebase setup complete!

Dashboard polling URL:
  https://nirikshak-default-rtdb.firebaseio.com/sensors/latest.json

Sample data written:
  timestamp     : 2025-06-12 14:30:00
  temperature   : 44.2
  current       : 5.1
  voltage       : 219.4
  vibration     : 0.83
  proximity     : 1420
  humidity      : 56.3
  probability   : 7.5
  status        : Normal
  fault         : 0
```

---

## Step 5 — Verify Data in Firebase Console

1. Firebase Console → Realtime Database → **Data** tab
2. You should see:
```
nirikshak-default-rtdb
└── sensors
    ├── latest
    │   ├── temperature: 44.2
    │   ├── current: 5.1
    │   ├── voltage: 219.4
    │   ├── vibration: 0.83
    │   ├── proximity: 1420
    │   ├── humidity: 56.3
    │   ├── probability: 7.5
    │   ├── status: "Normal"
    │   └── fault: 0
    ├── history
    │   └── -Nxyz...
    │       └── (same as latest)
    └── config
        ├── temperature: 65
        ├── current: 10
        ├── voltage: 230
        ├── vibration: 10
        └── proximity: 2000
```

---

## Step 6 — Connect Dashboard to Firebase

1. Open the dashboard in browser: **http://localhost:5000/dashboard**
2. In the **🔥 Firebase** panel, paste your project URL:
   ```
   https://nirikshak-default-rtdb.firebaseio.com
   ```
3. Click **🔥 Connect Firebase**
4. Dashboard header shows **🔥 Firebase** source badge
5. All 5 sensor cards + charts update immediately from cloud data

---

## Step 7A — Simulate Live Data (Python, no ESP32)

Edit `firebase_publisher.py`:
```python
FIREBASE_URL = "https://nirikshak-default-rtdb.firebaseio.com"
```

Run it:
```bash
python firebase_publisher.py
```

Output every 2 seconds:
```
[NORMAL ] Temp=43.2°C  Curr=5.8A  Volt=213.4V  Vib=0.92g  Prox=1380rpm  → Firebase ✅
[NORMAL ] Temp=47.1°C  Curr=4.9A  Volt=218.1V  Vib=1.12g  Prox=1450rpm  → Firebase ✅
[WARNING] Temp=58.4°C  Curr=8.3A  Volt=196.2V  Vib=8.40g  Prox=1720rpm  → Firebase ✅
[FAULT  ] Temp=74.8°C  Curr=12.1A Volt=241.0V  Vib=11.3g  Prox=2250rpm  → Firebase ✅
```

---

## Step 7B — Real ESP32 Publishing

### Required Libraries (Arduino IDE)
Install via **Sketch → Include Library → Manage Libraries**:
| Library | Author |
|---|---|
| Firebase ESP Client | Mobizt |
| ArduinoJson | Benoit Blanchon |
| DHT sensor library | Adafruit |
| Adafruit ADXL345 | Adafruit |

### Credentials to fill in `esp32_firebase.ino`

```cpp
#define WIFI_SSID          "YOUR_WIFI_NAME"
#define WIFI_PASSWORD      "YOUR_WIFI_PASSWORD"
#define FIREBASE_API_KEY   "AIzaSy..."           // Project Settings → Web API Key
#define FIREBASE_DB_URL    "https://nirikshak-default-rtdb.firebaseio.com"
#define FIREBASE_USER_EMAIL    "you@email.com"   // Firebase Auth user
#define FIREBASE_USER_PASSWORD "password"
```

> To create a Firebase Auth user:  
> Firebase Console → Build → Authentication → Sign-in method → Email/Password → Enable  
> Then: Users tab → Add user

### Board Settings (Arduino IDE)
- Board: **ESP32 Dev Module**
- Upload Speed: **921600**
- Port: your COM/tty port

### JSON sent to Firebase every 2 seconds
```json
{
  "timestamp":   "123456s uptime",
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
```

---

## Firebase DB Structure Summary

```
/sensors/latest          ← ESP32 overwrites this every 2s (dashboard polls this)
/sensors/history/{id}    ← ESP32 appends here (full log)
/sensors/config          ← Fault limits reference
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `firebase_setup.py` returns 401 | Set rules to test mode (Step 3) |
| Dashboard shows "Firebase Err" | Check URL has no trailing slash, rules are open |
| ESP32 won't connect Firebase | Verify API key and create Auth user (Step 7B) |
| Values show 0 on dashboard | Check JSON keys match exactly (lowercase) |
| CORS error in browser | Add `.json` to end of Firebase URL — RTDB supports browser fetch |

---

## Free Tier Limits (Firebase Spark Plan)

| Resource | Limit |
|---|---|
| Storage | 1 GB |
| Downloads | 10 GB / month |
| Simultaneous connections | 100 |
| **Cost** | **Free** |

At 1 reading every 2 seconds = 43,200 reads/day = well within free limits.

---

*Nirikshak — Predictive Maintenance · PCCOE 2025–26*