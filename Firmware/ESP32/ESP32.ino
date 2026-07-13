#include <WiFi.h>
#include <PubSubClient.h>

/* ================= WiFi Credentials ================= */
const char* ssid     = "ssid_name";
const char* password = "ssid_password";

/* ================= MQTT Config ================= */
const char* mqtt_server = "laptop/pc_id";
const int   mqtt_port   = 1883;
const char* mqtt_topic  = "sensor/data";

WiFiClient espClient;
PubSubClient client(espClient);

/* ================= Sensor Data ================= */
String temperature = "";
String currentVal  = "";
String voltage     = "";
String rpm         = "";
String vibration   = "";

/* ================= MQTT Reconnect ================= */
void reconnectMQTT() {
  while (!client.connected()) {
    Serial.print("Connecting to MQTT...");

    if (client.connect("ESP32_PDM")) {
      Serial.println(" Connected!");
    } else {
      Serial.print(" Failed, rc=");
      Serial.println(client.state());
      delay(2000);
    }
  }
}

/* ================= Parse UART Data ================= */
void parseData(String data) {

  int t  = data.indexOf("TEMP:");
  int c  = data.indexOf("CUR:");
  int v  = data.indexOf("VOLT:");
  int r  = data.indexOf("RPM:");
  int vb = data.indexOf("VIB:");

  if (t  != -1) temperature = data.substring(t + 5, data.indexOf(",", t));
  if (c  != -1) currentVal  = data.substring(c + 4, data.indexOf(",", c));
  if (v  != -1) voltage     = data.substring(v + 5, data.indexOf(",", v));
  if (r  != -1) rpm         = data.substring(r + 4, data.indexOf(",", r));
  if (vb != -1) vibration   = data.substring(vb + 4);
}

/* ================= Setup ================= */
unsigned long lastPublish = 0;

void setup() {

  Serial.begin(115200);

  // STM32 UART
  Serial2.begin(115200, SERIAL_8N1, 16, 17);

  /* WiFi */
  WiFi.begin(ssid, password);

  Serial.print("Connecting WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi Connected");
  Serial.print("ESP32 IP: ");
  Serial.println(WiFi.localIP());

  /* MQTT */
  client.setServer(mqtt_server, mqtt_port);
}

/* ================= Loop ================= */
void loop() {

  if (!client.connected()) {
    reconnectMQTT();
  }

  client.loop();

  /* Receive STM32 Data */
  if (Serial2.available()) {

    String incoming = Serial2.readStringUntil('\n');
    incoming.trim();

    Serial.println("UART Received:");
    Serial.println(incoming);

    parseData(incoming);
  }

  /* Publish every second */
  if (millis() - lastPublish >= 1000) {

    lastPublish = millis();

    if (temperature != "--") {

      char payload[200];

      snprintf(payload, sizeof(payload),
               "{\"temperature\": %s, "
               "\"current\": %s, "
               "\"voltage\": %s, "
               "\"rpm\": %s, "
               "\"vibration\": %s}",
               temperature.c_str(),
               currentVal.c_str(),
               voltage.c_str(),
               rpm.c_str(),
               vibration.c_str());

      client.publish(mqtt_topic, payload);

      Serial.println("MQTT Published:");
      Serial.println(payload);
    }
  }
}
