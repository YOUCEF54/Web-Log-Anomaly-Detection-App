# app/streamlit_app.py
import streamlit as st
import pandas as pd
import requests
import os
import json
from io import BytesIO
import time
import base64
import sys
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import websocket
import threading
import queue
import plotly.express as px


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CSV_PATH = os.path.join(ROOT, "data", "csic_database.csv")
LOG_PATH = os.path.join(ROOT, "data", "samples", "sample_access.log")
LOGO_PATH = os.path.join(os.path.dirname(__file__), "static", "logo.png")
MODELS_DIR = os.path.join(ROOT, "models")
API_URL = "http://127.0.0.1:5000"

st.set_page_config(
    page_title="Web Log Anomaly Detection",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Add src to sys.path so features can be imported if needed
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))
try:
    from features import build_features
except Exception:
    build_features = None
def inject_css():
    st.markdown("""
        <style>
            /* Main background */
            .stApp {
                background: #f5f7fa;
            }

            /* Card container */
            .card {
                background: white;
                padding: 20px;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.08);
                margin-bottom: 20px;
            }

            /* Titles */
            h1, h2, h3 {
                font-family: 'Segoe UI', sans-serif;
                font-weight: 600;
            }
            h1 {
                color: #D80032;
            }
            h2 {
                color: #223354;
            }
            h3 {
                color: #384b73;
            }

            /* Metric styling */
            div[data-testid="stMetric"] {
                background: white;
                padding: 15px;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            }

            /* Sidebar */
            section[data-testid="stSidebar"] {
                background-color: #f0f2f6;
            }

            /* Buttons */
            .stButton > button {
                background-color: #223354;
                color: white;
                border-radius: 8px;
                padding: 8px 20px;
                font-size: 15px;
                font-weight: 600;
                transition: 0.2s;
            }
            .stButton > button:hover {
                background-color: #445f8c;
                transform: scale(1.03);
            }
        </style>
    """, unsafe_allow_html=True)

inject_css()


