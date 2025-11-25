# src/train.py
"""
Train IsolationForest (priority) and a lightweight RandomForest.
Saves models into ../models and writes metadata.json
"""
import os
import json
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.metrics import classification_report
from config import CSIC_CSV, MODELS_DIR, MODEL_METADATA, ISO_CONTAMINATION, ISO_NESTIMATORS, RF_N_ESTIMATORS, RANDOM_STATE
from features import build_features

os.makedirs(MODELS_DIR, exist_ok=True)

def load_dataset():
    if not os.path.exists(CSIC_CSV):
        raise FileNotFoundError(f"Parsed dataset not found at {CSIC_CSV}. Run parse_logs.py first.")
    df = pd.read_csv(CSIC_CSV)
    if "label" not in df.columns:
        raise ValueError("Missing 'label' column in dataset. Run parse_logs.py.")
    df = df.dropna(subset=["label"])
    df["label"] = df["label"].astype(int)
    return df

def save_metadata(meta: dict):
    with open(MODEL_METADATA, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print("Model metadata saved to", MODEL_METADATA)

def main():
    print("=== Loading dataset ===")
    df = load_dataset()
    X, feature_cols = build_features(df)
    y = df["label"]

    print(f"Total samples: {len(df)}")
    print("Features:", feature_cols)

    # IsolationForest (priority)
    print("\n=== Training IsolationForest (priority model) ===")
    iso = IsolationForest(n_estimators=ISO_NESTIMATORS, contamination=ISO_CONTAMINATION, random_state=RANDOM_STATE)
    iso.fit(X)  # unsupervised on all data
    iso_path = os.path.join(MODELS_DIR, "iso_model.joblib")
    joblib.dump(iso, iso_path)
    print("Saved IsolationForest ->", iso_path)

    # RandomForest (lightweight)
    print("\n=== Training RandomForest (baseline) ===")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE
    )
    rf = RandomForestClassifier(n_estimators=RF_N_ESTIMATORS, random_state=RANDOM_STATE)
    rf.fit(X_train, y_train)
    rf_path = os.path.join(MODELS_DIR, "rf_model.joblib")
    joblib.dump(rf, rf_path)
    print("Saved RandomForest ->", rf_path)

    preds = rf.predict(X_test)
    print("\nRandomForest evaluation (simple baseline):")
    print(classification_report(y_test, preds))

    # metadata
    metadata = {
        "models": {
            "isolation_forest": {"path": iso_path, "contamination": ISO_CONTAMINATION, "n_estimators": ISO_NESTIMATORS},
            "random_forest": {"path": rf_path, "n_estimators": RF_N_ESTIMATORS}
        },
        "features": feature_cols,
        "samples": len(df)
    }
    save_metadata(metadata)
    print("\n=== Training completed ===")

if __name__ == "__main__":
    main()
