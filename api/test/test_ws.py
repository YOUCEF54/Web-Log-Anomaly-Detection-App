import websocket

ws = websocket.WebSocket()
ws.connect("ws://localhost:6789")
print("Connected!")
while True:
    print(ws.recv())
