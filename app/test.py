import streamlit as st
import pandas as pd
import requests
import json
import matplotlib.pyplot as plt
import seaborn as sns

API_URL = "http://localhost:5000/predict-log"
API_KEY = "imane_2025"

st.title("🔍 Web Log Anomaly Detection — Log File Demo")
st.write("Upload an Apache access.log file to detect anomalies.")

uploaded = st.file_uploader("Upload Apache LOG File", type=["log", "txt"])

if uploaded:
    st.info("📤 Sending log file to API...")

    files = {"file": uploaded}
    headers = {"x-api-key": API_KEY}

    # -----------------------------------------
    # API CALL
    # -----------------------------------------
    response = requests.post(API_URL, files=files, headers=headers)

    try:
        data = response.json()
    except:
        st.error("❌ API did not return JSON.")
        st.text(response.text)
        st.stop()

    # -----------------------------------------
    # HANDLE API RESPONSE
    # -----------------------------------------
    if data.get("status") != "ok":
        st.error("❌ API Error")
        st.json(data)
        st.stop()

    preds = data["prediction"]
    df = pd.DataFrame(preds)

    st.success("✅ Log file processed successfully!")

    # -----------------------------------------
    # SHOW RESULTS
    # -----------------------------------------
    st.subheader("📌 Log Parsed + Predictions")
    st.dataframe(df.head())

    # -----------------------------------------
    # THREAT SCORE
    # -----------------------------------------
    threat_col = None
    for col in df.columns:
        if "threat" in col.lower():
            threat_col = col

    if threat_col:
        st.subheader("📊 Threat Score Histogram")

        fig, ax = plt.subplots()
        ax.hist(df[threat_col], bins=5)
        ax.set_xlabel("Threat Score")
        ax.set_ylabel("Count")
        st.pyplot(fig)

        st.subheader("🚨 Anomalies détectées")
        st.dataframe(df[df[threat_col] > 0])
    else:
        st.warning("⚠️ No threat score in API output.")

    # -----------------------------------------
    # HEATMAP DES PREDICTIONS
    # -----------------------------------------
    pred_cols = [c for c in df.columns if "prediction" in c.lower() or "score" in c.lower()]

    if len(pred_cols) >= 2:
        st.subheader("🔥 Heatmap Correlation")

        fig, ax = plt.subplots()
        sns.heatmap(df[pred_cols].corr(), annot=True, cmap="coolwarm", ax=ax)
        st.pyplot(fig)
    else:
        st.info("ℹ️ Not enough prediction fields for heatmap.")
