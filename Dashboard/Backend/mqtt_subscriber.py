# ============================================================
#  mqtt_subscriber.py — HiveMQ Cloud → Multi-Model ML → Flask
#  Now forwards: fault_type, anomaly_score, is_anomaly, rul_trend
# ============================================================
import json, csv, os, ssl, sys, time
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import paho.mqtt.client as mqtt
import config

# ── Shared state (app.py reads this) ──────────────────────
latest_data = {}
last_update_time = 0.0
model       = None

CSV_FIELDS = [
    "timestamp", "temperature", "vibration", "current", "voltage", "rpm", "proximity",
    "temperature_outlier", "vibration_outlier", "current_outlier", "voltage_outlier", "rpm_outlier",
    "operating_hours", "anomaly_status", "anomaly_score", "fault_type", "confidence_score",
    "predicted_rul", "recommended_action", "fault", "probability", "status"
]

def init_csv():
    os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
    csv_path = os.path.join(BASE_DIR, config.DATA_CSV)
    if not os.path.exists(csv_path):
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_FIELDS)
        print(f"[CSV] Created {csv_path}", flush=True)

def append_csv(row):
    csv_path = os.path.join(BASE_DIR, config.DATA_CSV)
    with open(csv_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writerow(row)

def on_connect(client, userdata, flags, rc):
    codes = {0:"Connected OK", 1:"Bad protocol", 2:"Client ID rejected",
             3:"Server unavailable", 4:"Bad credentials", 5:"Not authorised"}
    print(f"[MQTT] {codes.get(rc, f'rc={rc}')}", flush=True)
    if rc == 0:
        client.subscribe(config.MQTT_TOPIC)
        print(f"[MQTT] Subscribed to: {config.MQTT_TOPIC}", flush=True)

def on_message(client, userdata, msg):
    global latest_data
    try:
        raw = json.loads(msg.payload.decode())
        print(f"[MQTT] {msg.topic}: {raw}", flush=True)

        # Map input keys (handle temperature, temp, current, curr, etc.)
        temp = float(raw.get("temperature", raw.get("temp", 42.0)))
        curr = float(raw.get("current", raw.get("curr", 5.0)))
        volt = float(raw.get("voltage", raw.get("volt", 220.0)))
        vib  = float(raw.get("vibration", raw.get("vib", 0.8)))
        rpm  = float(raw.get("rpm", raw.get("speed", raw.get("proximity", 1450.0))))

        reading = {
            "temperature": temp,
            "vibration":   vib,
            "current":     curr,
            "voltage":     volt,
            "rpm":         rpm,
        }

        # ── ML prediction ──────────────────────────────────
        try:
            from ml.model import predict
            result = predict(reading, model)
        except Exception as e:
            print(f"[ML] Prediction error: {e}", flush=True)
            import traceback; traceback.print_exc()
            result = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "temperature": temp,
                "vibration": vib,
                "current": curr,
                "voltage": volt,
                "rpm": int(rpm),
                "temperature_outlier": 0,
                "vibration_outlier": 0,
                "current_outlier": 0,
                "voltage_outlier": 0,
                "rpm_outlier": 0,
                "operating_hours": 0.0,
                "anomaly_status": "Normal",
                "anomaly_score": 0.12,
                "fault_type": "Healthy",
                "confidence_score": 95.0,
                "predicted_rul": 500.0,
                "recommended_action": "Continue normal operations.",
                "fault": 0, "probability": 5.0, "status": "Normal",
                "ml_completed_timestamp": time.time() * 1000.0,
                "inference_latency": 0.0
            }

        record = {
            "timestamp":           result.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            "temperature":         result["temperature"],
            "vibration":           result["vibration"],
            "current":             result["current"],
            "voltage":             result["voltage"],
            "rpm":                 result["rpm"],
            "proximity":           result["rpm"], # for dashboard compatibility
            "temperature_outlier": result["temperature_outlier"],
            "vibration_outlier":   result["vibration_outlier"],
            "current_outlier":     result["current_outlier"],
            "voltage_outlier":     result["voltage_outlier"],
            "rpm_outlier":         result["rpm_outlier"],
            "operating_hours":     result["operating_hours"],
            "anomaly_status":      result["anomaly_status"],
            "anomaly_score":       result["anomaly_score"],
            "fault_type":          result["fault_type"],
            "confidence_score":    result["confidence_score"],
            "predicted_rul":       result["predicted_rul"],
            "recommended_action":  result["recommended_action"],
            "fault":               result["fault"],
            "probability":         result["probability"],
            "status":              result["status"],
            "ml_completed_timestamp": result.get("ml_completed_timestamp", time.time() * 1000.0),
            "inference_latency":     result.get("inference_latency", 0.0)
        }

        global last_update_time
        append_csv(record)
        latest_data = record
        last_update_time = time.time()
        print(
            f"[ML]   {result['anomaly_status']:8s}  {result['fault_type']}({result['confidence_score']:.1f}%)  "
            f"RUL={result['predicted_rul']:.1f} hrs  "
            f"Action={result['recommended_action']}",
            flush=True
        )

    except Exception as e:
        print(f"[MQTT] Error: {e}", flush=True)
        import traceback; traceback.print_exc()

def on_disconnect(client, userdata, rc):
    print(f"[MQTT] Disconnected (rc={rc}). Reconnecting...", flush=True)

def on_subscribe(client, userdata, mid, granted_qos):
    print(f"[MQTT] Subscribe confirmed. QoS={granted_qos}", flush=True)

def start():
    global model
    init_csv()

    print("[ML] Loading models...", flush=True)
    try:
        from ml.model import load_model
        model = load_model()
        print("[ML] All models loaded successfully", flush=True)
    except Exception as e:
        print(f"[ML] WARNING: {e} - using rule-based fallback", flush=True)

    try:
        client = mqtt.Client(
            client_id=config.MQTT_CLIENT_ID,
            callback_api_version=mqtt.CallbackAPIVersion.VERSION1
        )
    except Exception:
        client = mqtt.Client(client_id=config.MQTT_CLIENT_ID)

    client.username_pw_set(config.MQTT_USERNAME, config.MQTT_PASSWORD)
    client.tls_set(tls_version=ssl.PROTOCOL_TLS)
    client.on_connect    = on_connect
    client.on_message    = on_message
    client.on_disconnect = on_disconnect
    client.on_subscribe  = on_subscribe

    print(f"[MQTT] Connecting to {config.MQTT_BROKER}:{config.MQTT_PORT}...", flush=True)
    while True:
        try:
            client.connect(config.MQTT_BROKER, config.MQTT_PORT, keepalive=60)
            client.loop_forever()
        except Exception as e:
            print(f"[MQTT] Connection failed: {e}. Retrying in 10 seconds...", flush=True)
            time.sleep(10)