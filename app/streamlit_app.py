import streamlit as st
import pandas as pd
import requests
import json
from io import StringIO
import plotly.express as px
import plotly.graph_objects as go

API_URL = "http://127.0.0.1:5000"

# -------------------------
# UI SETUP
# -------------------------
st.set_page_config(
    page_title="Web Log Anomaly Detection",
    layout="wide",
    page_icon="🛡️"
)

st.title("🛡️ Web Log Anomaly Detection Dashboard")
st.write("Upload log files (**CSV or Apache log**) and detect anomalies using RF, ISO, signatures & threat scoring.")

# -------------------------
# Sidebar – API KEY
# -------------------------
st.sidebar.header("🔐 API Settings")

api_key = st.sidebar.text_input("Enter API Key", type="password")
if not api_key:
    st.sidebar.warning("Enter your API key to enable predictions.")

# -------------------------
# File Upload
# -------------------------
st.sidebar.header("📤 Upload Logs")
uploaded_file = st.sidebar.file_uploader(
    "Upload CSV, LOG, TXT or JSON file",
    type=["csv", "log", "txt", "json"],
    accept_multiple_files=False
)

run_btn = st.sidebar.button("🚀 Run Prediction")

# -------------------------
# Utility
# -------------------------
def call_api_json(records):
    """Send a JSON list to /predict-json"""
    headers = {"x-api-key": api_key} if api_key else {}
    res = requests.post(f"{API_URL}/predict-json", json={"logs": records}, headers=headers)
    if res.status_code != 200:
        st.error(f"API error: {res.text}")
        return None  
    return res.json().get("prediction", [])

def call_api_csv(df):
    """Send a CSV file to /predict-csv"""
    headers = {"x-api-key": api_key} if api_key else {}
    files = {"file": ("uploaded.csv", df.to_csv(index=False), "text/csv")}
    res = requests.post(f"{API_URL}/predict-csv", files=files, headers=headers)
    if res.status_code != 200:
        st.error(f"API error: {res.text}")
        return None
    return res.json().get("prediction", [])

# -------------------------
# Parser for LOG files
# -------------------------
def parse_log_lines(lines):
    """Send raw lines to API /parse-log (new endpoint)"""
    headers = {"x-api-key": api_key} if api_key else {}
    res = requests.post(f"{API_URL}/parse-log", json={"lines": lines}, headers=headers)
    if res.status_code != 200:
        st.error(f"Parse error: {res.text}")
        return None
    return res.json().get("parsed", [])

