import asyncio
import websockets
import json
import requests
from jose import jwt

SECRET_KEY: str = "clipboard_key"
ALGORITHM: str = "HS256"


class ClipboardClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.access_token = None
        self.user_id = None
        self.device_id = None
        self.current_version = 0
        self.ws_connected = False

    def register(self, email, password):
        response = requests.post(f"{self.base_url}/auth/register", json={
            "email": email,
            "password": password,
        })
        data = response.json()
        print(data)

    def login(self, email, password, device_id, device_name, device_type):
        """用户登录并获取令牌"""
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={
                "email": email,
                "password": password,
                "device_id": device_id,
                "device_name": device_name,
                "device_type": device_type
            }
        )
        data = response.json()
        self.access_token = data["access_token"]

        # 解析令牌获取用户和设备ID
        payload = jwt.decode(self.access_token, SECRET_KEY, algorithms=[ALGORITHM])
        self.user_id = payload["sub"]
        self.device_id = payload["device_id"]
        print(f'login success. {self.user_id} {self.device_id} ')
        print(f'token: {self.access_token}')

    async def start_websocket(self):
        """启动WebSocket连接"""
        if not self.access_token:
            raise Exception("Not authenticated")

        ws_url = f"ws{self.base_url[4:]}/sync/notify?token={self.access_token}"

        async with websockets.connect(ws_url) as websocket:
            self.ws_connected = True
            print("WebSocket connected")

            # 发送初始化消息（当前版本）
            init_msg = json.dumps({
                "action": "init",
                "version": self.current_version
            })
            await websocket.send(init_msg)

            # 监听消息
            async for message in websocket:
                await self.handle_websocket_message(message)

    async def handle_websocket_message(self, message):
        """处理WebSocket消息"""
        try:
            web_message = json.loads(message)
            action = web_message.get("action")

            if action == "update":
                # 收到更新通知
                type = web_message.get("type")
                data = web_message.get("data")
                data_hash = web_message.get("data_hash")
                print(f"received websocket data. type: {type} data: {data} hash: {data_hash}")
                # latest_version = data["latest_version"]
                # new_items_count = data["new_items_count"]
                #
                # print(f"Received update: version={latest_version}, items={new_items_count}")

                # 触发同步操作
                # await self.sync_clipboard()

            elif action == "heartbeat":
                # 心跳检测
                print("Heartbeat received")

        except Exception as e:
            print(f"Error handling message: {e}")

    async def sync_clipboard(self):
        """执行剪贴板同步"""
        try:
            response = requests.get(
                f"{self.base_url}/clipboard/sync",
                params={"last_version": self.current_version},
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            data = response.json()

            # 处理同步数据
            for item in data["items"]:
                # 更新本地剪贴板
                self.update_local_clipboard(item)

                # 更新当前版本
                self.current_version = max(self.current_version, item["version"])

            print(f"Sync completed. New version: {self.current_version}")

        except Exception as e:
            print(f"Sync error: {e}")

    def update_local_clipboard(self, item):
        """更新本地剪贴板内容"""
        # 注意：避免循环触发
        if item["source_device"] != self.device_id:
            print(f"Updating clipboard with: {item['data'][:50]}...")

            # 实际应用中调用系统剪贴板API
            # pyperclip.copy(item["data"])

            # 更新GUI显示等

    def upload_clipboard(self, content, content_type="text"):
        """上传本地剪贴板内容"""
        try:
            response = requests.post(
                f"{self.base_url}/clipboard",
                json={
                    "type": content_type,
                    "data": content,
                    "meta": {
                        "source": "Python Client"
                    }
                },
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            if response.status_code != 200:
                raise Exception(response.text)
            data = response.json()
            # self.current_version = data["version"]
            print(f"Upload successful. {data}")

        except Exception as e:
            print(f"Upload error: {e}")

    def upload(self, content_type: str, content: str | None = None, file=None):
        """

        :param content_type: text,image,file
        :param content:
        :param file:
        :return:
        """
        try:
            if file:
                print('uploading file...')
                file = {'file': open(file, 'rb')}
                response = requests.post(
                    f"{self.base_url}/clipboard",
                    data={
                        "type": content_type
                    },
                    files=file,
                    headers={"Authorization": f"Bearer {self.access_token}"}
                )
            else:
                print('uploading text...')
                response = requests.post(
                    f"{self.base_url}/clipboard",
                    data={
                        "type": content_type,
                        "data": content,
                    },
                    headers={"Authorization": f"Bearer {self.access_token}"}
                )

            if response.status_code != 200:
                raise Exception(response.text)
            data = response.json()

            print(f"Upload successful. {data}")

        except Exception as e:
            print(f"Upload error: {e}")

    def run(self):
        """主循环"""
        asyncio.run(self.start_websocket())


# 使用示例
if __name__ == "__main__":
    client = ClipboardClient("http://localhost:8000")
    # client.register("user@example.com", "string")
    client.login("user@example.com", "string", "new_device_id", "My Laptop", "windows")

    # 启动WebSocket监听
    # client.run()
    client.upload(content='hello world', content_type='text')

    #TODO:上传文件失败，需要排查
    client.upload(file='test.jpg', content_type='image')