# Utilities
def load_logo_b64():
    if os.path.exists(LOGO_PATH):
        with open(LOGO_PATH, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def headers(key):
    return {"x-api-key": key} if key else {}

def api_check_key(key):
    try:
        r = requests.get(f"{API_URL}/health", headers=headers(key), timeout=4)
        return r.status_code == 200
    except Exception:
        return False

def map_threat_color(df, level_col="Threat_Level"):
    if level_col in df.columns:
        color_map = {"Low": "🟢 Safe", "Medium": "🟡 Medium", "High": "🔴 High"}
        df["_Threat_Label"] = df[level_col].map(color_map).fillna(df[level_col])
    return df

# Login page
def login_page():
    logo_b64 = load_logo_b64()
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if logo_b64:
            st.markdown(f"<div style='text-align:center'><img src='data:image/png;base64,{logo_b64}' width='160'></div>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align:center'>Web Log Anomaly Detection</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center;color:#555'>Enter your API key to continue</p>", unsafe_allow_html=True)
        key = st.text_input("API Key", type="password")
        if st.button("Enter", use_container_width=True):
            if api_check_key(key):
                st.session_state["auth"] = True
                st.session_state["api_key"] = key
                st.success("API key valid ✔")
                st.rerun()
            else:
                st.error("Invalid API key ❌")
    st.markdown("<br><br><br>", unsafe_allow_html=True)

# Dashboard
def dashboard_page():
    st.title("📊 Dashboard — Web Log Intelligence Center")

    # ----------------------------------------------------
    # Load dataset
    # ----------------------------------------------------
    if not os.path.exists(CSV_PATH):
        st.warning("❌ Dataset not found at data/csic_database.csv")
        return

    df = pd.read_csv(CSV_PATH)

    # ====================================================
    # SECTION 1 — Dataset Quick View
    # ====================================================
    st.markdown("### 📁 Dataset Preview")
    st.dataframe(df.head(), use_container_width=True)

    # ====================================================
    # SECTION 2 — Global Metrics (Professional Cards)
    # ====================================================
    total_samples = len(df)
    unique_urls = df["url"].nunique() if "url" in df else 0
    attack_count = int(df["label"].sum()) if "label" in df else "N/A"
    avg_payload = round(df["body"].astype(str).apply(len).mean(), 2) if "body" in df else "N/A"

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📌 Total Samples", total_samples)
    col2.metric("🌐 Unique URLs", unique_urls)
    col3.metric("🚨 Detected Attacks", attack_count)
    col4.metric("📦 Avg Payload Size", avg_payload)

    st.markdown("---")

    # ====================================================
    # SECTION 3 — Feature Histograms
    # ====================================================
    st.markdown("### 🧬 Feature Distributions")

    feat_cols = ["url_length", "param_count", "payload_length", "url_entropy"]
    existing = [c for c in feat_cols if c in df.columns]

    if existing:
        colA, colB = st.columns(2)
        for i, col in enumerate(existing):
            target_col = colA if i % 2 == 0 else colB
            with target_col:
                st.markdown(f"**📌 {col} Distribution**")
                fig, ax = plt.subplots(figsize=(5, 3))
                sns.histplot(df[col].dropna(), bins=30, kde=True, ax=ax)
                ax.set_xlabel("")
                st.pyplot(fig)

    st.markdown("---")

    # ====================================================
    # SECTION 4 — Correlation Heatmap
    # ====================================================
    st.markdown("### 🔥 Correlation Heatmap")

    numeric_df = df.select_dtypes(include=["int64", "float64"])

    if numeric_df.shape[1] >= 2:
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.heatmap(numeric_df.corr(), annot=True, cmap="coolwarm", ax=ax)
        st.pyplot(fig)
    else:
        st.info("⚠️ Not enough numeric columns for correlation heatmap.")

    st.markdown("---")

    # ====================================================
    # SECTION 5 — Prediction Comparison RF / ISO
    # ====================================================
    if "RF_Prediction" in df.columns or "ISO_Prediction" in df.columns:
        st.markdown("### ⚔️ RandomForest vs IsolationForest — Prediction Comparison")

        col1, col2 = st.columns(2)

        if "RF_Prediction" in df.columns:
            with col1:
                st.markdown("**🌲 RF Prediction Count**")
                fig, ax = plt.subplots(figsize=(4, 3))
                df["RF_Prediction"].value_counts().sort_index().plot(kind="bar", ax=ax)
                st.pyplot(fig)

        if "ISO_Prediction" in df.columns:
            with col2:
                st.markdown("**🧩 ISO Prediction Count**")
                fig, ax = plt.subplots(figsize=(4, 3))
                df["ISO_Prediction"].value_counts().sort_index().plot(kind="bar", ax=ax)
                st.pyplot(fig)

    st.markdown("---")

    # ====================================================
    # SECTION 6 — Threat Score + Threat Level
    # ====================================================
    if "Threat_Score" in df.columns:
        st.markdown("### 🚨 Threat Score Distribution")

        fig, ax = plt.subplots(figsize=(7, 4))
        sns.histplot(df["Threat_Score"].dropna(), kde=True, bins=25, ax=ax)
        st.pyplot(fig)

        if "Threat_Level" in df.columns:
            st.markdown("### 🟥🟨🟩 Threat Level Breakdown")
            fig, ax = plt.subplots(figsize=(5, 3))
            df["Threat_Level"].value_counts().plot(kind="bar", ax=ax)
            st.pyplot(fig)

    st.markdown("---")

    # ====================================================
    # SECTION 7 — Attack Type Breakdown
    # ====================================================
    if "Attack_Type" in df.columns:
        st.markdown("### 🧨 Attack Type Count")

        fig, ax = plt.subplots(figsize=(6, 3))
        df["Attack_Type"].fillna("None").value_counts().plot(kind="bar", ax=ax)
        st.pyplot(fig)

    st.markdown("---")

    # ====================================================
    # SECTION 8 — Bonus Professional Add-ons
    # ====================================================
    # Top URLs requested
    if "url" in df.columns:
        st.markdown("### 🌍 Top Requested URLs")
        top_urls = df["url"].value_counts().head(10)

        fig, ax = plt.subplots(figsize=(6, 3))
        top_urls.plot(kind="bar", ax=ax)
        st.pyplot(fig)

    # Top user agents
    if "user_agent" in df.columns:
        st.markdown("### 🖥️ Most Common User Agents")
        uac = df["user_agent"].fillna("Unknown").value_counts().head(8)

        fig, ax = plt.subplots(figsize=(6, 3))
        uac.plot(kind="bar", ax=ax)
        st.pyplot(fig)


# Model Insight
def model_insight_page():
    st.title("🧠 Model Insight & Evaluation")

    # ---------------------------------------------------
    # 1. Load dataset
    # ---------------------------------------------------
    if not os.path.exists(CSV_PATH):
        st.error("Dataset not found")
        return

    df = pd.read_csv(CSV_PATH)

    # ---------------------------------------------------
    # 2. Load models
    # ---------------------------------------------------
    rf_model = None
    iso_model = None

    try:
        rf_model = joblib.load(os.path.join(MODELS_DIR, "rf_model.joblib"))
    except Exception as e:
        st.error(f"Could not load RandomForest: {e}")

    try:
        iso_model = joblib.load(os.path.join(MODELS_DIR, "iso_model.joblib"))
    except Exception as e:
        st.error(f"Could not load IsolationForest: {e}")

    # ---------------------------------------------------
    # 3. Build features
    # ---------------------------------------------------
    X, feature_cols = None, None
    if build_features is not None:
        try:
            X, feature_cols = build_features(df)
        except Exception as e:
            st.error(f"Feature extraction failed: {e}")
            return

    st.markdown("---")

    # ---------------------------------------------------
    # ⭐ SECTION 1 — RandomForest Feature Importance
    # ---------------------------------------------------
    st.markdown("## 🌲 RandomForest — Feature Importance")

    if rf_model is not None and feature_cols is not None:
        try:
            imp = rf_model.feature_importances_
            imp_df = pd.DataFrame({"Feature": feature_cols, "Importance": imp}).sort_values("Importance", ascending=False)

            fig, ax = plt.subplots(figsize=(8,4))
            sns.barplot(data=imp_df, x="Importance", y="Feature", ax=ax)
            ax.set_title("Feature Importance (Security-Relevant Features)")
            st.pyplot(fig)
        except Exception as e:
            st.error(f"Feature importance error: {e}")
    else:
        st.info("Feature importance unavailable.")

    st.markdown("---")

    # ---------------------------------------------------
    # ⭐ SECTION 2 — Comparison Normal vs Malicious (URL Entropy & URL Length)
    # ---------------------------------------------------
    st.markdown("## 🔎 Normal vs Malicious — URL Behaviour Analysis")

    if "label" in df.columns:
        try:
            col1, col2 = st.columns(2)

            with col1:
                fig, ax = plt.subplots(figsize=(4,3))
                sns.kdeplot(df[df["label"] == 0]["url_entropy"], label="Normal", fill=True)
                sns.kdeplot(df[df["label"] == 1]["url_entropy"], label="Malicious", fill=True)
                ax.set_title("URL Entropy Distribution")
                st.pyplot(fig)

            with col2:
                fig, ax = plt.subplots(figsize=(4,3))
                sns.kdeplot(df[df["label"] == 0]["url_length"], label="Normal", fill=True)
                sns.kdeplot(df[df["label"] == 1]["url_length"], label="Malicious", fill=True)
                ax.set_title("URL Length Distribution")
                st.pyplot(fig)

        except Exception as e:
            st.error(f"Entropy/Length distribution error: {e}")

    st.markdown("---")

    # ---------------------------------------------------
    # ⭐ SECTION 3 — Top Suspicious Parameters
    # ---------------------------------------------------
    st.markdown("## 🧪 Most Suspicious Query Parameters")

    try:
        df["params"] = df["url"].apply(lambda u: str(u).split("?")[1] if "?" in str(u) else "")
        params_series = df[df["label"] == 1]["params"].value_counts().head(15)

        fig, ax = plt.subplots(figsize=(6,3))
        params_series.plot(kind="barh", ax=ax)
        ax.set_title("Top Parameters in Malicious Requests")
        st.pyplot(fig)

    except Exception as e:
        st.info("No parameter patterns found in dataset.")

    st.markdown("---")

    # ---------------------------------------------------
    # ⭐ SECTION 4 — IsolationForest Anomaly Score Distribution
    # ---------------------------------------------------
    st.markdown("## 🧩 IsolationForest — Anomaly Score Distribution")

    if iso_model is not None and X is not None:
        try:
            scores = iso_model.decision_function(X)

            fig, ax = plt.subplots(figsize=(7,4))
            sns.histplot(scores, bins=30, kde=True, ax=ax)
            ax.set_title("Anomaly Scores (Lower = More Suspicious)")
            st.pyplot(fig)
        except Exception as e:
            st.error(f"IsolationForest score visualization error: {e}")

    st.markdown("---")

    # ---------------------------------------------------
    # ⭐ SECTION 5 — Examples of High-Risk Requests
    # ---------------------------------------------------
    st.markdown("## 🚨 High-Risk Real Examples")

    try:
        if "Threat_Score" in df.columns:
            high_risk = df.sort_values("Threat_Score", ascending=False).head(10)
        else:
            # fallback using IsoForest score
            anomaly_scores = iso_model.decision_function(X)
            df["_anomaly_score"] = anomaly_scores
            high_risk = df.sort_values("_anomaly_score").head(10)

        st.dataframe(high_risk[["ip", "url", "method", "payload", "label"]], use_container_width=True)

    except Exception as e:
        st.info("Could not extract high-risk examples.")

    st.markdown("---")

    # ---------------------------------------------------
    # ⭐ SECTION 6 — Confusion Matrix & Classification Report
    # ---------------------------------------------------
    st.markdown("## 📊 Classification Performance")

    if "label" in df.columns and rf_model is not None and X is not None:
        try:
            from sklearn.metrics import confusion_matrix, classification_report

            y_true = df["label"]
            y_pred = rf_model.predict(X)

            # Confusion matrix
            cm = confusion_matrix(y_true, y_pred)
            fig, ax = plt.subplots(figsize=(5,4))
            sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax)
            ax.set_title("Confusion Matrix")
            st.pyplot(fig)

            # Report
            st.markdown("### Classification Report")
            report = classification_report(y_true, y_pred, output_dict=True)
            st.dataframe(pd.DataFrame(report).transpose())

        except Exception as e:
            st.error(f"Performance evaluation error: {e}")

    st.markdown("---")

    st.success("Model Insight page loaded successfully ✔")


