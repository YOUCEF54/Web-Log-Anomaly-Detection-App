"""
api/live.py
Simple WebSocket emitter using Flask-SocketIO.
This server can broadcast log events under event name 'log_event'.
A separate replay script (scripts/attack_replay.py) can connect and emit events.
Run: python api/live.py
"""

from flask import Flask
from flask_socketio import SocketIO, emit
import eventlet
import json
import time
import os

eventlet.monkey_patch()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

@socketio.on('connect')
def on_connect():
    print("Client connected")
    emit('server_info', {'msg': 'connected'})

@socketio.on('disconnect')
def on_disconnect():
    print("Client disconnected")

# Optional endpoint: broadcast a manual message (curl or requests can post to this)
@app.route("/broadcast", methods=["POST"])
def broadcast():
    # for quick tests you can post a JSON body and it will be broadcast
    from flask import request
    data = request.get_json(force=True)
    socketio.emit('log_event', data)
    return {"status": "ok", "sent": True}, 200


if __name__ == "__main__":
    print("Starting SocketIO server on 0.0.0.0:6000")
    socketio.run(app, host="0.0.0.0", port=6000)
