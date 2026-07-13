#!/usr/bin/env python3
# ============================================================
#  pipeline.py — Nirikshak IoT Predictive Maintenance Pipeline
#
#  Workflow:
#    CSV Ingestion → Preprocessing → 3-Stage ML Inference → Firebase Push
# ============================================================

import os
import sys
import argparse
import time
import json
import urllib.request
import pandas as pd
import numpy as np
from datetime import datetime

# Setup paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import config
from ml import model

def parse_args():
    parser = argparse.ArgumentParser(description="Nirikshak IoT Processing Pipeline")
    parser.add_argument(
        "--csv_path", 
        type=str, 
        default=os.path.join(BASE_DIR, "data", "nirikshak_historical_data.csv"),
        help="Path to static/historical CSV file"
    )
    parser.add_argument(
        "--mode", 
        type=str, 
        choices=["batch", "stream"], 
        default="batch",
        help="Run mode: 'batch' (process and push all) or 'stream' (process and push one-by-one)"
    )
    parser.add_argument(
        "--firebase_url", 
        type=str, 
        default=config.FIREBASE_URL if (hasattr(config, "FIREBASE_URL") and config.FIREBASE_URL) else "https://nirikshak-project-default-rtdb.firebaseio.com/",
        help="Firebase Realtime Database URL"
    )
    parser.add_argument(
        "--interval", 
        type=float, 
        default=2.0,
        help="Polling/Streaming interval in seconds (for stream mode)"
    )
    return parser.parse_args()

def push_to_firebase(firebase_url, record_id, raw_data, processed_data, ml_prediction, combined_data):
    """
    Pushes data split across the 3 Firebase collections/paths:
      1. /raw_sensor_data_storage
      2. /processed_data_storage
      3. /ml_prediction_storage
      
    Also updates a unified /sensors/latest and appends to /sensors/history for compatibility.
    """
    headers = {"Content-Type": "application/json"}
    
    # 1. Push to Raw Sensor Data Storage
    raw_url = f"{firebase_url.rstrip('/')}/raw_sensor_data_storage/{record_id}.json"
    req_raw = urllib.request.Request(
        raw_url, data=json.dumps(raw_data).encode(), method="PUT", headers=headers
    )
    
    # 2. Push to Processed Data Storage
    proc_url = f"{firebase_url.rstrip('/')}/processed_data_storage/{record_id}.json"
    req_proc = urllib.request.Request(
        proc_url, data=json.dumps(processed_data).encode(), method="PUT", headers=headers
    )
    
    # 3. Push to ML Prediction Storage
    pred_url = f"{firebase_url.rstrip('/')}/ml_prediction_storage/{record_id}.json"
    req_pred = urllib.request.Request(
        pred_url, data=json.dumps(ml_prediction).encode(), method="PUT", headers=headers
    )
    
    # 4. Update latest combined record (for dashboard live view)
    latest_url = f"{firebase_url.rstrip('/')}/sensors/latest.json"
    req_latest = urllib.request.Request(
        latest_url, data=json.dumps(combined_data).encode(), method="PUT", headers=headers
    )
    
    # 5. Append to history list (for dashboard log compatibility)
    history_url = f"{firebase_url.rstrip('/')}/sensors/history.json"
    req_history = urllib.request.Request(
        history_url, data=json.dumps(combined_data).encode(), method="POST", headers=headers
    )
    
    # Execute requests
    try:
        with urllib.request.urlopen(req_raw, timeout=5) as r:
            pass
        with urllib.request.urlopen(req_proc, timeout=5) as r:
            pass
        with urllib.request.urlopen(req_pred, timeout=5) as r:
            pass
        with urllib.request.urlopen(req_latest, timeout=5) as r:
            pass
        with urllib.request.urlopen(req_history, timeout=5) as r:
            pass
        return True
    except Exception as e:
        print(f"  [Firebase Error] Push failed: {e}")
        return False

