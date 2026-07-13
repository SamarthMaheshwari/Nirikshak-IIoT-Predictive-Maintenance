# ============================================================
#  utils/data_cleaner.py — Preprocessing Pipeline
# ============================================================
import pandas as pd
import numpy as np

def clean_reading(data: dict) -> dict | None:
    """
    Clean and validate a single MQTT reading.
    Returns None if data is invalid/corrupted.
    """
    required = ["temperature", "vibration", "current"]

    # Check all required fields exist
    for field in required:
        if field not in data:
            print(f"[Cleaner] Missing field: {field}")
            return None

    try:
        temp      = float(data["temperature"])
        vibration = float(data["vibration"])
        current   = float(data["current"])
        humidity  = float(data.get("humidity", 0))
    except (ValueError, TypeError) as e:
        print(f"[Cleaner] Type error: {e}")
        return None

    # --- Range validation (physical limits) ---
    if not (-10 <= temp <= 150):
        print(f"[Cleaner] Temp out of range: {temp}")
        return None
    if not (0 <= vibration <= 20):
        print(f"[Cleaner] Vibration out of range: {vibration}")
        return None
    if not (0 <= current <= 30):
        print(f"[Cleaner] Current out of range: {current}")
        return None

    return {
        "temperature": round(temp, 2),
        "vibration":   round(vibration, 3),
        "current":     round(current, 2),
        "humidity":    round(humidity, 1),
    }


def load_and_clean_csv(filepath: str) -> pd.DataFrame:
    """Load CSV, drop nulls, remove outliers using IQR."""
    df = pd.read_csv(filepath, parse_dates=["timestamp"])
    df.dropna(inplace=True)

    numeric_cols = ["temperature", "vibration", "current", "humidity"]
    for col in numeric_cols:
        if col in df.columns:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            df = df[(df[col] >= Q1 - 1.5 * IQR) & (df[col] <= Q3 + 1.5 * IQR)]

    df.reset_index(drop=True, inplace=True)
    return df


def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Feature engineering for ML model.
    Adds rolling statistics for better fault detection.
    """
    df = df.copy()
    for col in ["temperature", "vibration", "current"]:
        if col in df.columns:
            df[f"{col}_mean5"] = df[col].rolling(5, min_periods=1).mean()
            df[f"{col}_std5"]  = df[col].rolling(5, min_periods=1).std().fillna(0)
    return df