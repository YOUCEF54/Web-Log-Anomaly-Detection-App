import websocket
import json
import time
import pandas as pd

WS_URL = "ws://127.0.0.1:5001/stream"
API_KEY = "your_api_key_here"

def on_open(ws):
    print("🔗 WebSocket connection opened.")
    ws.send(json.dumps({"api_key": API_KEY}))

def on_message(ws, message):
    data = json.loads(message)
    print("📥 Received:", data)

def on_error(ws, error):
    print("❌ Error:", error)

def on_close(ws, a, b):
    print("🔌 WebSocket closed.")

def run_client():
    ws = websocket.WebSocketApp(
        WS_URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )
    ws.run_forever()

if __name__ == "__main__":
    run_client()
