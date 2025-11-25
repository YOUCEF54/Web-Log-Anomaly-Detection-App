"""
scripts/attack_replay.py
Replay rows from data/csic_database.csv (or sample_access.log) to:
 - Flask API (/predict-json)  OR
 - WebSocket server (api/live.py) as 'log_event'
Usage examples:
  python scripts/attack_replay.py --mode api --file ../data/csic_database.csv --rate 10
  python scripts/attack_replay.py --mode ws --file ../data/sample_access.log --rate 2
"""

import argparse
import time
import json
import os
import pandas as pd
import requests

def replay_api(csv_path, endpoint="http://127.0.0.1:5000/predict-json", rate_per_min=60):
    df = pd.read_csv(csv_path)
    total = len(df)
    interval = 60.0 / max(rate_per_min, 1)
    print(f"Replaying {total} rows → {endpoint} at {rate_per_min} events/min (interval={interval:.2f}s)")

    for i, row in df.iterrows():
        payload = row.dropna().to_dict()
        try:
            r = requests.post(endpoint, json=payload, timeout=5)
            print(f"[{i+1}/{total}] status={r.status_code}")
        except Exception as e:
            print("API send error:", e)
        time.sleep(interval)


def replay_ws_csv(csv_path, ws_url="ws://127.0.0.1:6000/socket.io/?EIO=4&transport=websocket", rate_per_min=60):
    # lazy import to avoid dependency when not used
    from websocket import create_connection
    df = pd.read_csv(csv_path)
    interval = 60.0 / max(rate_per_min, 1)
    print(f"Replaying {len(df)} rows to WS {ws_url} at {rate_per_min} events/min")

    ws = create_connection(ws_url)
    try:
        for i, row in df.iterrows():
            payload = row.dropna().to_dict()
            # socket.io transport framing is complex; many setups accept a raw JSON message
            # we send a plain JSON string, server should be prepared to parse it on 'log_event'
            ws.send(json.dumps(payload))
            print(f"[{i+1}/{len(df)}] sent")
            time.sleep(interval)
    finally:
        ws.close()


def replay_logfile(logfile_path, endpoint=None, rate_per_min=60, mode="api"):
    # If logfile (apache) — parse into simple dicts (very simple parser)
    rows = []
    with open(logfile_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            # minimal parsing: keep the whole line as 'raw'
            rows.append({"raw": line.strip()})

    interval = 60.0 / max(rate_per_min, 1)
    print(f"Replaying {len(rows)} logfile lines at {rate_per_min} events/min to mode={mode}")

    if mode == "api" and endpoint:
        for i, r in enumerate(rows):
            try:
                requests.post(endpoint, json=r, timeout=5)
            except Exception as e:
                print("API error", e)
            time.sleep(interval)
    else:
        print("WS mode for raw log lines is not implemented in this simple script.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["api", "ws"], default="api")
    p.add_argument("--file", required=True)
    p.add_argument("--rate", type=int, default=60, help="events per minute")
    p.add_argument("--endpoint", default="http://127.0.0.1:5000/predict-json")
    p.add_argument("--ws-url", default="ws://127.0.0.1:6000/socket.io/?EIO=4&transport=websocket")
    args = p.parse_args()

    if not os.path.exists(args.file):
        print("File not found:", args.file)
        raise SystemExit(1)

    if args.file.endswith(".csv"):
        if args.mode == "api":
            replay_api(args.file, endpoint=args.endpoint, rate_per_min=args.rate)
        else:
            replay_ws_csv(args.file, ws_url=args.ws_url, rate_per_min=args.rate)
    else:
        replay_logfile(args.file, endpoint=args.endpoint, rate_per_min=args.rate, mode=args.mode)
