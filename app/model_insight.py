# app/model_insight.py
import streamlit as st
import pandas as pd
import joblib
import os
import base64
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from io import BytesIO

st.set_page_config(page_title="Model Insight", layout="wide", page_icon="🔎")

# paths
LOGO_PATH = "static/logo.png"
MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models"))
RF_PATH = os.path.join(MODEL_DIR, "rf_model.joblib")
ISO_PATH = os.path.join(MODEL_DIR, "iso_model.joblib")
DATA_PATH = "../data/csic_database.csv"

# header + logo
if os.path.exists(LOGO_PATH):
    logo_b64 = base64.b64encode(open(LOGO_PATH, "rb").read()).decode()
    st.markdown(f"<div style='display:flex;align-items:center;gap:12px'>"
                f"<img src='data:image/png;base64,{logo_b64}' width='84'>"
                f"<h1>Model Insight & Diagnostics</h1></div>", unsafe_allow_html=True)
else:
    st.title("Model Insight & Diagnostics")

st.write("Inspect feature importance, model behaviour, and evaluation metrics.")

# load dataset
@st.cache_data
def load_data():
    if not os.path.exists(DATA_PATH):
        return None
    df = pd.read_csv(DATA_PATH)
    return df

df = load_data()
if df is None:
    st.warning("Dataset file not found at ../data/csic_database.csv — run parse_logs.py first.")
else:
    st.markdown(f"**Dataset size:** {len(df):,} rows")

# Load models
col1, col2 = st.columns(2)
with col1:
    if os.path.exists(RF_PATH):
        rf = joblib.load(RF_PATH)
        st.success("RandomForest loaded")
    else:
        rf = None
        st.warning("RF model not found in models/")

with col2:
    if os.path.exists(ISO_PATH):
        iso = joblib.load(ISO_PATH)
        st.success("IsolationForest loaded")
    else:
        iso = None
        st.warning("ISO model not found in models/")

# Feature importance (RF)
if rf is not None:
    st.subheader("Feature importance (RandomForest)")
    try:
        importances = rf.feature_importances_
        # try to read feature names from model (if stored) or from features module
        if hasattr(rf, "feature_names_in_"):
            feature_cols = list(rf.feature_names_in_)
        else:
            # fallback: try to infer from dataset by running simple build_features if present
            feature_cols = None

        if feature_cols is None:
            # attempt minimal safe inference: numeric columns sorted by importance length
            # create a placeholder names series
            feature_cols = [f"f{i}" for i in range(len(importances))]

        fi_df = pd.DataFrame({"feature": feature_cols, "importance": importances}).sort_values("importance", ascending=False)
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(x="importance", y="feature", data=fi_df, ax=ax)
        ax.set_title("RandomForest Feature Importance")
        st.pyplot(fig)
        st.dataframe(fi_df.reset_index(drop=True), use_container_width=True)
    except Exception as e:
        st.error(f"Could not compute/import feature importance: {e}")

# Isolation forest insights
if iso is not None and df is not None:
    st.subheader("IsolationForest: anomaly score distribution")
    try:
        # Build features on-the-fly: try to call src.features if available
        import sys, os
        sys.path.append(os.path.abspath("../src"))
        from features import build_features
        X, feature_cols = build_features(df)
        iso_scores = iso.decision_function(X)
        fig2, ax2 = plt.subplots(figsize=(8, 4))
        ax2.hist(iso_scores, bins=60)
        ax2.set_title("IsolationForest decision_function scores")
        st.pyplot(fig2)
        st.write("Lower scores → more anomalous (IsolationForest).")
    except Exception as e:
        st.info("Could not compute ISO scores locally — ensure src/features.py exists and models were trained.")
        st.exception(e)

# Export model summaries
st.subheader("Download models / artifacts")
col1, col2 = st.columns(2)
with col1:
    if os.path.exists(RF_PATH):
        with open(RF_PATH, "rb") as f:
            b = f.read()
            st.download_button("Download RandomForest (.joblib)", data=b, file_name="rf_model.joblib")
with col2:
    if os.path.exists(ISO_PATH):
        with open(ISO_PATH, "rb") as f:
            b = f.read()
            st.download_button("Download IsolationForest (.joblib)", data=b, file_name="iso_model.joblib")

st.info("Tip: feature importance + iso score histogram help justify why predictions are made (good for your report).")
