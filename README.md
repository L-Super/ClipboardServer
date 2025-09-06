# 剪贴板同步系统

一个基于 FastAPI 的跨设备剪贴板同步服务，支持实时同步和用户认证。

## 功能特性

- 🔐 **用户认证系统**：支持用户注册和登录
- 📱 **多设备支持**：支持 Windows、macOS、Linux、iOS、Android、Web 等设备
- 🔄 **实时同步**：基于 WebSocket 的实时剪贴板同步
- 🌐 **Web 界面**：现代化的登录注册界面和仪表板
- 🔒 **JWT 认证**：安全的 token 认证机制
- 📊 **设备管理**：查看和管理已连接的设备
- 📝 **API 文档**：自动生成的 Swagger API 文档

## 快速开始

### 1. 安装依赖

```bash
# 使用 uv 安装依赖
uv sync
```

### 2. 启动服务器

```bash
# 启动开发服务器
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 后台启动
nohup uv run uvicorn main:app --host 0.0.0.0 --port 8000 &
```

### 3. 访问 Web 界面

打开浏览器访问：http://localhost:8000

## 项目结构

```
clipboard_server/
├── main.py              # FastAPI 主应用
├── auth.py              # 认证相关功能
├── models.py            # 数据库模型
├── schemas.py           # Pydantic 数据模型
├── crud.py              # 数据库 CRUD 操作
├── database.py          # 数据库配置
├── connection_manager.py # WebSocket 连接管理
├── config.py            # 配置文件
├── static/              # 静态文件
│   ├── index.html       # 登录注册页面
│   ├── dashboard.html   # 仪表板页面
│   ├── style.css        # 样式文件
│   └── script.js        # 客户端脚本
├── uploads/             # 文件上传目录
├── clipboard.db         # SQLite 数据库
├── pyproject.toml       # 项目配置
└── README.md           # 项目说明
```

## API 接口

### 认证接口

- `POST /auth/register` - 用户注册
- `POST /auth/login` - 用户登录

### 剪贴板接口

- `POST /clipboard` - 上传剪贴板内容
- `GET /clipboard` - 获取剪贴板内容
- `GET /clipboard/history` - 获取剪贴板历史

### 设备管理

- `GET /devices` - 获取用户设备列表
- `DELETE /devices/{device_id}` - 删除设备

### WebSocket

- `ws://localhost:8000/sync/notify` - 实时同步通知

## 使用方法

### 1. 注册新用户

访问 http://localhost:8000，点击"立即注册"，填写邮箱和密码。

### 2. 登录

使用注册的邮箱和密码登录，同时需要提供设备信息：
- 设备类型（选择您的设备类型）
- 设备名称（可自定义或自动生成）
- 设备ID（基于浏览器指纹自动生成，无需手动输入）

### 3. 使用剪贴板同步

登录成功后，系统会自动跳转到仪表板页面，显示：
- 用户信息
- 设备信息
- 连接状态
- API 接口信息

### 4. API 文档

访问 http://localhost:8000/docs 查看完整的 API 文档。

### 5. 设备指纹测试

访问 http://localhost:8000/test-fingerprint 查看和测试设备指纹生成功能。

## 开发说明

### 技术栈

- **后端**：FastAPI + SQLAlchemy + SQLite
- **前端**：HTML5 + CSS3 + JavaScript
- **认证**：JWT (JSON Web Tokens)
- **实时通信**：WebSocket
- **数据库**：SQLite

### 数据库模型

- **User**：用户信息
- **Device**：设备信息
- **ClipboardItem**：剪贴板内容
- **ClipboardHistory**：剪贴板历史

### 安全特性

- 密码哈希存储
- JWT token 认证
- 设备级别的访问控制
- 输入验证和清理
- 基于浏览器指纹的设备识别

## 许可证

MIT License
