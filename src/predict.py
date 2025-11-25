# src/predict.py
"""
Load models and predict on DataFrame or CSV.
Provides fallback if models missing (graceful).
"""
import os
import joblib
import pandas as pd
from features import build_features
from config import MODELS_DIR

def _model_path(name):
    return os.path.join(MODELS_DIR, name)

def load_models():
    rf_path = _model_path("rf_model.joblib")
    iso_path = _model_path("iso_model.joblib")

    rf = iso = None
    if os.path.exists(rf_path):
        try:
            rf = joblib.load(rf_path)
        except Exception as e:
            print("Warning: failed loading RF:", e)
    else:
        print("Warning: RF model not found at", rf_path)

    if os.path.exists(iso_path):
        try:
            iso = joblib.load(iso_path)
        except Exception as e:
            print("Warning: failed loading ISO:", e)
    else:
        print("Warning: ISO model not found at", iso_path)

    return rf, iso

def predict_df(df: pd.DataFrame):
    rf, iso = load_models()
    X, feature_cols = build_features(df)
    out = df.copy()

    if rf is not None:
        try:
            out["RF_Prediction"] = rf.predict(X).astype(int)
        except Exception as e:
            print("RF predict error:", e)
            out["RF_Prediction"] = 0
    else:
        out["RF_Prediction"] = 0

    if iso is not None:
        try:
            iso_raw = iso.predict(X)  # -1 anomaly, 1 normal
            out["ISO_Prediction"] = (iso_raw == -1).astype(int)
        except Exception as e:
            print("ISO predict error:", e)
            out["ISO_Prediction"] = 0
    else:
        out["ISO_Prediction"] = 0

    # final ensemble: mark anomaly if any model flagged it
    out["Anomaly"] = ((out["RF_Prediction"] + out["ISO_Prediction"]) >= 1).astype(int)
    return out

def predict_file(path: str):
    df = pd.read_csv(path)
    return predict_df(df)

if __name__ == "__main__":
    print("Test predict on csic csv ")
    test_path = os.path.join(os.path.dirname(__file__), "..", "data", "csic_database.csv")
    if os.path.exists(test_path):
        df = predict_file(test_path)
        print(df.head())
    else:
        print("No test CSV found at", test_path)
