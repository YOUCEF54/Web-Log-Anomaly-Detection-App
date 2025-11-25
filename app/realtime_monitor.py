# app/realtime_monitor.py
import streamlit as st
import pandas as pd
import plotly.express as px
import os
import base64
import time
import threading
import queue
from websocket import WebSocketApp

st.set_page_config(page_title="Real-Time Monitor", layout="wide", page_icon="⚡")

LOGO_PATH = "static/logo.png"
if os.path.exists(LOGO_PATH):
    b = base64.b64encode(open(LOGO_PATH, "rb").read()).decode()
    st.markdown(f"<div style='display:flex;align-items:center;gap:12px'>"
                f"<img src='data:image/png;base64,{b}' width='72'>"
                f"<h2>Real-Time Monitor</h2></div>", unsafe_allow_html=True)
else:
    st.title("Real-Time Monitor")

st.write("Stream live log events (WebSocket) or upload sample logs for simulation.")

# UI controls
ws_url = st.text_input("WebSocket URL (socket.io compatible)", "ws://127.0.0.1:6000/socket.io/?EIO=4&transport=websocket")
start = st.button("Start Stream")
stop = st.button("Stop Stream")
simulate = st.button("Simulate (sample file)")

# area placeholders
chart_ph = st.empty()
table_ph = st.empty()
status_ph = st.empty()

q = queue.Queue()
ws_app = None
thread_obj = None

def on_message(ws, message):
    try:
        if '{' in message:
            idx = message.index('{')
            payload = message[idx:]
            import json
            obj = json.loads(payload)
            q.put(obj)
    except Exception as e:
        print("parse err", e)

def on_error(ws, err):
    q.put({"__ws_error": str(err)})

def on_close(ws, c, m):
    q.put({"__ws_closed": True})

def run_ws(url):
    global ws_app
    ws_app = WebSocketApp(url, on_message=on_message, on_error=on_error, on_close=on_close)
    ws_app.run_forever()

# data frame to collect last N events
cols = ["timestamp", "url", "method", "RF_Prediction", "ISO_Prediction", "Anomaly"]
events_df = pd.DataFrame(columns=cols)

# start thread
if start:
    status_ph.info("Starting WebSocket client...")
    thread_obj = threading.Thread(target=run_ws, args=(ws_url,), daemon=True)
    thread_obj.start()
    status_ph.success("WebSocket client started")

if stop:
    status_ph.warning("Stopping WebSocket (attempt).")
    if ws_app:
        ws_app.close()

# simulate: read sample log and push fake events (local)
if simulate:
    sample_path = "../data/sample_access.log"
    if os.path.exists(sample_path):
        lines = open(sample_path, "r", encoding="utf-8", errors="ignore").read().splitlines()
        # simple parser — produce events
        import random, datetime, json
        for i, ln in enumerate(lines[:150]):
            events_df = pd.concat([events_df, pd.DataFrame([{
                "timestamp": pd.Timestamp.now(),
                "url": f"/sample/path/{i}",
                "method": random.choice(["GET","POST"]),
                "RF_Prediction": random.choice([0,0,0,1]),
                "ISO_Prediction": random.choice([0,0,1]),
                "Anomaly": 0
            }])], ignore_index=True)
        status_ph.success("Loaded sample events for simulation.")
    else:
        status_ph.error("No sample_access.log found in ../data/")

# polling the queue and updating UI
last_update = time.time()
while True:
    try:
        item = q.get(timeout=0.2)
    except queue.Empty:
        item = None

    if item is not None:
        # handle ws meta
        if "__ws_error" in item:
            status_ph.error("WebSocket error: " + item["__ws_error"])
            continue
        if "__ws_closed" in item:
            status_ph.info("WebSocket closed by server.")
            break

        # normalize incoming event (expect dict with method/url/preds)
        row = {
            "timestamp": pd.Timestamp.now(),
            "url": item.get("url", item.get("path", "")),
            "method": item.get("method", ""),
            "RF_Prediction": int(item.get("RF_Prediction", 0)),
            "ISO_Prediction": int(item.get("ISO_Prediction", 0)),
            "Anomaly": int(item.get("Anomaly", 0))
        }
        events_df = pd.concat([events_df, pd.DataFrame([row])], ignore_index=True)
        # keep last 500
        if len(events_df) > 500:
            events_df = events_df.tail(500).reset_index(drop=True)

    # update UI every ~0.8s
    if time.time() - last_update > 0.8:
        last_update = time.time()
        if not events_df.empty:
            fig = px.line(events_df.tail(200), x="timestamp", y="Anomaly", title="Live anomaly stream (last events)")
            chart_ph.plotly_chart(fig, use_container_width=True)
            table_ph.dataframe(events_df.tail(12), use_container_width=True)
        else:
            chart_ph.info("No events yet — start the WebSocket or simulate sample logs.")

    # non-blocking exit for streamlit
    if stop:
        break
