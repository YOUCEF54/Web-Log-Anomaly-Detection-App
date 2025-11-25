
# api/app.py
"""
Web Log Anomaly Detection — Flask API (final)
Endpoints:
 - GET  /health
 - POST /predict-json  (requires x-api-key header)
 - POST /predict-csv   (file upload, requires x-api-key header)
 - POST /predict-log   (apache log file upload, requires x-api-key header)
Return: JSON (list of records or single record)
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import joblib
import os
import traceback
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# Import project helpers from src (features, attack_signatures, threat_score)
# Make sure your PYTHONPATH allows "src" or run from repo root.
from src.features import build_features
from src.attack_signatures import annotate_df
from src.threat_score import compute_threat_score
from src.parse_logs import parse_apache_log_lines  # parser for access.log lines

# CONFIG
API_KEY = os.environ.get("WLAD_API_KEY", "weblogs-detection-2025")
MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models"))

app = Flask(__name__)
CORS(app)

# Helper: load models safely
def load_models():
    rf_path = os.path.join(MODEL_DIR, "rf_model.joblib")
    iso_path = os.path.join(MODEL_DIR, "iso_model.joblib")
    if not os.path.exists(rf_path) or not os.path.exists(iso_path):
        raise FileNotFoundError(f"Model files not found in {MODEL_DIR}. Expect rf_model.joblib and iso_model.joblib")
    rf = joblib.load(rf_path)
    iso = joblib.load(iso_path)
    return rf, iso

try:
    MODEL_RF, MODEL_ISO = load_models()
    print("[INFO] Models loaded from:", MODEL_DIR)
except Exception as e:
    print("[ERROR] Failed to load models:", str(e))
    MODEL_RF, MODEL_ISO = None, None


# -------------------------
# Helpers
# -------------------------
def require_key():
    key = request.headers.get("x-api-key") or request.args.get("api_key")
    return key == API_KEY

def safe_build_and_predict(df: pd.DataFrame):
    """
    Input: raw dataframe (may miss columns)
    Returns: df with predictions + attack signatures + threat score
    """
    # Ensure the DataFrame has the expected columns (features.build_features will fill missing columns)
    X, feature_cols = build_features(df)

    # predict
    if MODEL_RF is None or MODEL_ISO is None:
        raise RuntimeError("Models not loaded on server")

    rf_preds = MODEL_RF.predict(X)
    iso_raw = MODEL_ISO.predict(X)            # iso -> -1 anomaly, 1 normal
    iso_preds = (iso_raw == -1).astype(int)

    # attach predictions to original df copy
    out = df.copy().reset_index(drop=True)
    out["RF_Prediction"] = pd.Series(rf_preds).astype(int)
    out["ISO_Prediction"] = pd.Series(iso_preds).astype(int)

    # compute some helper fields used by threat scoring
    # ensure payload_length and url_entropy exist
    out["payload_length"] = out.get("body", "").fillna("").astype(str).apply(len)
    # compute url_entropy via features module (build_features computed url_entropy on X; reuse X)
    # X may have 'url_entropy' column; if not, create zero
    if "url_entropy" in X.columns:
        out["url_entropy"] = X["url_entropy"].astype(float).values
    else:
        out["url_entropy"] = 0.0

    # annotate signatures and compute threat score
    out = annotate_df(out)
    out = compute_threat_score(out)

    return out

# -------------------------
# Routes
# -------------------------
@app.route("/health", methods=["GET"])
def health():
    ok = (MODEL_RF is not None and MODEL_ISO is not None)
    return jsonify({"status": "OK" if ok else "WARN", "models_loaded": ok}), 200

@app.route("/", methods=["GET"])
def root():
    return jsonify({"message": "Web Log Anomaly Detection API", "models_loaded": MODEL_RF is not None and MODEL_ISO is not None})

@app.route("/predict-json", methods=["POST"])
def predict_json():
    try:
        if not require_key():
            return jsonify({"status": "error", "message": "Missing or invalid API key (x-api-key)"}), 401

        payload = request.get_json(force=True)
        if payload is None:
            return jsonify({"status": "error", "message": "Empty JSON"}), 400

        # Accept single dict or list of dicts
        if isinstance(payload, dict):
            df = pd.DataFrame([payload])
        else:
            df = pd.DataFrame(payload)

        out = safe_build_and_predict(df)
        return jsonify({"status": "ok", "prediction": out.to_dict(orient="records")}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e), "trace": traceback.format_exc()}), 500

@app.route("/predict-csv", methods=["POST"])
def predict_csv():
    try:
        if not require_key():
            return jsonify({"status": "error", "message": "Missing or invalid API key (x-api-key)"}), 401

        if "file" not in request.files:
            return jsonify({"status": "error", "message": "No file uploaded (use 'file' form field)"}), 400

        f = request.files["file"]
        df = pd.read_csv(f)
        out = safe_build_and_predict(df)
        return jsonify({"status": "ok", "prediction": out.to_dict(orient="records")}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e), "trace": traceback.format_exc()}), 500

@app.route("/predict-log", methods=["POST"])
def predict_log():
    try:
        if not require_key():
            return jsonify({"status": "error", "message": "Missing or invalid API key (x-api-key)"}), 401

        if "file" not in request.files:
            return jsonify({"status": "error", "message": "No file uploaded (use 'file' form field)"}), 400

        f = request.files["file"]
        content = f.read().decode(errors="ignore").splitlines()
        df = parse_apache_log_lines(content)

        if df is None or df.empty:
            return jsonify({"status": "error", "message": "Log file parsed zero lines"}), 400

        out = safe_build_and_predict(df)
        return jsonify({"status": "ok", "prediction": out.to_dict(orient="records")}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e), "trace": traceback.format_exc()}), 500


# Run
if __name__ == "__main__":
    print("Starting API on http://0.0.0.0:5000 (use x-api-key header to authenticate)")
    app.run(host="0.0.0.0", port=5000, debug=True)
