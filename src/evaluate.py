# src/evaluate.py
"""
Evaluation script for both models. Saves confusion matrices as images.
"""
import os
import joblib
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report, confusion_matrix
from features import build_features
from config import CSIC_CSV, MODELS_DIR

PLOTS_DIR = os.path.join(MODELS_DIR, "plots")
os.makedirs(PLOTS_DIR, exist_ok=True)

def main():
    if not os.path.exists(CSIC_CSV):
        raise FileNotFoundError("Parsed dataset missing. Run parse_logs.py first.")

    df = pd.read_csv(CSIC_CSV)
    if "label" not in df.columns:
        raise ValueError("'label' column missing.")
    df = df.dropna(subset=["label"])
    df["label"] = df["label"].astype(int)

    X, feature_cols = build_features(df)
    y = df["label"]

    # RandomForest
    rf_path = os.path.join(MODELS_DIR, "rf_model.joblib")
    if os.path.exists(rf_path):
        rf = joblib.load(rf_path)
        rf_preds = rf.predict(X)
        print("RandomForest Report:\n", classification_report(y, rf_preds))
        cm = confusion_matrix(y, rf_preds)
        plt.figure(figsize=(6,4))
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues")
        plt.title("RF Confusion Matrix")
        plt.tight_layout()
        rf_png = os.path.join(PLOTS_DIR, "rf_confusion.png")
        plt.savefig(rf_png)
        print("Saved", rf_png)
        plt.close()
    else:
        print("RF model not found, skipping RF evaluation.")

    # IsolationForest
    iso_path = os.path.join(MODELS_DIR, "iso_model.joblib")
    if os.path.exists(iso_path):
        iso = joblib.load(iso_path)
        iso_preds = (iso.predict(X) == -1).astype(int)
        print("IsolationForest Report:\n", classification_report(y, iso_preds))
        cm2 = confusion_matrix(y, iso_preds)
        plt.figure(figsize=(6,4))
        sns.heatmap(cm2, annot=True, fmt="d", cmap="Reds")
        plt.title("ISO Confusion Matrix")
        plt.tight_layout()
        iso_png = os.path.join(PLOTS_DIR, "iso_confusion.png")
        plt.savefig(iso_png)
        print("Saved", iso_png)
        plt.close()
    else:
        print("ISO model not found, skipping ISO evaluation.")

if __name__ == "__main__":
    main()
