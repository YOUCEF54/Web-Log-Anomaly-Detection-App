# app/client.py
import streamlit as st
import pandas as pd
import requests
import base64
import os
import time
from io import StringIO, BytesIO

st.set_page_config(page_title="Batch Client", layout="wide", page_icon="📤")

LOGO = "static/logo.png"
API_URL = "http://127.0.0.1:5000"

if os.path.exists(LOGO):
    b = base64.b64encode(open(LOGO, "rb").read()).decode()
    st.markdown(f"<div style='display:flex;align-items:center;gap:12px'><img src='data:image/png;base64,{b}' width='60'><h2>Batch Client & Tester</h2></div>", unsafe_allow_html=True)
else:
    st.title("Batch Client & Tester")

st.write("Upload a CSV (or log) of requests, call API for predictions, and download results.")

api_key = st.text_input("API Key", type="password")
if not api_key:
    st.warning("Enter API key to proceed.")
    st.stop()
headers = {"X-API-KEY": api_key}

uploaded = st.file_uploader("Upload CSV (or .log) for batch predictions", type=["csv", "log", "txt"])
col1, col2 = st.columns(2)

with col1:
    if st.button("Run prediction on uploaded file") and uploaded:
        mode = "CSV" if uploaded.name.lower().endswith(".csv") else "LOG"
        files = {"file": (uploaded.name, uploaded, uploaded.type)}
        endpoint = "/predict-csv" if mode == "CSV" else "/predict-log"
        with st.spinner("Sending to API..."):
            resp = requests.post(API_URL + endpoint, files=files, headers=headers)
        if resp.status_code == 200:
            df = pd.DataFrame(resp.json())
            st.success(f"Got {len(df)} predictions")
            st.dataframe(df.head(10), use_container_width=True)
            csv = df.to_csv(index=False).encode()
            st.download_button("Download results (.csv)", data=csv, file_name="predictions.csv")
        else:
            st.error(f"API Error: {resp.status_code} - {resp.text}")

with col2:
    if st.button("Generate synthetic sample CSV (100 lines)"):
        # simple synthetic CSV with required columns
        rows = []
        import random
        for i in range(100):
            rows.append({
                "url": f"/test/page?id={i}",
                "method": random.choice(["GET","POST"]),
                "user_agent": "Mozilla/5.0",
                "cookie": "",
                "content_type": "",
                "content_length": 0,
                "body": ""
            })
        df = pd.DataFrame(rows)
        csv = df.to_csv(index=False).encode()
        st.download_button("Download synthetic sample", data=csv, file_name="sample_logs.csv")
        st.success("Synthetic sample ready to download.")

st.markdown("---")
st.info("You can also call the API using curl or Postman to test endpoints /predict-csv and /predict-log.")
