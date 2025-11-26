# ws_server.py
"""
Simple replay WebSocket server: streams lines from a log file as JSON messages
Usage:
    python ws_server.py --host 0.0.0.0 --port 6789 --file data/samples/sample_access.log --speed 0.3
"""
import argparse
import asyncio
import json
import websockets
import os
import time

async def handler(websocket, path, lines, delay):
    print(f"Client connected: {websocket.remote_address}")
    try:
        for line in lines:
            payload = {"log": line}
            await websocket.send(json.dumps(payload))
            await asyncio.sleep(delay)
    except websockets.ConnectionClosed:
        print("Client disconnected")
    except Exception as e:
        print("WS handler error:", e)

async def main_async(host, port, file, speed):
    if not os.path.exists(file):
        raise FileNotFoundError(file)
    with open(file, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.read().splitlines()
    async def _handler(ws, path):
        await handler(ws, path, lines, speed)
    print(f"Starting replay WS server on ws://{host}:{port}")
    async with websockets.serve(_handler, host, port):
        await asyncio.Future()  # run forever

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", default=6789, type=int)
    parser.add_argument("--file", required=True)
    parser.add_argument("--speed", default=0.3, type=float)
    args = parser.parse_args()
    try:
        asyncio.run(main_async(args.host, args.port, args.file, args.speed))
    except KeyboardInterrupt:
        print("Server stopped")
    except Exception as e:
        print("WS server error:", e)

if __name__ == "__main__":
    main()
