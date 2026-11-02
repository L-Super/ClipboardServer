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

# 安装可选依赖，test 目录使用
uv sync --extra test
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
│   └── script.js        # js脚本
├── uploads/             # 文件上传目录
└── pyproject.toml       # 项目配置
```

## Docker 部署

### 方式一：使用 docker-compose

```bash
# 生产环境：拉取 GHCR 镜像并启动
docker compose pull
docker compose up -d

# 查看日志
docker compose logs -f

# 停止
docker compose down
```

服务暴露端口：`8000`，若与宿主机端口冲突，可在 `docker-compose.yml` 中调整为 `宿主:容器` 映射，例如 `18000:8000`。

### 开发环境：本地构建镜像

```bash
docker compose -f docker-compose-dev.yml up -d --build
docker compose -f docker-compose-dev.yml watch
```

开发环境使用 `Dockerfile` 本地构建，并通过 Compose Watch 同步源码；生产环境使用 `docker-compose.yml` 直接运行 GHCR 镜像。

### 方式二：使用 Docker 直接构建运行

```bash
# 构建镜像
docker build -t clipboard-server:latest .

# 运行容器（绑定端口与数据卷）
docker run -d \
  --name clipboard-server \
  -p 8000:8000 \
  -e SECRET_KEY=please_change_me \
  -e TZ=Asia/Shanghai \
  -v %cd%/uploads:/app/uploads \
  -v %cd%/static:/app/static:ro \
  clipboard-server:latest
```

说明：
- 若在 Linux/macOS，将上面的 `%cd%` 替换为 `$(pwd)`。

### 方式三：拉取 Docker 镜像

```bash
docker pull ghcr.io/l-super/clipboardserver:latest
docker run -d --name clipboard-server \
  -p 8000:8000 \
  --env-file .env \
  -v "${PWD}/uploads:/app/uploads" \
  -v "${PWD}/logs:/app/logs" \
  ghcr.io/l-super/clipboardserver:latest
```

推送到 `main` 分支或创建 `v*.*.*` 标签后，GitHub Actions 会自动构建并发布镜像到 GitHub Container Registry（GHCR）。


## API 文档

访问以下地址查看完整的 API 文档：
- Swagger UI: http://localhost:8000/docs

## 配置说明

### 配置文件

项目使用 `config.py` 管理配置，通过环境变量或 `.env` 文件覆盖默认值。

### 主要配置项

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `DATABASE_URL` | 数据库连接字符串 | `sqlite:///clipboard.db` |
| `ACCESS_TOKEN_EXPIRE_DAYS` | Access Token 过期天数 | `60` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh Token 过期天数 | `30` |
| `LOG_LEVEL` | 日志级别 | `INFO` |

### 环境变量示例

创建 `.env` 文件：
```env
DATABASE_URL=sqlite:///clipboard.db
TZ=Asia/Shanghai
LOG_LEVEL=INFO
```

## 开发说明

### 技术栈

- **后端**：FastAPI
- **前端**：HTML5 + CSS3 + JavaScript
- **认证**：JWT (JSON Web Tokens)
- **实时通信**：WebSocket
- **数据库**：MySQL / SQLite

## 许可证

[MIT License](LICENSE)