# Prediction page with tabs
def prediction_page():
    st.title("🧪 Test & Predict Logs")
    tab_csv, tab_log, tab_json = st.tabs(["📄 CSV", "📝 LOG/TXT", "📋 JSON"])

    with tab_csv:
        st.subheader("CSV Prediction")
        file = st.file_uploader("Upload CSV", type=["csv"], key="csv_up")

        if file:
            # Preview CSV
            file.seek(0)
            df = pd.read_csv(file)
            st.dataframe(df.head(), use_container_width=True)

            if st.button("Run CSV Prediction"):
                if "api_key" not in st.session_state:
                    st.error("API key missing")
                else:
                    file.seek(0)  # VERY IMPORTANT!
                    payload = file.read()

                    r = requests.post(
                        f"{API_URL}/predict-csv",
                        files={"file": ("upload.csv", payload)},
                        headers=headers(st.session_state.get("api_key"))
                    )

                    if r.status_code == 200:
                        res = pd.DataFrame(r.json().get("prediction", []))
                        res = map_threat_color(res)
                        st.dataframe(res, use_container_width=True)
                    else:
                        st.error(r.text)

    with tab_log:
        st.subheader("Log / Txt Prediction")
        file = st.file_uploader("Upload LOG/TXT", type=["log", "txt"], key="log_up")
        if file:
            try:
                text = file.read().decode("utf-8", errors="ignore")
                st.code("\n".join(text.splitlines()[:10]))
            except Exception:
                st.info("Binary preview not available.")
            if st.button("Parse & Predict Log"):
                if "api_key" not in st.session_state:
                    st.error("API key missing")
                else:
                    file.seek(0)
                    payload = file.read()
                    r = requests.post(f"{API_URL}/predict-log", files={"file": ("upload.log", payload)},
                                      headers=headers(st.session_state.get("api_key")))
                    if r.status_code == 200:
                        res = pd.DataFrame(r.json().get("prediction", []))
                        res = map_threat_color(res)
                        st.dataframe(res, use_container_width=True)
                    else:
                        st.error(r.text)

    with tab_json:
        st.subheader("JSON Prediction")
        json_input = st.text_area("Paste JSON array or object", height=200)
        if st.button("Predict JSON"):
            if not json_input:
                st.error("Paste JSON")
            elif "api_key" not in st.session_state:
                st.error("API key missing")
            else:
                try:
                    data = json.loads(json_input)
                except Exception as e:
                    st.error(f"Invalid JSON: {e}")
                    data = None
                if data is not None:
                    r = requests.post(f"{API_URL}/predict-json", json=data, headers=headers(st.session_state.get("api_key")))
                    if r.status_code == 200:
                        res = pd.DataFrame(r.json().get("prediction", []))
                        res = map_threat_color(res)
                        st.dataframe(res, use_container_width=True)
                    else:
                        st.error(r.text)

