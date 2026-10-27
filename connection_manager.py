import asyncio
import json
import time
from dataclasses import dataclass

from fastapi import WebSocket

import log
from config import settings


@dataclass
class PendingMessage:
    """等待客户端 ACK 的消息"""
    message_id: str
    user_id: str
    device_id: str
    payload: str          # 已序列化的 JSON 字符串
    last_sent_at: float   # 最近一次发送时间（time.monotonic）
    retries: int = 0


class ConnectionManager:
    def __init__(self):
        # 存储WebSocket连接
        self.active_connections: dict[str, WebSocket] = {}
        # 等待 ACK 的消息：message_id -> PendingMessage
        self.pending: dict[str, PendingMessage] = {}
        self._retry_task: asyncio.Task | None = None

    @staticmethod
    def _key(user_id: str, device_id: str) -> str:
        return f"{user_id}_{device_id}"

    async def connect(self, websocket: WebSocket, user_id: str, device_id: str):
        await websocket.accept()
        key = self._key(user_id, device_id)
        self.active_connections[key] = websocket

    def disconnect(self, user_id: str, device_id: str):
        key = self._key(user_id, device_id)
        if key in self.active_connections:
            del self.active_connections[key]

    async def send_personal_message(self, message: str, user_id: str, device_id: str):
        key = self._key(user_id, device_id)
        if key in self.active_connections:
            await self.active_connections[key].send_text(message)

    async def broadcast(self, message: str, user_id: str, exclude_device: str = None):
        for key, connection in self.active_connections.items():
            if key.startswith(f"{user_id}_") and (exclude_device is None or not key.endswith(exclude_device)):
                await connection.send_text(message)

    async def send_with_ack(self, user_id: str, device_id: str, payload: str, message_id: str) -> bool:
        """发送一条要求 ACK 的消息并登记到待确认队列；返回 False 表示设备离线，未发送。"""
        key = self._key(user_id, device_id)
        if key not in self.active_connections:
            log.warning(f'send_with_ack: device {device_id} offline, drop message {message_id}')
            return False

        self.pending[message_id] = PendingMessage(
            message_id=message_id, user_id=user_id, device_id=device_id,
            payload=payload, last_sent_at=time.monotonic(),
        )
        try:
            await self.active_connections[key].send_text(payload)
        except Exception:
            self.pending.pop(message_id, None)
            log.error(f'send_text failed for {message_id} to device {device_id}', exc_info=True)
            return False
        return True

    def handle_client_message(self, user_id: str, device_id: str, text: str):
        """解析客户端上行消息，目前只处理 ack（心跳由上层决定）。"""
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            log.debug(f'ignore non-json message from device {device_id}')
            return
        if data.get('action') == 'ack':
            self._handle_ack(user_id, device_id, data.get('message_id', ''))

    def _handle_ack(self, user_id: str, device_id: str, message_id: str):
        pending = self.pending.get(message_id)
        if not pending:
            return  # 重复/过期的 ack，忽略
        if pending.user_id != user_id or pending.device_id != device_id:
            log.warning(f'ack mismatch for {message_id}, from {user_id}/{device_id}')
            return
        del self.pending[message_id]
        log.debug(f'message {message_id} acked by {device_id}')

    def start_retry_loop(self):
        """启动后台重试任务（幂等，重复调用不产生多个任务）。"""
        if self._retry_task is None or self._retry_task.done():
            self._retry_task = asyncio.create_task(self._retry_loop())

    async def _retry_loop(self):
        log.info('connection manager retry loop started')
        while True:
            await asyncio.sleep(1)  # 每秒扫描一次
            now = time.monotonic()
            for message_id, pending in list(self.pending.items()):
                if now - pending.last_sent_at < settings.SYNC_ACK_TIMEOUT_SECONDS:
                    continue

                key = self._key(pending.user_id, pending.device_id)
                # 设备已离线 → 放弃（离线补发属于第二层，这里先留 TODO）
                if key not in self.active_connections:
                    log.warning(f'device {pending.device_id} offline, drop pending message {message_id}')
                    del self.pending[message_id]
                    continue

                # 超过最大重试次数 → 放弃
                if pending.retries >= settings.SYNC_MAX_RETRIES:
                    log.error(f'give up message {message_id} to device {pending.device_id} '
                              f'after {pending.retries} retries')
                    del self.pending[message_id]
                    continue

                pending.retries += 1
                pending.last_sent_at = now
                try:
                    await self.active_connections[key].send_text(pending.payload)
                    log.debug(f'retry #{pending.retries} message {message_id} to device {pending.device_id}')
                except Exception:
                    log.error(f'retry send failed for {message_id} to device {pending.device_id}', exc_info=True)
                    del self.pending[message_id]