# -------------------------
# Visualization Functions
# -------------------------
def display_visualizations(result_df):
    """Display comprehensive visualizations and metrics for the prediction results"""
    
    if result_df.empty:
        st.warning("No data to visualize")
        return
    
    # -------------------------
    # 1. SUMMARY METRICS
    # -------------------------
    st.markdown("---")
    st.subheader("📊 Summary Metrics")
    
    total_requests = len(result_df)
    
    # Count anomalies (either RF or ISO flagged as anomaly)
    rf_anomalies = result_df.get("RF_Prediction", pd.Series([0]*len(result_df))).sum()
    iso_anomalies = result_df.get("ISO_Prediction", pd.Series([0]*len(result_df))).sum()
    total_anomalies = len(result_df[(result_df.get("RF_Prediction", 0) == 1) | (result_df.get("ISO_Prediction", 0) == 1)])
    
    anomaly_pct = (total_anomalies / total_requests * 100) if total_requests > 0 else 0
    
    # Threat score stats
    threat_scores = result_df.get("threat_score", pd.Series([0]*len(result_df)))
    avg_threat = threat_scores.mean() if len(threat_scores) > 0 else 0
    max_threat = threat_scores.max() if len(threat_scores) > 0 else 0
    
    # Display metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Requests", f"{total_requests:,}")
    
    with col2:
        st.metric("Anomalies Detected", f"{total_anomalies} ({anomaly_pct:.1f}%)")
    
    with col3:
        st.metric("Avg Threat Score", f"{avg_threat:.1f}")
    
    with col4:
        severity = "🔴 CRITICAL" if max_threat >= 70 else "🟠 HIGH" if max_threat >= 50 else "🟡 MEDIUM" if max_threat >= 30 else "🟢 LOW"
        st.metric("Max Threat Score", f"{max_threat:.0f} {severity}")
    
    # -------------------------
    # 2. VISUALIZATIONS
    # -------------------------
    st.markdown("---")
    st.subheader("📈 Visual Analysis")
    
    # Create two columns for charts
    col_left, col_right = st.columns(2)
    
    # -------------------------
    # 2.1 Anomaly Distribution (Pie Chart)
    # -------------------------
    with col_left:
        st.markdown("#### Anomaly Distribution")
        
        anomaly_counts = {
            "Normal": total_requests - total_anomalies,
            "Anomalous": total_anomalies
        }
        
        fig_pie = px.pie(
            values=list(anomaly_counts.values()),
            names=list(anomaly_counts.keys()),
            color=list(anomaly_counts.keys()),
            color_discrete_map={"Normal": "#2ecc71", "Anomalous": "#e74c3c"},
            hole=0.4
        )
        fig_pie.update_layout(height=350)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # -------------------------
    # 2.2 Threat Score Distribution (Histogram)
    # -------------------------
    with col_right:
        st.markdown("#### Threat Score Distribution")
        
        fig_hist = px.histogram(
            result_df,
            x="threat_score" if "threat_score" in result_df.columns else [0]*len(result_df),
            nbins=20,
            color_discrete_sequence=["#3498db"]
        )
        fig_hist.update_layout(
            xaxis_title="Threat Score",
            yaxis_title="Count",
            height=350,
            showlegend=False
        )
        st.plotly_chart(fig_hist, use_container_width=True)
    
    # -------------------------
    # 2.3 Attack Signatures (Bar Chart)
    # -------------------------
    st.markdown("#### Attack Signatures Detected")
    
    # Find signature columns
    signature_cols = [col for col in result_df.columns if col.startswith("sig_")]
    
    if signature_cols:
        sig_counts = {}
        for col in signature_cols:
            count = result_df[col].sum() if col in result_df.columns else 0
            if count > 0:
                sig_name = col.replace("sig_", "").replace("_", " ").title()
                sig_counts[sig_name] = count
        
        if sig_counts:
            sig_df = pd.DataFrame(list(sig_counts.items()), columns=["Attack Type", "Count"])
            sig_df = sig_df.sort_values("Count", ascending=True)
            
            fig_bar = px.bar(
                sig_df,
                x="Count",
                y="Attack Type",
                orientation="h",
                color="Count",
                color_continuous_scale="Reds"
            )
            fig_bar.update_layout(height=max(300, len(sig_counts) * 40), showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No attack signatures detected in this dataset")
    else:
        st.info("No attack signature columns found in results")
    
    # -------------------------
    # 2.4 Top Attacking IPs (if IP column exists)
    # -------------------------
    ip_columns = [col for col in result_df.columns if "ip" in col.lower() or col == "client"]
    
    if ip_columns:
        st.markdown("#### Top Attacking IPs")
        ip_col = ip_columns[0]
        
        # Filter for anomalies only
        anomalous_ips = result_df[
            (result_df.get("RF_Prediction", 0) == 1) | (result_df.get("ISO_Prediction", 0) == 1)
        ]
        
        if len(anomalous_ips) > 0:
            ip_counts = anomalous_ips[ip_col].value_counts().head(10)
            
            fig_ip = px.bar(
                x=ip_counts.values,
                y=ip_counts.index,
                orientation="h",
                labels={"x": "Anomalous Requests", "y": "IP Address"},
                color=ip_counts.values,
                color_continuous_scale="OrRd"
            )
            fig_ip.update_layout(height=max(300, len(ip_counts) * 40), showlegend=False)
            st.plotly_chart(fig_ip, use_container_width=True)
        else:
            st.info("No anomalous IPs detected")
    
    # -------------------------
    # 2.5 Model Agreement Analysis
    # -------------------------
    st.markdown("#### Model Agreement Analysis")
    
    if "RF_Prediction" in result_df.columns and "ISO_Prediction" in result_df.columns:
        both_normal = len(result_df[(result_df["RF_Prediction"] == 0) & (result_df["ISO_Prediction"] == 0)])
        both_anomaly = len(result_df[(result_df["RF_Prediction"] == 1) & (result_df["ISO_Prediction"] == 1)])
        rf_only = len(result_df[(result_df["RF_Prediction"] == 1) & (result_df["ISO_Prediction"] == 0)])
        iso_only = len(result_df[(result_df["RF_Prediction"] == 0) & (result_df["ISO_Prediction"] == 1)])
        
        agreement_data = {
            "Category": ["Both Normal", "Both Anomaly", "RF Only", "ISO Only"],
            "Count": [both_normal, both_anomaly, rf_only, iso_only],
            "Color": ["#2ecc71", "#e74c3c", "#f39c12", "#9b59b6"]
        }
        
        fig_agreement = px.bar(
            agreement_data,
            x="Category",
            y="Count",
            color="Category",
            color_discrete_map={
                "Both Normal": "#2ecc71",
                "Both Anomaly": "#e74c3c",
                "RF Only": "#f39c12",
                "ISO Only": "#9b59b6"
            }
        )
        fig_agreement.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig_agreement, use_container_width=True)
    
    # -------------------------
    # 3. ENHANCED RESULTS TABLE
    # -------------------------
    st.markdown("---")
    st.subheader("📋 Detailed Results")
    
    # Color-code based on threat score
    def highlight_threat(row):
        if "threat_score" not in row:
            return [""] * len(row)
        
        threat = row.get("threat_score", 0)
        if threat >= 70:
            color = "background-color: #ffcccc"  # Red (Critical)
        elif threat >= 50:
            color = "background-color: #ffe6cc"  # Orange (High)
        elif threat >= 30:
            color = "background-color: #ffffcc"  # Yellow (Medium)
        else:
            color = "background-color: #ccffcc"  # Green (Low)
        
        return [color] * len(row)
    
    # Check dataset size - only apply styling for reasonably sized datasets
    total_cells = len(result_df) * len(result_df.columns)
    max_styleable_cells = 200000  # Conservative limit below pandas default
    
    if total_cells <= max_styleable_cells:
        # Apply styling for smaller datasets
        styled_df = result_df.style.apply(highlight_threat, axis=1)
        st.dataframe(styled_df, use_container_width=True, height=400)
    else:
        # For large datasets, display without styling to avoid rendering limits
        st.info(f"ℹ️ Dataset is large ({total_cells:,} cells). Displaying without color coding for performance.")
        st.dataframe(result_df, use_container_width=True, height=400)
    
    # -------------------------
    # 4. DOWNLOAD BUTTON
    # -------------------------
    csv = result_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Results as CSV",
        data=csv,
        file_name="anomaly_detection_results.csv",
        mime="text/csv"
    )



