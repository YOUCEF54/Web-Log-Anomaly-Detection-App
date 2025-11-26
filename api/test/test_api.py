# test_api.py
"""
Simple integration tests for the API endpoints.
Run: python test_api.py
"""
import requests
import json
import os

API = "http://127.0.0.1:5000"
API_KEY = "weblogs-detection-2025"

headers = {"x-api-key": API_KEY}

def test_health():
    r = requests.get(f"{API}/health", headers=headers)
    print("[TEST] /health", r.status_code, r.json())

def test_predict_json():
    payload = {"method":"GET", "url":"/search.php?q=test", "user_agent":"Mozilla/5.0", "body":""}
    r = requests.post(f"{API}/predict-json", json=payload, headers=headers)
    print("[TEST] /predict-json", r.status_code, r.text[:100])

def test_predict_csv():
    path = os.path.join("data", "csic_database.csv")
    if not os.path.exists(path):
        print("❌ CSV not found:", path)
        return
    with open(path, "rb") as f:
        files = {"file": ("csic_database.csv", f)}
        r = requests.post(f"{API}/predict-csv", files=files, headers=headers)
        print("[TEST] /predict-csv", r.status_code, (len(r.json().get("prediction", [])) if r.status_code==200 else r.text[:200]))

def test_predict_log():
    path = os.path.join("data", "samples", "sample_access.log")
    if not os.path.exists(path):
        print("❌ log not found:", path)
        return
    with open(path, "rb") as f:
        files = {"file": ("sample_access.log", f)}
        r = requests.post(f"{API}/predict-log", files=files, headers=headers)
        print("[TEST] /predict-log", r.status_code, (len(r.json().get("prediction", [])) if r.status_code==200 else r.text[:200]))

if __name__ == "__main__":
    print("🚀 Running API Integration Tests...")
    test_health()
    test_predict_json()
    test_predict_csv()
    test_predict_log()
    print("✨ Tests Completed.")
