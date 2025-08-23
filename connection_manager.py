from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # 存储WebSocket连接
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str, device_id: str):
        await websocket.accept()
        key = f"{user_id}_{device_id}"
        self.active_connections[key] = websocket

    def disconnect(self, user_id: str, device_id: str):
        key = f"{user_id}_{device_id}"
        if key in self.active_connections:
            del self.active_connections[key]

    async def send_personal_message(self, message: str, user_id: str, device_id: str):
        key = f"{user_id}_{device_id}"
        if key in self.active_connections:
            await self.active_connections[key].send_text(message)

    async def broadcast(self, message: str, user_id: str, exclude_device: str = None):
        for key, connection in self.active_connections.items():
            if key.startswith(f"{user_id}_") and (exclude_device is None or not key.endswith(exclude_device)):
                await connection.send_text(message)