# Replay simulator (WebSocket)
def replay_page():
    st.title("🔄 Replay Simulator (WebSocket)")

    import websocket   # <--- FIX: correct client library

    # INIT
    if "ws_conn" not in st.session_state:
        st.session_state.ws_conn = None
    if "replay_data" not in st.session_state:
        st.session_state.replay_data = []

    url = st.text_input("WebSocket URL", "ws://localhost:6789")
    col1, col2, col3 = st.columns([1, 1, 1])

    # ---------------------------------------------------
    # CONNECT
    # ---------------------------------------------------
    if col1.button("Connect"):
        try:
            ws = websocket.create_connection(url, timeout=4)
            st.session_state.ws_conn = ws
            st.success("🟢 Connected to WebSocket server")
        except Exception as e:
            st.error(f"❌ Failed to connect: {e}")
            st.session_state.ws_conn = None

    # ---------------------------------------------------
    # DISCONNECT
    # ---------------------------------------------------
    if col2.button("Disconnect"):
        if st.session_state.ws_conn:
            try:
                st.session_state.ws_conn.close()
            except:
                pass
            st.session_state.ws_conn = None
            st.warning("🔴 Disconnected")
        else:
            st.info("No active connection")

    # ---------------------------------------------------
    # FETCH MESSAGES
    # ---------------------------------------------------
    if col3.button("Fetch messages"):
        ws = st.session_state.ws_conn
        if ws is None:
            st.warning("Not connected")
        else:
            ws.settimeout(0.3)
            new_msgs = []

            while True:
                try:
                    raw = ws.recv()
                    new_msgs.append(json.loads(raw))
                except Exception:
                    break

            # --- APPLY PREDICTION ON EACH LOG ---
            enriched = []
            for msg in new_msgs:
                log_line = msg.get("log", "")
                fake_file = BytesIO((log_line + "\n").encode())

                try:
                    r = requests.post(
                        f"{API_URL}/predict-log",
                        files={"file": ("stream.log", fake_file.getvalue())},
                        headers=headers(st.session_state["api_key"]),
                    )
                    if r.status_code == 200:
                        preds = r.json().get("prediction", [])
                        if preds:
                            enriched.append(preds[0])
                except:
                    pass

            if enriched:
                st.session_state.replay_data.extend(enriched)
                st.session_state.replay_data = st.session_state.replay_data[-200:]
                st.success(f"📥 Received {len(enriched)} messages with prediction")
            else:
                st.info("No new messages")

    # ---------------------------------------------------
    # DISPLAY
    # ---------------------------------------------------
    st.markdown("### 📜 Recent messages")

    if st.session_state.replay_data:
        df = pd.DataFrame(st.session_state.replay_data)
        df = map_threat_color(df)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No messages yet — Connect then Fetch")


