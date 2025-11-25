# 🛡️ Web Log Anomaly Detection

A comprehensive web application for detecting anomalies and security threats in web server logs using Machine Learning. The system combines **Random Forest** and **Isolation Forest** models with attack signature detection and threat scoring to identify potential security risks in real-time.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-2.0+-green.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.0+-red.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 📋 Table of Contents

- [Features](#-features)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Visualizations](#-visualizations)
- [Machine Learning Models](#-machine-learning-models)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

### 🔍 Anomaly Detection
- **Dual Model Approach**: Random Forest (RF) and Isolation Forest (ISO) for robust detection
- **Attack Signature Recognition**: Identifies SQL injection, XSS, path traversal, and more
- **Threat Scoring**: Automatically calculates risk scores (0-100) for each request
- **Multiple Format Support**: CSV, Apache logs, JSON, and plain text files

### 📊 Interactive Dashboard
- **Real-time Visualizations**: Interactive charts with Plotly
  - Anomaly distribution pie chart
  - Threat score histogram
  - Attack signatures bar chart
  - Top attacking IPs analysis
  - Model agreement comparison
- **Summary Metrics**: At-a-glance KPIs (total requests, anomalies %, avg/max threat scores)
- **Color-Coded Results**: Threat-level-based color coding (🔴 Critical, 🟠 High, 🟡 Medium, 🟢 Low)
- **Export Functionality**: One-click CSV download

### 🚀 REST API
- **Flask Backend**: Scalable API with authentication
- **Multiple Endpoints**: JSON, CSV, and log file processing
- **API Key Authentication**: Secure access control
- **CORS Enabled**: Cross-origin resource sharing support

## 📁 Project Structure

```
WebLogAnomalyDetection/
├── api/                      # Flask API backend
│   ├── app.py               # Main API server
│   └── live.py              # Live streaming endpoint
├── app/                      # Streamlit frontend
│   ├── streamlit_app.py     # Main dashboard (enhanced with visualizations)
│   ├── 1_About.py           # About page
│   ├── model_insight.py     # Model insights page
│   ├── realtime_monitor.py  # Real-time monitoring
│   └── static/              # Static assets
├── data/                     # Sample datasets
│   ├── csic_database.csv    # CSIC dataset
│   └── sample_access.log    # Sample Apache logs
├── models/                   # Trained ML models
│   ├── rf_model.joblib      # Random Forest model
│   └── iso_model.joblib     # Isolation Forest model
├── notebooks/                # Jupyter notebooks for training
├── src/                      # Source code modules
│   ├── features.py          # Feature engineering
│   ├── attack_signatures.py # Signature detection
│   ├── threat_score.py      # Threat scoring logic
│   └── parse_logs.py        # Log parsing utilities
├── scripts/                  # Utility scripts
├── requirements.txt          # Python dependencies
└── README.md                # This file
```

## 🔧 Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/WebLogAnomalyDetection.git
cd WebLogAnomalyDetection
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies include:**
- `pandas`, `numpy` - Data processing
- `scikit-learn` - Machine learning models
- `flask`, `flask-cors`, `flask-socketio` - API backend
- `streamlit` - Web dashboard
- `plotly` - Interactive visualizations
- `matplotlib`, `seaborn` - Additional plotting
- `joblib` - Model serialization

## 🚀 Usage

The application consists of two components that run simultaneously:

### 1. Start the Flask API Backend

```bash
python api\app.py
```

The API will start on **http://127.0.0.1:5000**

**Default API Key:** `weblogs-detection-2025`

You can change this by setting the `WLAD_API_KEY` environment variable:

```bash
# Windows
set WLAD_API_KEY=your-custom-key
python api\app.py

# Linux/Mac
export WLAD_API_KEY=your-custom-key
python api/app.py
```

### 2. Start the Streamlit Dashboard

Open a **new terminal** window and run:

```bash
.\venv\Scripts\Activate.ps1  # Activate virtual environment
streamlit run app\streamlit_app.py
```

The dashboard will open in your browser at **http://localhost:8501**

### 3. Use the Application

1. Navigate to **http://localhost:8501** in your browser
2. Enter the API key in the sidebar: `weblogs-detection-2025`
3. Upload a log file (CSV, LOG, TXT, or JSON)
4. Click **"🚀 Run Prediction"**
5. View the results with interactive visualizations!

## 📡 API Documentation

### Base URL
```
http://127.0.0.1:5000
```

### Authentication
All endpoints (except `/health`) require an API key in the request header:

```
x-api-key: weblogs-detection-2025
```

### Endpoints

#### `GET /health`
Check API health status

**Response:**
```json
{
  "status": "OK",
  "models_loaded": true
}
```

#### `POST /predict-json`
Predict anomalies from JSON payload

**Request:**
```json
{
  "logs": [
    {
      "method": "GET",
      "url": "/admin",
      "status": 200,
      "body": "",
      "user_agent": "Mozilla/5.0"
    }
  ]
}
```

**Response:**
```json
{
  "status": "ok",
  "prediction": [
    {
      "method": "GET",
      "url": "/admin",
      "RF_Prediction": 1,
      "ISO_Prediction": 1,
      "threat_score": 75.5,
      "sig_sql_injection": 0,
      "sig_xss": 0
    }
  ]
}
```

#### `POST /predict-csv`
Upload CSV file for prediction

**Request:**
- Form data with `file` field containing CSV

**Response:** Same as `/predict-json`

#### `POST /predict-log`
Upload Apache log file for prediction

**Request:**
- Form data with `file` field containing log file

**Response:** Same as `/predict-json`

## 📊 Visualizations

The Streamlit dashboard provides comprehensive visual analysis:

### Summary Metrics
- **Total Requests**: Count of analyzed log entries
- **Anomalies Detected**: Count and percentage of flagged requests
- **Average Threat Score**: Mean threat level across all logs
- **Maximum Threat Score**: Highest threat with severity badge

### Interactive Charts

1. **Anomaly Distribution** (Pie Chart)
   - Visual breakdown of normal vs anomalous requests
   - Green for normal, red for anomalous

2. **Threat Score Distribution** (Histogram)
   - Shows distribution of threat scores across all logs
   - Helps identify concentration of threat levels

3. **Attack Signatures** (Bar Chart)
   - Count of each detected attack type
   - SQL injection, XSS, path traversal, etc.

4. **Top Attacking IPs** (Bar Chart)
   - Top 10 IP addresses with most anomalous requests
   - Helps identify malicious sources

5. **Model Agreement Analysis** (Bar Chart)
   - Compares RF vs ISO predictions
   - Shows consensus and disagreement between models

### Color-Coded Results Table

| Threat Score | Color | Severity |
|--------------|-------|----------|
| >= 70 | 🔴 Red | Critical |
| 50-69 | 🟠 Orange | High |
| 30-49 | 🟡 Yellow | Medium |
| < 30 | 🟢 Green | Low |

*Note: For large datasets (>200K cells), color coding is disabled for performance.*

## 🤖 Machine Learning Models

### Random Forest Classifier
- **Purpose**: Supervised anomaly detection
- **Features**: URL patterns, HTTP methods, status codes, payload characteristics
- **Output**: Binary classification (0=normal, 1=anomaly)

### Isolation Forest
- **Purpose**: Unsupervised anomaly detection
- **Features**: Same feature set as Random Forest
- **Output**: Binary classification (-1=anomaly, 1=normal)

### Feature Engineering
The system extracts the following features:
- URL length and entropy
- Payload length
- HTTP method (encoded)
- Status code patterns
- User agent characteristics
- Special character counts
- Attack signature patterns

### Attack Signatures
Detects the following attack types:
- SQL Injection (`' OR`, `UNION SELECT`, etc.)
- Cross-Site Scripting (XSS) (`<script>`, `javascript:`, etc.)
- Path Traversal (`../`, `..\\`)
- Command Injection (`; ls`, `| cat`, etc.)
- Null Byte Injection (`%00`)

### Threat Scoring
Combines multiple factors to calculate a threat score (0-100):
- Base score from anomaly predictions
- Bonus points for detected attack signatures
- Multipliers for high-risk patterns
- Adjusted by payload size and URL complexity

## 🧪 Testing

### Sample Data
Test files are provided in the `data/` directory:
- `csic_database.csv` - CSIC HTTP dataset
- `sample_access.log` - Apache access log format

### Running Tests

```bash
# Test API endpoints
python test_api.py

# Manual testing via dashboard
# 1. Start both servers
# 2. Upload data/csic_database.csv
# 3. Verify visualizations render correctly
```

## 🛠️ Development

### Training New Models

Use the Jupyter notebooks in `notebooks/` to retrain models:

```bash
jupyter notebook notebooks/
```

Notebooks include:
- Data preprocessing
- Feature engineering
- Model training and evaluation
- Model export to `models/` directory

### Adding New Attack Signatures

Edit `src/attack_signatures.py` and add patterns to the detection functions:

```python
def detect_new_attack(url, body, headers):
    patterns = [r'your_pattern_here']
    # Detection logic
    return 1 if detected else 0
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- CSIC HTTP Dataset for training data
- Streamlit for the amazing dashboard framework
- Plotly for interactive visualizations
- scikit-learn for machine learning models

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Built with ❤️ for security professionals and data scientists**
