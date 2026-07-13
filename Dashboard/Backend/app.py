import json, csv, os, threading, time, sys

# Fix path so mqtt_subscriber can be found
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
import mqtt_subscriber
from config import FLASK_HOST, FLASK_PORT, DATA_CSV, FIREBASE_URL

app = Flask(__name__)
app.config["SECRET_KEY"] = "nirikshak_secret_2025"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

def get_history_data():
    if FIREBASE_URL:
        try:
            import urllib.request, json
            url = f"{FIREBASE_URL.rstrip('/')}/sensors/history.json"
            req = urllib.request.Request(url, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=5) as r:
                data = json.loads(r.read().decode())
                if data:
                    if isinstance(data, dict):
                        rows = [v for v in data.values() if v]
                        rows.sort(key=lambda x: x.get("timestamp", ""))
                        return rows
                    elif isinstance(data, list):
                        return [v for v in data if v]
        except Exception as e:
            print(f"[Firebase History Fetch Error] {e}", flush=True)
            
    # Fallback to local CSV
    rows = []
    base_dir = os.path.dirname(os.path.abspath(__file__))
    abs_csv = os.path.join(base_dir, DATA_CSV)
    if os.path.exists(abs_csv):
        try:
            with open(abs_csv, newline="") as f:
                rows = list(csv.DictReader(f))
        except Exception:
            pass
    return rows

# ── Routes ─────────────────────────────────────────────────
@app.route("/home")
def home():
    return render_template("index.html")

# Also make home the default
@app.route("/")
def root():
    return render_template("index.html")

@app.route("/dashboard")
def index():
    return render_template("dashboard.html")

@app.route("/api/latest")
def api_latest():
    if FIREBASE_URL:
        try:
            import urllib.request, json
            url = f"{FIREBASE_URL.rstrip('/')}/sensors/latest.json"
            req = urllib.request.Request(url, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=3) as r:
                res = json.loads(r.read().decode())
                if res and isinstance(res, dict):
                    try:
                        from ml.model import predict
                        prediction = predict(res)
                        return jsonify(prediction)
                    except Exception:
                        return jsonify(res)
        except Exception as e:
            pass
    return jsonify(mqtt_subscriber.latest_data)

@app.route("/api/history")
def api_history():
    rows = get_history_data()
    return jsonify(rows[-50:])

@app.route("/api/stats")
def api_stats():
    rows = get_history_data()
    if not rows:
        return jsonify({})
    temps  = [float(r["temperature"]) for r in rows if r.get("temperature")]
    vibs   = [float(r["vibration"])   for r in rows if r.get("vibration")]
    currs  = [float(r["current"])     for r in rows if r.get("current")]
    faults = [int(r["fault"])         for r in rows if r.get("fault") not in ("", None)]
    return jsonify({
        "total_readings": len(rows),
        "total_faults":   sum(faults),
        "uptime_pct":     round((1 - sum(faults) / max(len(faults), 1)) * 100, 1),
        "avg_temp":       round(sum(temps) / len(temps), 1) if temps else 0,
        "avg_vibration":  round(sum(vibs)  / len(vibs),  3) if vibs  else 0,
        "avg_current":    round(sum(currs) / len(currs), 1) if currs else 0,
    })

# ── Real-time push loop ────────────────────────────────────
def push_loop():
    import urllib.request, json, time, random, math
    from datetime import datetime
    from ml.model import predict
    
    cycle = 0
    while True:
        time.sleep(2)
        
        # 1. Try to fetch from Firebase
        if FIREBASE_URL:
            try:
                url = f"{FIREBASE_URL.rstrip('/')}/sensors/latest.json"
                req = urllib.request.Request(url, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=3) as r:
                    res = json.loads(r.read().decode())
                    if res and isinstance(res, dict):
                        try:
                            mqtt_subscriber.latest_data = predict(res)
                            mqtt_subscriber.last_update_time = time.time()
                        except Exception:
                            mqtt_subscriber.latest_data = res
                            mqtt_subscriber.last_update_time = time.time()
            except Exception as e:
                pass
        
        # 2. Watchdog: check if no live updates for > 5 seconds
        now = time.time()
        last_up = getattr(mqtt_subscriber, "last_update_time", 0.0)
        
        if now - last_up > 5.0:
            # Generate simulated reading
            temp = round(random.uniform(40.0, 50.0) + (math.sin(cycle * 0.1) * 5.0), 2)
            curr = round(random.uniform(4.5, 6.5) + (math.cos(cycle * 0.15) * 1.0), 2)
            volt = round(random.uniform(215.0, 225.0) + random.uniform(-2, 2), 1)
            vib  = round(random.uniform(0.8, 1.8) + (math.sin(cycle * 0.05) * 0.4), 3)
            rpm  = int(random.uniform(1150, 1350) + (math.sin(cycle * 0.2) * 50))
            
            sim_reading = {
                "temperature": temp,
                "current": curr,
                "voltage": volt,
                "vibration": vib,
                "rpm": rpm,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            try:
                prediction = predict(sim_reading)
                prediction["source"] = "local-simulator-fallback"
                mqtt_subscriber.latest_data = prediction
                print(f"[Watchdog] Offline/idle. Pushed simulated telemetry: Temp={temp}C, Vib={vib}g, Status={prediction.get('status')}", flush=True)
            except Exception as e:
                print(f"[Local Simulator Fallback Error] {e}", flush=True)
            
            cycle += 1
            
        data = mqtt_subscriber.latest_data
        if data:
            socketio.emit("sensor_update", data)

# ── Start ──────────────────────────────────────────────────
if __name__ == "__main__":
    # Start MQTT subscriber in background thread
    socketio.start_background_task(target=mqtt_subscriber.start)

    # Start real-time push loop
    socketio.start_background_task(target=push_loop)

    print(f"\nNirikshak Dashboard -> http://localhost:{FLASK_PORT}\n")
    socketio.run(app, host=FLASK_HOST, port=FLASK_PORT, debug=False, allow_unsafe_werkzeug=True)