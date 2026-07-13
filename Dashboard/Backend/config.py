# ============================================================
#  config.py — Nirikshak Project Configuration
# ============================================================

# --- HiveMQ Cloud (Free Tier) ---
MQTT_BROKER    = "27ba182fd536475e8a5d3195430f436b.s1.eu.hivemq.cloud"
MQTT_PORT      = 8883
MQTT_USERNAME  = "Shriraj2004"
MQTT_PASSWORD  = "Shriraj2004"
MQTT_TOPIC     = "nirikshak/machine1"
MQTT_CLIENT_ID = "nirikshak_subscriber"

# --- Data ---
DATA_CSV      = "data/machine_data.csv"
TRAINING_CSV  = "data/training_data.csv"
MODEL_PATH    = "ml/rf_model.pkl"

# --- Flask ---
FLASK_HOST    = "0.0.0.0"
FLASK_PORT    = 5000
FLASK_DEBUG   = False

# --- ML Thresholds (all 5 sensors) ---
TEMP_MAX      = 85.0    # °C
CURRENT_MAX   = 10.0    # A
VOLTAGE_NOMINAL = 230.0 # V (anomaly if volt > 230 or < 230)
VIBRATION_MAX = 4.0     # g
PROXIMITY_MAX = 1450    # rpm

# --- Firebase Realtime Database URL ---
FIREBASE_URL  = "https://nirikshak-project-default-rtdb.firebaseio.com/"