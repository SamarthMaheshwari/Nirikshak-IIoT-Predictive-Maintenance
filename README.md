# Nirikshak: An Industrial IoT Predictive Maintenance System

<p align="center">
  <img src="Documentation/System.png" width="700">
</p>

## Overview

Nirikshak is a low-cost Industrial Internet of Things (IIoT) based Predictive Maintenance System designed for monitoring the health of industrial motors in real time.

The system continuously acquires data from multiple sensors using an STM32-based Data Acquisition (DAQ) device. The collected data is transmitted wirelessly through an ESP32 module using the MQTT protocol. A Python-based subscriber stores the incoming data, which is then visualized on a real-time dashboard for monitoring and analysis.

This project demonstrates hardware design, embedded firmware development, wireless communication, PCB design, and industrial data acquisition.

---

## Features

- Real-time industrial motor monitoring
- Wireless data transmission using MQTT
- Custom STM32-based DAQ board
- ESP32 Wi-Fi communication
- Multi-sensor data acquisition
- Real-time dashboard visualization
- Custom PCB designed in EasyEDA
- Custom 3D enclosure
- Modular firmware architecture
- Low-cost and scalable IIoT solution

---

# System Architecture

```
Industrial Motor
        │
        ▼
Sensors
│
├── MPU6050 (Vibration)
├── DS18B20 (Temperature)
├── ZMPT101B (Voltage)
├── SCT-013 (Current)
└── Proximity Sensor (RPM)
        │
        ▼
STM32 BlackPill
(Data Acquisition)
        │
UART
        │
        ▼
ESP32 DevKit V1
        │
Wi-Fi
        │
MQTT
        │
Python Subscriber
        │
CSV Storage
        │
Dashboard
```

---

# Hardware

## Microcontrollers

- STM32 BlackPill (STM32F411)
- ESP32 DevKit V1

## Sensors

- MPU6050
- DS18B20
- ZMPT101B
- SCT-013 Current Sensor
- Inductive Proximity Sensor

---

# Software Stack

| Software | Purpose |
|----------|---------|
| Arduino IDE | Firmware Development |
| EasyEDA | PCB Design |
| Python | Data Subscriber |
| MQTT | Communication Protocol |
| GitHub | Version Control |

---

# Repository Structure

```
Nirikshak
│
├── Firmware
│   ├── STM32
│   └── ESP32
│
├── MQTT
│   ├── Subscriber_Script
│   └── MQTT Architecture
│
├── PCB
│   ├── EasyEDA
│   ├── Layout
│   └── Schematic
│
├── Dashboard
│
├── Documentation
│
├── 3D_Enclosure
│
├── Images
│
├── README.md
└── LICENSE
```

---

# PCB

The DAQ board was designed in EasyEDA.

Features include

- STM32 BlackPill
- ESP32 Interface
- Sensor Connectors
- Power Distribution
- Compact 2-Layer PCB

---

# Dashboard

The dashboard displays

- Temperature
- Current
- Voltage
- RPM
- Vibration
- Live Sensor Data

---

# Communication

```
STM32
   │
UART
   │
ESP32
   │
Wi-Fi
   │
MQTT Broker
   │
Python Subscriber
   │
CSV Database
   │
Dashboard
```

---

# Future Improvements

- Edge AI for fault prediction
- Machine Learning integration
- Cloud deployment
- Mobile application
- OTA firmware updates
- Multi-machine monitoring

---

# Author

**Samarth Jadhav**

Electronics & Telecommunication Engineering

Specialization:
- Embedded Systems
- Industrial IoT
- Firmware Development
- PCB Design

GitHub:
[Samarth Maheshwari](https://github.com/SamarthMaheshwari)

LinkedIn:
[Samarth Maheshwari](www.linkedin.com/in/samarth-maheshwari-709670259)

---

# Acknowledgements

This project was developed as a Final Year Engineering Project focusing on Industrial IoT and Predictive Maintenance.

---

# License

This project is licensed under the MIT License.
See the LICENSE file for details.
