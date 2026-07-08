# Nirikshak

Industrial IoT Predictive Maintenance System

---

## Dashboard

![Dashboard](Images/Dashboard2.jpg)

---

# Project Overview

Nirikshak is an Industrial Internet of Things (IIoT) Predictive Maintenance System developed for monitoring industrial motors in real time.

The project continuously acquires sensor data from industrial equipment, processes the readings using STM32 firmware, transmits the data wirelessly through ESP32 using MQTT, stores the data on a local server, and visualizes machine health through a modern web dashboard.

The system is designed to help industries reduce downtime, improve maintenance planning, and detect abnormal operating conditions before failures occur.

---

# Features

- Real-Time Monitoring
- Predictive Maintenance Framework
- Industrial IoT Architecture
- MQTT Communication
- Live Dashboard
- Machine Health Monitoring
- Fault Detection
- Data Logging
- Wireless Communication
- Modular Design

---

# Hardware Components

| Component | Purpose |
|-----------|----------|
| STM32F103CBT6 | Data Acquisition Unit |
| ESP32 | WiFi Communication |
| INA260 | Current & Voltage Measurement |
| MPU6050 | Vibration Monitoring |
| Temperature Sensor | Temperature Monitoring |
| Industrial Motor | Test Equipment |

---

# Software Stack

## Programming Languages

- Embedded C
- C++
- Python
- HTML
- CSS
- JavaScript

## Tools

- STM32CubeIDE
- Arduino IDE
- VS Code
- MQTT
- Flask
- GitHub

---

# System Architecture

```
Sensors
     │
     ▼
 STM32 DAQ
     │
     ▼
 ESP32 MQTT Publisher
     │
     ▼
 MQTT Broker
     │
     ▼
 Python Subscriber
     │
     ▼
 Database / CSV
     │
     ▼
 Flask Dashboard
     │
     ▼
 User
```

---

# Sensor Parameters

## Temperature

Measures machine temperature continuously and compares it against predefined safety limits.

---

## Current

Monitors motor current consumption and overload conditions.

---

## Voltage

Measures input supply voltage for stability analysis.

---

## Vibration

Detects abnormal vibration patterns that may indicate bearing wear, imbalance, or mechanical faults.

---

# Workflow

### Step 1

Sensors collect machine data.

↓

### Step 2

STM32 reads all sensor values.

↓

### Step 3

ESP32 sends data through MQTT.

↓

### Step 4

MQTT Broker receives data.

↓

### Step 5

Python subscriber stores data.

↓

### Step 6

Dashboard updates in real time.

↓

### Step 7

Machine health is evaluated.

---

# Folder Structure

```
Firmware/
Dashboard/
Machine_Learning/
Hardware/
MQTT/
Dataset/
Documents/
Images/
```

---

# Applications

- Industrial Motor Monitoring
- Predictive Maintenance
- Condition Monitoring
- Factory Automation
- Smart Manufacturing
- Industrial IoT

---

# Future Improvements

- AI Based Fault Detection
- Remaining Useful Life Prediction
- Cloud Integration
- Mobile Application
- Email Alerts
- SMS Notifications
- Multi-Machine Dashboard
- Historical Data Analysis

---

# Getting Started

## Clone Repository

```
git clone https://github.com/username/Nirikshak-IIoT-Predictive-Maintenance.git
```

---

## Install Requirements

Python

MQTT Broker

STM32CubeIDE

Arduino IDE

---

## Run Dashboard

```
python app.py
```

---

## Connect STM32

Upload STM32 firmware.

---

## Connect ESP32

Upload ESP32 firmware.

---

## Start MQTT Broker

Start the MQTT broker.

---

## Open Dashboard

Open

```
http://localhost:5000
```

---

# Project Status

🚧 Under Development

---

# Author

**Sam**

Embedded Systems Engineer

Industrial IoT

Firmware Development