# -------------------------
# Main logic
# -------------------------
if run_btn and uploaded_file:
    if not api_key:
        st.error("❌ You must enter API key before running.")
        st.stop()

    ext = uploaded_file.name.split(".")[-1].lower()

    st.info(f"📄 Processing file: **{uploaded_file.name}**")

    # =====================================================
    # CASE 1 : CSV FILE
    # =====================================================
    if ext == "csv":
        df = pd.read_csv(uploaded_file)
        st.write("### Preview of CSV")
        st.dataframe(df.head())

        st.write("⏳ Sending CSV to API...")

        pred = call_api_csv(df)
        if pred:
            st.success("Prediction complete!")
            result_df = pd.DataFrame(pred)
            display_visualizations(result_df)

    # =====================================================
    # CASE 2 : LOG / TXT FILE
    # =====================================================
    elif ext in ["log", "txt"]:
        text = uploaded_file.read().decode("utf-8", errors="ignore")
        lines = text.splitlines()

        st.write(f"📑 Found **{len(lines)}** log entries")

        st.write("⏳ Parsing log lines via API /parse-log ...")
        parsed = parse_log_lines(lines)

        if parsed:
            st.success("Logs parsed successfully!")
            df_logs = pd.DataFrame(parsed)
            st.dataframe(df_logs.head())

            st.write("⏳ Running anomaly detection on parsed logs...")
            preds = call_api_json(parsed)

            if preds:
                result_df = pd.DataFrame(preds)
                st.success("Prediction complete!")
                display_visualizations(result_df)

    # =====================================================
    # CASE 3 : JSON FILE
    # =====================================================
    elif ext == "json":
        data = json.load(uploaded_file)
        if isinstance(data, dict):
            records = data.get("logs", [])
        else:
            records = data

        st.write("⏳ Sending JSON logs to API...")
        preds = call_api_json(records)

        if preds:
            st.success("Prediction complete!")
            result_df = pd.DataFrame(preds)
            display_visualizations(result_df)

    else:
        st.error("Unsupported file type.")
