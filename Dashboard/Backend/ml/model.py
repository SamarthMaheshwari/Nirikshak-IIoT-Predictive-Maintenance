#!/usr/bin/env python3
# ============================================================
#  ml/model.py — 3-stage Predictive Maintenance Inference Pipeline
#
#  Stages:
#    1. Isolation Forest       → Anomaly Detection
#    2. Random Forest Classifier→ Fault Classification
#    3. Random Forest Regressor → RUL Prediction
# ============================================================

import os
import sys
import time
import numpy as np
import pandas as pd
import joblib
from datetime import datetime
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

# ── Paths ──────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ML_DIR = os.path.join(BASE_DIR, "ml")

SCALER_PATH = os.path.join(ML_DIR, "scaler.pkl")
MEDIANS_PATH = os.path.join(ML_DIR, "medians.pkl")
OUTLIER_BOUNDS_PATH = os.path.join(ML_DIR, "outlier_bounds.pkl")
IF_PATH = os.path.join(ML_DIR, "isolation_forest.pkl")
RFC_PATH = os.path.join(ML_DIR, "fault_classifier.pkl")
RFR_PATH = os.path.join(ML_DIR, "rul_regressor.pkl")

# ── Global Model Store (Lazy Loaded) ──────────────────────
_scaler = None
_medians = None
_outlier_bounds = None
_isolation_forest = None
_fault_classifier = None
_rul_regressor = None

# ── State variables for real-time operating hours tracking ─
_last_timestamp = None
_cumulative_operating_hours = 0.0

def load_models():
    """Loads all model artifacts and preprocessors from the ml directory."""
    global _scaler, _medians, _outlier_bounds, _isolation_forest, _fault_classifier, _rul_regressor
    errors = []
    
    # Preprocessor scaler
    try:
        if os.path.exists(SCALER_PATH):
            _scaler = joblib.load(SCALER_PATH)
        else:
            errors.append("scaler.pkl not found")
    except Exception as e:
        errors.append(f"scaler.pkl load failed: {e}")
        
    # Preprocessor medians
    try:
        if os.path.exists(MEDIANS_PATH):
            _medians = joblib.load(MEDIANS_PATH)
        else:
            errors.append("medians.pkl not found")
    except Exception as e:
        errors.append(f"medians.pkl load failed: {e}")
        
    # Preprocessor outlier bounds
    try:
        if os.path.exists(OUTLIER_BOUNDS_PATH):
            _outlier_bounds = joblib.load(OUTLIER_BOUNDS_PATH)
        else:
            errors.append("outlier_bounds.pkl not found")
    except Exception as e:
        errors.append(f"outlier_bounds.pkl load failed: {e}")
        
    # Isolation Forest
    try:
        if os.path.exists(IF_PATH):
            _isolation_forest = joblib.load(IF_PATH)
        else:
            errors.append("isolation_forest.pkl not found")
    except Exception as e:
        errors.append(f"isolation_forest.pkl load failed: {e}")
        
    # Random Forest Classifier
    try:
        if os.path.exists(RFC_PATH):
            _fault_classifier = joblib.load(RFC_PATH)
        else:
            errors.append("fault_classifier.pkl not found")
    except Exception as e:
        errors.append(f"fault_classifier.pkl load failed: {e}")
        
    # Random Forest Regressor
    try:
        if os.path.exists(RFR_PATH):
            _rul_regressor = joblib.load(RFR_PATH)
        else:
            errors.append("rul_regressor.pkl not found")
    except Exception as e:
        errors.append(f"rul_regressor.pkl load failed: {e}")
        
    if errors:
        print("[ML Model Loader] Warnings/Errors encountered during startup:")
        for err in errors:
            print(f"  - {err}")
        return False
        
    print("[ML Model Loader] All Nirikshak pipeline artifacts loaded successfully!")
    return True

def load_model():
    """Legacy shim — used by other modules to trigger loading."""
    return load_models()

