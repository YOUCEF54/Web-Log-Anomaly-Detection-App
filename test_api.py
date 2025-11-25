import requests
import json

API_KEY = "weblogs-detection-2025"
BASE_URL = "http://127.0.0.1:5000"


# ---------------------------------------------
# Test 1 : Health-check
# ---------------------------------------------
def test_health():
    print("\n[TEST] /health")
    url = f"{BASE_URL}/health"
    r = requests.get(url)
    print("Status:", r.status_code)
    print("Response:", r.json())


# ---------------------------------------------
# Test 2 : JSON Prediction
# ---------------------------------------------
def test_json_predict():
    print("\n[TEST] /predict-json")

    url = f"{BASE_URL}/predict-json"

    sample_log = {
        "ip": "127.0.0.1",
        "url": "/search.php?q=test",
        "method": "GET",
        "user_agent": "Mozilla/5.0",
        "body": ""
    }

    headers = {"x-api-key": API_KEY}

    r = requests.post(url, json=sample_log, headers=headers)

    print("Status:", r.status_code)
    print("Response:", r.json())


# ---------------------------------------------
# Test 3 : CSV Prediction
# ---------------------------------------------
def test_csv_predict():
    print("\n[TEST] /predict-csv")

    url = f"{BASE_URL}/predict-csv"
    headers = {"x-api-key": API_KEY}

    FILE_PATH = r"data/csic_database.csv"  # Change with your file

    try:
        files = {"file": open(FILE_PATH, "rb")}
    except FileNotFoundError:
        print("❌ CSV file not found:", FILE_PATH)
        return

    r = requests.post(url, files=files, headers=headers)

    print("Status:", r.status_code)

    try:
        data = r.json()
        print("First row:", data["prediction"][0])
    except Exception:
        print("Raw Response:", r.text)


# ---------------------------------------------
# Run all tests
# ---------------------------------------------
if __name__ == "__main__":
    print("\n🚀 Running API Integration Tests...")

    test_health()
    test_json_predict()
    test_csv_predict()

    print("\n✨ Tests Completed.")