def run_pipeline():
    args = parse_args()
    
    print("\n" + "=" * 60)
    print("  NIRIKSHAK - CSV TO FIREBASE 3-STAGE INGESTION PIPELINE")
    print("=" * 60)
    print(f"Mode:         {args.mode.upper()}")
    print(f"CSV Path:     {args.csv_path}")
    print(f"Firebase URL: {args.firebase_url}")
    
    # Ensure models are loaded
    print("[Pipeline] Initializing ML models...")
    model.load_models()
    
    # Check CSV existence
    if not os.path.exists(args.csv_path):
        print(f"[ERROR] CSV file not found at {args.csv_path}.")
        print("Please run 'python ml/train.py' first to generate historical training data.")
        sys.exit(1)
        
    # Initialize local CSV
    try:
        from mqtt_subscriber import init_csv
        csv_path = os.path.join(BASE_DIR, config.DATA_CSV)
        if os.path.exists(csv_path):
            os.remove(csv_path)
        init_csv()
        print("[Pipeline] Reset local CSV backup database.")
    except Exception as e:
        print(f"[Pipeline] Warning initializing local CSV: {e}")

    # Read CSV
    print(f"[Pipeline] Ingesting static/historical CSV...")
    df = pd.read_csv(args.csv_path)
    print(f"Loaded {len(df)} rows.")
    
    # Sort and prepare
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    # Run Preprocessing steps on DataFrame to calculate correct operating_hours
    print("[Pipeline] Running preprocessing pipeline...")
    # Calculate operating hours from timestamp deltas
    time_deltas = df['timestamp'].diff().dt.total_seconds() / 3600.0
    time_deltas = time_deltas.fillna(0.0)
    
    # Cap giant gaps
    cycle_resets = (time_deltas > 2.0).astype(int)
    operating_hours_list = []
    current_acc = 0.0
    for delta, is_reset in zip(time_deltas, cycle_resets):
        if is_reset:
            current_acc = 0.0
        else:
            current_acc += delta
        operating_hours_list.append(current_acc)
    df['operating_hours'] = operating_hours_list
    
    # Execute batch processing or stream processing
    if args.mode == "batch":
        print("\n[Pipeline] Processing in BATCH mode. Pushing all records...")
        success_count = 0
        total_rows = len(df)
        
        # Limit batch push to first 100 rows to avoid blowing up free-tier Firebase quotas, 
        # but let the user know they can configure it.
        limit_rows = min(total_rows, 200)
        print(f"Processing the first {limit_rows} rows of the historical CSV...")
        
        for idx in range(limit_rows):
            row = df.iloc[idx]
            
            # Format timestamp string
            ts_str = row['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
            
            # Extract raw reading dict
            reading = {
                "timestamp": ts_str,
                "temperature": float(row['temperature']),
                "vibration": float(row['vibration']),
                "current": float(row['current']),
                "voltage": float(row['voltage']),
                "rpm": float(row['rpm']),
                "operating_hours": float(row['operating_hours'])
            }
            
            # Run 3-stage inference
            res = model.predict(reading)
            
            # Split into the 3 Firebase storage collections
            record_id = f"rec_{row['timestamp'].strftime('%Y%m%d_%H%M%S')}_{idx:05d}"
            
            raw_data = {
                "timestamp": ts_str,
                "temperature": res["temperature"],
                "vibration": res["vibration"],
                "current": res["current"],
                "voltage": res["voltage"],
                "rpm": res["rpm"]
            }
            
            processed_data = {
                "timestamp": ts_str,
                "temperature_scaled": float(row['temperature']), # will be scaled in prediction if models are loaded
                "vibration_scaled": float(row['vibration']),
                "current_scaled": float(row['current']),
                "voltage_scaled": float(row['voltage']),
                "rpm_scaled": float(row['rpm']),
                "temperature_outlier": int(res["temperature_outlier"]),
                "vibration_outlier": int(res["vibration_outlier"]),
                "current_outlier": int(res["current_outlier"]),
                "voltage_outlier": int(res["voltage_outlier"]),
                "rpm_outlier": int(res["rpm_outlier"]),
                "operating_hours": res["operating_hours"]
            }
            
            ml_prediction = {
                "timestamp": ts_str,
                "anomaly_status": res["anomaly_status"],
                "anomaly_score": res["anomaly_score"],
                "fault_type": res["fault_type"],
                "confidence_score": res["confidence_score"],
                "predicted_rul": res["predicted_rul"],
                "recommended_action": res["recommended_action"]
            }
            
            # Push to Firebase
            ok = push_to_firebase(args.firebase_url, record_id, raw_data, processed_data, ml_prediction, res)
            if ok:
                success_count += 1
            
            # Local CSV push for Flask dashboard backup
            try:
                from mqtt_subscriber import append_csv
                res["proximity"] = res["rpm"]
                append_csv(res)
            except Exception as e:
                pass
                
            if (idx + 1) % 20 == 0 or idx + 1 == limit_rows:
                print(f"  Pushed {idx + 1}/{limit_rows} records...")
                
        print(f"\n[Batch Complete] Successfully pushed {success_count}/{limit_rows} records to Firebase.")
        print(f"Data split across paths:")
        print(f"  - {args.firebase_url.rstrip('/')}/raw_sensor_data_storage")
        print(f"  - {args.firebase_url.rstrip('/')}/processed_data_storage")
        print(f"  - {args.firebase_url.rstrip('/')}/ml_prediction_storage")
        
    else: # stream mode
        print(f"\n[Pipeline] Processing in STREAM mode. Pushing one record every {args.interval}s...")
        print("Press Ctrl+C to exit.")
        print(f"{'#':>4}  {'Timestamp':<19}  {'Temp':>5}  {'Vib':>6}  {'Curr':>5}  {'Volt':>5}  {'Status':<8}  {'Fault Type':<16}  {'RUL':>5}  Firebase")
        print("-" * 100)
        
        idx = 0
        try:
            while idx < len(df):
                row = df.iloc[idx]
                ts_str = row['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
                
                reading = {
                    "timestamp": ts_str,
                    "temperature": float(row['temperature']),
                    "vibration": float(row['vibration']),
                    "current": float(row['current']),
                    "voltage": float(row['voltage']),
                    "rpm": float(row['rpm']),
                    "operating_hours": float(row['operating_hours'])
                }
                
                # Run 3-stage inference
                res = model.predict(reading)
                
                # Record ID
                record_id = f"rec_{row['timestamp'].strftime('%Y%m%d_%H%M%S')}_{idx:05d}"
                
                raw_data = {
                    "timestamp": ts_str,
                    "temperature": res["temperature"],
                    "vibration": res["vibration"],
                    "current": res["current"],
                    "voltage": res["voltage"],
                    "rpm": res["rpm"]
                }
                
                processed_data = {
                    "timestamp": ts_str,
                    "temperature_scaled": float(row['temperature']),
                    "vibration_scaled": float(row['vibration']),
                    "current_scaled": float(row['current']),
                    "voltage_scaled": float(row['voltage']),
                    "rpm_scaled": float(row['rpm']),
                    "temperature_outlier": int(res["temperature_outlier"]),
                    "vibration_outlier": int(res["vibration_outlier"]),
                    "current_outlier": int(res["current_outlier"]),
                    "voltage_outlier": int(res["voltage_outlier"]),
                    "rpm_outlier": int(res["rpm_outlier"]),
                    "operating_hours": res["operating_hours"]
                }
                
                ml_prediction = {
                    "timestamp": ts_str,
                    "anomaly_status": res["anomaly_status"],
                    "anomaly_score": res["anomaly_score"],
                    "fault_type": res["fault_type"],
                    "confidence_score": res["confidence_score"],
                    "predicted_rul": res["predicted_rul"],
                    "recommended_action": res["recommended_action"]
                }
                
                ok = push_to_firebase(args.firebase_url, record_id, raw_data, processed_data, ml_prediction, res)
                status_sym = "[OK]" if ok else "[ERR]"
                
                # Local CSV push for Flask dashboard backup
                try:
                    from mqtt_subscriber import append_csv
                    res["proximity"] = res["rpm"]
                    append_csv(res)
                except Exception as e:
                    pass
                
                print(
                    f"{idx+1:>4}  {ts_str}  "
                    f"{res['temperature']:>5.1f}  "
                    f"{res['vibration']:>6.3f}  "
                    f"{res['current']:>5.1f}  "
                    f"{res['voltage']:>5.0f}  "
                    f"{res['anomaly_status']:<8}  "
                    f"{res['fault_type']:<16}  "
                    f"{res['predicted_rul']:>5.1f}  "
                    f"{status_sym}",
                    flush=True
                )
                
                idx += 1
                time.sleep(args.interval)
                
        except KeyboardInterrupt:
            print("\n[Stream Stopped] Exited streaming pipeline.")

if __name__ == "__main__":
    run_pipeline()
