from fastapi import WebSocket


class ConnectionManager:

    def __init__(self):
        self.active_connections = {}

    async def connect(self, chat_id: str, websocket: WebSocket):

        await websocket.accept()

        self.active_connections[chat_id] = websocket

        print(f"WebSocket connected: {chat_id}")

    def disconnect(self, chat_id: str):

        self.active_connections.pop(chat_id, None)

        print(f"WebSocket disconnected: {chat_id}")

    async def send_event(
        self,
        chat_id: str,
        event: dict
    ):

        websocket = self.active_connections.get(chat_id)

        if websocket:
            await websocket.send_json(event)


manager = ConnectionManager()