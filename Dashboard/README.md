# Dashboard

The Dashboard provides a real-time web interface for monitoring sensor data collected by the **Nirikshak Industrial IoT Predictive Maintenance System**.

It receives live sensor data through the backend, processes incoming telemetry, and displays the current machine status, historical data, and system statistics in an interactive web interface.

---

# Folder Structure

```
Dashboard/
│
├── Backend/
│   ├── app.py
│   ├── mqtt_subscriber.py
│   ├── config.py
│   ├── firebase_setup.py
│   ├── firebase_publisher.py
│   ├── pipeline.py
│   ├── requirements.txt
│   ├── templates/
│   ├── static/
│   ├── utils/
│   ├── ml/
│   ├── Firebase/
│   ├── Simulation/
│   └── Documentation/
│
├── Images/
└── README.md
```

---

# Features

- Real-time sensor monitoring
- Live dashboard updates using Socket.IO
- Historical data visualization
- Machine health monitoring
- Automatic fallback to simulated sensor data when no live data is available
- Responsive web interface

---

# Prerequisites

- Python 3.10 or later
- Internet connection (if using Firebase)
- Git (optional)

---

# Installation

Open a terminal inside the **Backend** folder.

Install the required Python packages:

```bash
pip install -r requirements.txt
```

---

# Running the Dashboard

Navigate to the Backend folder:

```bash
cd Dashboard/Backend
```

Run the application:

```bash
python app.py
```

If everything starts correctly, you should see a message similar to:

```
Nirikshak Dashboard -> http://localhost:5000
```

Open the displayed URL in your web browser.

Example:

```
http://localhost:5000
```

---

# Data Source

The dashboard automatically retrieves sensor data using the configured backend services.

Depending on the project configuration, data may come from:

- Firebase Realtime Database
- MQTT Subscriber
- Local simulator (automatic fallback)

If no live sensor data is available, the application generates simulated telemetry so the dashboard remains functional for demonstration purposes.

---

# Firebase Configuration

If you want to use your own Firebase project:

1. Create a Firebase Realtime Database.
2. Update the Firebase configuration in:

```
Backend/config.py
```

3. Replace the database URL with your own Firebase URL.

The Firebase folder also contains:

- Firebase security rules
- Firebase setup documentation

---

# Dashboard Pages

| Route | Description |
|--------|-------------|
| `/` | Home page |
| `/home` | Home page |
| `/dashboard` | Real-time dashboard |
| `/api/latest` | Latest sensor data |
| `/api/history` | Historical data |
| `/api/stats` | System statistics |

---

# Notes

- `app.py` is the main entry point of the dashboard.
- The MQTT subscriber is started automatically in the background when the application launches.
- No additional terminal or manual execution of the subscriber is required.

---

# Screenshots

Add dashboard screenshots inside the `Images` folder and reference them here.

Example:

```
Images/
├── dashboard_home.png
├── dashboard_live.png
└── dashboard_statistics.png
```

---

# Troubleshooting

### Missing Python packages

Install all dependencies again:

```bash
pip install -r requirements.txt
```

---

### Dashboard does not open

Verify that:

- Python is installed correctly.
- All required packages are installed.
- The configured port is available.

---

### No live sensor data

The dashboard automatically switches to simulated sensor data when no live telemetry is detected, allowing the interface to remain operational for testing and demonstration.

---