def _extract_and_clean_sensors(reading: dict) -> dict:
    """
    Extracts sensor readings from a dict, handling common keys, missing values, 
    and outlier flagging.
    """
    cleaned = {}
    
    # Get values with fallbacks/aliases
    t_val = reading.get("temperature", reading.get("temp", reading.get("Temperature(C)", reading.get("Temperature"))))
    v_val = reading.get("vibration", reading.get("vib", reading.get("Vibration(mm/s)", reading.get("Vibration"))))
    c_val = reading.get("current", reading.get("curr", reading.get("Current(A)", reading.get("Current"))))
    vo_val = reading.get("voltage", reading.get("volt", reading.get("Voltage(V)", reading.get("Voltage"))))
    r_val = reading.get("rpm", reading.get("speed", reading.get("Speed(RPM)", reading.get("proximity", reading.get("proximity_sensor")))))
    
    # Impute missing values using medians (if loaded) or default values
    defaults = {"temperature": 42.0, "vibration": 0.8, "current": 5.0, "voltage": 220.0, "rpm": 1450.0}
    
    for sensor, val in [("temperature", t_val), ("vibration", v_val), ("current", c_val), ("voltage", vo_val), ("rpm", r_val)]:
        if val is None or pd.isna(val):
            # Impute using median
            imputed_val = _medians.get(sensor, defaults[sensor]) if _medians else defaults[sensor]
            cleaned[sensor] = float(imputed_val)
        else:
            cleaned[sensor] = float(val)
            
    # Outlier Flagging (Flag, don't drop) based on absolute user threshold specifications
    cleaned["temperature_outlier"] = 1 if cleaned["temperature"] > 85.0 else 0
    cleaned["vibration_outlier"] = 1 if cleaned["vibration"] > 4.0 else 0
    cleaned["current_outlier"] = 1 if cleaned["current"] > 10.0 else 0
    cleaned["voltage_outlier"] = 1 if abs(cleaned["voltage"] - 230.0) > 0.5 else 0
    cleaned["rpm_outlier"] = 1 if cleaned["rpm"] > 1450.0 else 0
            
    return cleaned

def _rule_based_fallback(sensors: dict, operating_hours: float) -> dict:
    """Fallback logic used when model pickles are missing."""
    temp = sensors["temperature"]
    vib = sensors["vibration"]
    curr = sensors["current"]
    volt = sensors["voltage"]
    rpm = sensors["rpm"]
    
    # Basic logic
    is_anomaly = False
    anomaly_status = "Normal"
    anomaly_score = 0.12
    fault_type = "Healthy"
    confidence = 98.0
    
    if temp > 85.0 or abs(volt - 230.0) > 0.5 or vib > 4.0 or curr > 10.0 or rpm > 1450.0:
        is_anomaly = True
        anomaly_status = "Anomaly"
        anomaly_score = 0.82
        
    if temp > 75.0:
        fault_type = "Overheating"
        confidence = 90.0
    elif vib > 4.5:
        fault_type = "Bearing Fault"
        confidence = 92.0
    elif curr > 12.0:
        fault_type = "Electrical Fault"
        confidence = 88.0
    elif rpm < 1100.0:
        fault_type = "Rotor Fault"
        confidence = 85.0
    elif vib > 2.5:
        fault_type = "Unbalance"
        confidence = 80.0
    elif is_anomaly:
        fault_type = "Misalignment"
        confidence = 75.0
        
    # Simple RUL estimation
    # High vibration and high temperature lead to lower RUL
    predicted_rul = 500.0 - (operating_hours * 0.5)
    if fault_type != "Healthy":
        predicted_rul = min(predicted_rul, 120.0 - (vib * 10.0) - (temp - 40.0))
    predicted_rul = max(0.0, predicted_rul)
    
    return {
        "anomaly_status": anomaly_status,
        "anomaly_score": anomaly_score,
        "fault_type": fault_type,
        "confidence_score": confidence,
        "predicted_rul": round(predicted_rul, 1)
    }

