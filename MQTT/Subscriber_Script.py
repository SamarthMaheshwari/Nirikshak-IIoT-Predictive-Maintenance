
import paho.mqtt.client as mqtt
import firebase_admin
from firebase_admin import credentials, db
import json
import csv
import os
from datetime import datetime

# ================= Firebase Setup =================

cred = credentials.Certificate("serviceAccountKey.json")

firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://dht11-4ed11-default-rtdb.asia-southeast1.firebasedatabase.app/'
})

firebase_ref = db.reference('sensor')

# ================= CSV Setup =================

csv_file = "pdm_sensor_data.csv"

if not os.path.exists(csv_file):
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            "Timestamp",
            "Temperature",
            "Current",
            "Voltage",
            "RPM",
            "Vibration"
        ])

# ================= MQTT Callback =================

def on_message(client, userdata, msg):
    try:
        print("\n📩 MQTT Message Received")

        data = json.loads(msg.payload.decode())

        temperature = data.get("temperature")
        current = data.get("current")
        voltage = data.get("voltage")
        rpm = data.get("rpm")
        vibration = data.get("vibration")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"🌡 Temperature : {temperature} °C")
        print(f"⚡ Current     : {current} A")
        print(f"🔌 Voltage     : {voltage} V")
        print(f"🔄 RPM         : {rpm}")
        print(f"📳 Vibration   : {vibration}")

        # ================= Firebase Latest =================

        firebase_ref.child("latest").set({
            "temperature": temperature,
            "current": current,
            "voltage": voltage,
            "rpm": rpm,
            "vibration": vibration,
            "timestamp": timestamp
        })

        # ================= Firebase History =================

        firebase_ref.child("history").push({
            "temperature": temperature,
            "current": current,
            "voltage": voltage,
            "rpm": rpm,
            "vibration": vibration,
            "timestamp": timestamp
        })

        # ================= CSV Logging =================

        with open(csv_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                timestamp,
                temperature,
                current,
                voltage,
                rpm,
                vibration
            ])

        print("✅ Saved to Firebase and CSV")

    except Exception as e:
        print("❌ Error:", e)

# ================= MQTT Setup =================

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT Broker")
        client.subscribe("sensor/data")
        print("🚀 Listening on topic: sensor/data")
    else:
        print("❌ MQTT Connection Failed. Code:", rc)

client = mqtt.Client()

client.on_connect = on_connect
client.on_message = on_message

print("🔗 Connecting to MQTT Broker...")

client.connect("localhost", 1883, 60)

client.loop_forever()

