import streamlit as st
import base64
import os

st.set_page_config(
    page_title="About • Web Log Anomaly Detection",
    page_icon="ℹ️",
)

# --- Load Logo ---
logo_path = "static/logo.png"
encoded_logo = None
if os.path.exists(logo_path):
    encoded_logo = base64.b64encode(open(logo_path, "rb").read()).decode()

# --- CSS Styling ---
st.markdown("""
<style>
    body {
        background-color: #f5f7fb;
    }

    .about-container {
        background-color: white;
        padding: 25px 35px;
        border-radius: 12px;
        box-shadow: 0 3px 10px rgba(0,0,0,0.05);
        margin-top: 20px;
    }

    .title-about {
        font-size: 32px;
        font-weight: 800;
        color: #1e293b;
        margin-bottom: 10px;
        display:flex;
        align-items:center;
        gap:15px;
    }

    .section-title {
        font-size: 22px;
        margin-top: 30px;
        font-weight: bold;
        color: #0f172a;
    }

    p {
        font-size: 16px;
        color: #334155;
        line-height: 1.55;
    }

    .team-card {
        background:#f8fafc;
        padding:15px;
        border-radius:10px;
        margin-bottom:10px;
        border-left:4px solid #3b82f6;
    }

</style>
""", unsafe_allow_html=True)

# --- Header with Logo ---
st.markdown('<div class="about-container">', unsafe_allow_html=True)

if encoded_logo:
    st.markdown(
        f"""
        <div class="title-about">
            <img src="data:image/png;base64,{encoded_logo}" width="70"/>
            About the Project
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.title("ℹ️ About the Project")

st.write("""
This project focuses on **detecting anomalies within HTTP web logs** using a combination of  
**supervised (RandomForest)** and **unsupervised (IsolationForest)** machine learning models.

The system aims to **identify malicious requests**, suspicious behaviours,  
and potential intrusion attempts in real-time or via offline batch analysis.
""")

# ------------------------------------------
# OBJECTIVES
# ------------------------------------------

st.markdown("<div class='section-title'>🎯 Project Objectives</div>", unsafe_allow_html=True)

st.write("""
- Build a **robust machine learning pipeline** capable of detecting anomalies in web server logs.  
- Provide a **Flask API** to expose prediction services.  
- Develop a **Streamlit dashboard** for monitoring, visualization, and reporting.  
- Ensure compatibility with both **CSV datasets** and **raw Apache access logs**.  
- Demonstrate real-world value through **threat simulation** and anomaly correlation.  
""")

# ------------------------------------------
# DATASET
# ------------------------------------------

st.markdown("<div class='section-title'>📚 Dataset Used</div>", unsafe_allow_html=True)

st.write("""
We use the **CSIC 2010 HTTP Dataset**, a standard benchmark for web intrusion detection.

It contains:
- Normal traffic  
- SQL injections  
- XSS attacks  
- Path traversal  
- Broken authentication attempts  
- Command injections  
""")

# ------------------------------------------
# METHODOLOGY
# ------------------------------------------

st.markdown("<div class='section-title'>🧠 Machine Learning Pipeline</div>", unsafe_allow_html=True)

st.write("""
Our approach combines:
- **RandomForestClassifier** → Supervised anomaly detection (labelled data)  
- **IsolationForest** → Unsupervised detection for unseen threats  
- **Feature extraction** from HTTP logs (URL, method, headers, length, user agent...)  
- **Dual-model verification** to reduce false positives  
""")

# ------------------------------------------
# SYSTEM ARCHITECTURE
# ------------------------------------------

st.markdown("<div class='section-title'>🏗️ System Architecture</div>", unsafe_allow_html=True)

st.write("""
The project consists of:

1. **Data Preprocessing & Feature Engineering**  
2. **Jupyter Notebooks** for model training  
3. **Model serialization (.pkl)**  
4. **Flask API** exposing `/predict-csv`, `/predict-log`, `/predict-json`  
5. **Streamlit Dashboard** for visualization & real-time monitoring  
""")

# ------------------------------------------
# TEAM
# ------------------------------------------

st.markdown("<div class='section-title'>👥 Project Team</div>", unsafe_allow_html=True)

st.markdown("""
<div class="team-card">
    <b>Imane Barakat</b> — Machine Learning & System Integration
</div>

<div class="team-card">
    <b>[Naoual Elhilali]</b> — Backend & Flask API
</div>

<div class="team-card">
    <b>[Youssef El Omari]</b> — Dashboard & UX
</div>

<div class="team-card">
    <b>[Soufiane Chajjaoui]</b> — Dataset, Testing & Documentation
</div>
""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)