def predict(reading: dict, model=None) -> dict:
    """
    Main entry point for Nirikshak 3-stage ML sequential inference.
    Takes raw dictionary of values and returns complete preprocessed and inferred dict.
    """
    start_time = time.time()
    global _last_timestamp, _cumulative_operating_hours
    
    # 1. Clean and process sensor readings (imputation, outlier flags)
    sensors = _extract_and_clean_sensors(reading)
    
    # 2. Track / Compute operating hours from timestamp deltas
    timestamp_str = reading.get("timestamp")
    current_time = None
    
    if timestamp_str:
        try:
            current_time = datetime.strptime(str(timestamp_str), "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                current_time = datetime.strptime(str(timestamp_str), "%H:%M:%S")
                # Add dummy date if only time is provided
                today = datetime.today()
                current_time = datetime(today.year, today.month, today.day, current_time.hour, current_time.minute, current_time.second)
            except Exception:
                current_time = datetime.now()
    else:
        current_time = datetime.now()
        
    # Check if operating_hours was passed in explicitly (e.g. batch run)
    if "operating_hours" in reading:
        operating_hours = float(reading["operating_hours"])
        _cumulative_operating_hours = operating_hours
    else:
        # Compute delta from last reading
        if _last_timestamp is not None:
            delta_hours = (current_time - _last_timestamp).total_seconds() / 3600.0
            # Cap deltas to avoid weird jumps (e.g. server downtime)
            if 0.0 < delta_hours < 2.0:
                _cumulative_operating_hours += delta_hours
            elif delta_hours >= 2.0:
                # server was likely down, simulate small 10 min step
                _cumulative_operating_hours += 0.1667
        _last_timestamp = current_time
        operating_hours = _cumulative_operating_hours
 
    # 3. Model Inference (or Rule-Based Fallback)
    if _scaler is None or _isolation_forest is None or _fault_classifier is None or _rul_regressor is None:
        # Attempt reloading
        loaded = load_models()
        if not loaded:
            # Fallback
            predictions = _rule_based_fallback(sensors, operating_hours)
            # Create a combined result dictionary
            result = {
                "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "temperature": sensors["temperature"],
                "vibration": sensors["vibration"],
                "current": sensors["current"],
                "voltage": sensors["voltage"],
                "rpm": int(sensors["rpm"]),
                "temperature_outlier": sensors["temperature_outlier"],
                "vibration_outlier": sensors["vibration_outlier"],
                "current_outlier": sensors["current_outlier"],
                "voltage_outlier": sensors["voltage_outlier"],
                "rpm_outlier": sensors["rpm_outlier"],
                "operating_hours": round(operating_hours, 3),
                "anomaly_status": predictions["anomaly_status"],
                "anomaly_score": predictions["anomaly_score"],
                "fault_type": predictions["fault_type"],
                "confidence_score": predictions["confidence_score"],
                "predicted_rul": predictions["predicted_rul"],
                "model_source": "rule-based-fallback"
            }
            # Add recommended action
            result["recommended_action"] = _get_recommended_action(result["anomaly_status"], result["fault_type"], result["predicted_rul"])
            
            # Backwards compatibility flags for legacy dashboard scripts
            result["fault"] = 1 if result["fault_type"] != "Healthy" else 0
            result["probability"] = result["confidence_score"]
            result["status"] = "Fault" if result["anomaly_status"] == "Anomaly" else "Normal"
            result["rul_trend"] = [result["predicted_rul"]]
            result["inference_latency"] = round((time.time() - start_time) * 1000.0, 2)
            result["ml_completed_timestamp"] = time.time() * 1000.0
            return result
 
    # 4. Standard 3-stage sequential ML inference
    # A. Scale features
    raw_feats = np.array([[
        sensors["temperature"],
        sensors["vibration"],
        sensors["current"],
        sensors["voltage"],
        sensors["rpm"]
    ]])
    scaled_feats = _scaler.transform(raw_feats)
    
    # B. Stage 1: Isolation Forest (Anomaly status & score)
    if_pred = _isolation_forest.predict(scaled_feats)[0]
    anomaly_status = "Anomaly" if if_pred == -1 else "Normal"
    # Convert score_samples (range [-1, 0]) to an anomaly score where higher is more anomalous
    anomaly_score = float(-_isolation_forest.score_samples(scaled_feats)[0])
    
    # C. Stage 2: Random Forest Classifier (Fault type & confidence)
    fault_type = _fault_classifier.predict(scaled_feats)[0]
    probs = _fault_classifier.predict_proba(scaled_feats)[0]
    classes = _fault_classifier.classes_
    class_idx = np.where(classes == fault_type)[0][0]
    confidence_score = float(probs[class_idx]) * 100.0
    
    # D. Stage 3: Random Forest Regressor (RUL prediction)
    # Inputs: 5 scaled sensors + operating_hours
    reg_input = np.column_stack((scaled_feats, [[operating_hours]]))
    predicted_rul = float(_rul_regressor.predict(reg_input)[0])
    predicted_rul = max(0.0, round(predicted_rul, 1))
    
    # Construct combined response
    result = {
        "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
        "temperature": sensors["temperature"],
        "vibration": sensors["vibration"],
        "current": sensors["current"],
        "voltage": sensors["voltage"],
        "rpm": int(sensors["rpm"]),
        "temperature_outlier": sensors["temperature_outlier"],
        "vibration_outlier": sensors["vibration_outlier"],
        "current_outlier": sensors["current_outlier"],
        "voltage_outlier": sensors["voltage_outlier"],
        "rpm_outlier": sensors["rpm_outlier"],
        "operating_hours": round(operating_hours, 3),
        "anomaly_status": anomaly_status,
        "anomaly_score": round(anomaly_score, 4),
        "fault_type": fault_type,
        "confidence_score": round(confidence_score, 1),
        "predicted_rul": predicted_rul,
        "model_source": "3-stage-ml-pipeline"
    }
    
    # Add recommended action
    result["recommended_action"] = _get_recommended_action(anomaly_status, fault_type, predicted_rul)
    
    # Backwards compatibility flags for legacy dashboard scripts
    result["fault"] = 1 if fault_type != "Healthy" else 0
    result["probability"] = confidence_score
    result["status"] = "Fault" if anomaly_status == "Anomaly" else "Normal"
    result["rul_trend"] = [predicted_rul]
    result["inference_latency"] = round((time.time() - start_time) * 1000.0, 2)
    result["ml_completed_timestamp"] = time.time() * 1000.0
    
    return result

def _get_recommended_action(anomaly_status: str, fault_type: str, rul: float) -> str:
    """Generates a contextual recommended action based on the ML predictions."""
    if anomaly_status == "Normal" and fault_type == "Healthy":
        return "Continue normal operations. Next check in 250 operating hours."
        
    if rul < 24.0:
        return f"CRITICAL ALERT: Machine failure imminent (RUL: {rul} hrs). Shut down and inspect immediately!"
        
    action_map = {
        "Bearing Fault": f"Inspect bearing housing for wear or lack of lubrication. Schedule check within 24 hrs.",
        "Misalignment": f"Re-align shaft coupling. Schedule check within 48 hrs.",
        "Unbalance": f"Perform rotor balancing. Inspect within 48 hrs.",
        "Overheating": f"Check cooling fans and motor ventilation immediately. Reduce operating load.",
        "Electrical Fault": f"Inspect stator winding, terminal voltage, and cables. Risk of short circuit!",
        "Rotor Fault": f"Inspect rotor bars. Check for current fluctuations and perform stator current analysis."
    }
    
    return action_map.get(fault_type, "Anomaly detected. Monitor closely and schedule full maintenance diagnostic.")

# Pre-load models at import time
load_models()