# Live stream: file replay -> API
def stream_page():
    st.title("📡 Live Streaming — Real Time Detection")

    # -------------------------------------------------
    # SAFETY INITIALIZATION (fix KeyError)
    # -------------------------------------------------
    if "stream" not in st.session_state:
        st.session_state["stream"] = False

    if "stream_history" not in st.session_state:
        st.session_state["stream_history"] = []

    if "logs" not in st.session_state:
        st.session_state["logs"] = []

    # -------------------------------------------------
    # CHECK LOG FILE
    # -------------------------------------------------
    if not os.path.exists(LOG_PATH):
        st.error(f"No log file found at: {LOG_PATH}")
        return

    # -------------------------------------------------
    # UI BUTTONS
    # -------------------------------------------------
    col1, col2 = st.columns(2)

    if col1.button("▶️ Start Streaming"):
        st.session_state["stream"] = True

    if col2.button("⛔ Stop"):
        st.session_state["stream"] = False

    output = st.empty()

    # -------------------------------------------------
    # STREAMING MODE (LIVE PREDICTION)
    # -------------------------------------------------
    if st.session_state["stream"]:
        try:
            lines = open(LOG_PATH, "r", encoding="utf-8", errors="ignore").read().splitlines()
        except Exception as e:
            st.error(f"Could not read log file: {e}")
            return

        for line in lines:
            if not st.session_state["stream"]:
                break  # streaming stopped by user

            fake = BytesIO((line + "\n").encode())

            # Send single-line log to API
            try:
                resp = requests.post(
                    f"{API_URL}/predict-log",
                    files={"file": ("stream.log", fake.getvalue())},
                    headers=headers(st.session_state.get("api_key"))
                )
            except Exception as e:
                st.error(f"API connection failed: {e}")
                st.session_state["stream"] = False
                break

            if resp.status_code == 200:
                try:
                    preds = resp.json().get("prediction", [])
                    if preds:
                        row = preds[0]

                        # Add visual threat label
                        row["_Threat_Label"] = {
                            "Low": "🟢 Safe",
                            "Medium": "🟡 Medium",
                            "High": "🔴 High"
                        }.get(row.get("Threat_Level"), "⚪ Unknown")

                        # Rolling history
                        st.session_state["stream_history"].append(row)
                        st.session_state["stream_history"] = st.session_state["stream_history"][-200:]

                        # Live update
                        output.dataframe(
                            pd.DataFrame(st.session_state["stream_history"]),
                            width="stretch"
                        )

                except Exception as e:
                    st.error(f"Error decoding API response: {e}")
                    break

            else:
                st.error(f"API returned {resp.status_code}: {resp.text}")
                st.session_state["stream"] = False
                break

            time.sleep(0.30)

    # -------------------------------------------------
    # WHEN STREAMING IS OFF (SHOW HISTORY + OPTIONAL TIMELINE)
    # -------------------------------------------------
    else:
        if st.session_state["stream_history"]:
            st.markdown("### 📜 Last Streamed Logs")
            output.dataframe(
                pd.DataFrame(st.session_state["stream_history"]),
                width="stretch"
            )

            # Optional threat timeline if logs contain timestamps
            df = pd.DataFrame(st.session_state["stream_history"])

            if "timestamp" in df.columns and "Threat_Score" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

                if df["timestamp"].notna().sum() > 2:
                    st.markdown("### 📈 Threat Score Timeline")
                    fig, ax = plt.subplots(figsize=(10, 3))
                    ax.plot(df["timestamp"], df["Threat_Score"])
                    ax.set_title("Threat Score Over Time", fontsize=12)
                    ax.set_xlabel("Time")
                    ax.set_ylabel("Score")
                    st.pyplot(fig)

        else:
            st.info("Stream stopped. Click **Start Streaming** to replay logs.")

# About
def about_page():
    st.title("ℹ️ About")
    logo = load_logo_b64()
    if logo:
        st.image(base64.b64decode(logo), width=90)
    st.write("""
    Web Log Anomaly Detection — demo system combining RandomForest + IsolationForest,
    signature detection and a threat scoring function. Use API key to authenticate.
    """)

# Routing
if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    login_page()
else:
    with st.sidebar:
        st.markdown("""
            <h2 style='color:#223354;'>🛡️ Navigation</h2>
            <hr>
        """, unsafe_allow_html=True)

        page = st.radio(" ", ["Dashboard", "Model Insight", "Prediction", "Replay Simulator", "Live Stream", "About"])

    if page == "Dashboard":
        dashboard_page()
    elif page == "Model Insight":
        model_insight_page()
    elif page == "Prediction":
        prediction_page()
    elif page == "Replay Simulator":
        replay_page()
    elif page == "Live Stream":
        stream_page()
    else:
        about_page()
