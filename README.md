# Clipboard Sync System

[中文](README_CN.md)

A FastAPI-based cross-device clipboard synchronization service with real-time sync and user authentication.

## Features

- 🔐 **User Authentication**: User registration and login support
- 📱 **Multi-device Support**: Supports Windows, macOS, Linux, iOS, Android, Web devices
- 🔄 **Real-time Sync**: WebSocket-based real-time clipboard synchronization
- 🌐 **Web Interface**: Modern login/registration interface and dashboard
- 🔒 **JWT Authentication**: Secure token-based authentication mechanism
- 📊 **Device Management**: View and manage connected devices
- 📝 **API Documentation**: Auto-generated Swagger API documentation

## Quick Start

### 1. Install Dependencies

```bash
# Install dependencies using uv
uv sync

# Install optional dependencies for test directory
uv sync --extra test
```

### 2. Start Server

```bash
# Start development server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Start in background
nohup uv run uvicorn main:app --host 0.0.0.0 --port 8000 &
```

### 3. Access Web Interface

Open your browser and visit: http://localhost:8000

## Project Structure

```
clipboard_server/
├── main.py              # FastAPI main application
├── auth.py              # Authentication related functions
├── models.py            # Database models
├── schemas.py           # Pydantic data models
├── crud.py              # Database CRUD operations
├── database.py          # Database configuration
├── connection_manager.py # WebSocket connection management
├── config.py            # Configuration file
├── static/              # Static files
│   ├── index.html       # Login/registration page
│   ├── dashboard.html   # Dashboard page
│   ├── style.css        # Style file
│   └── script.js        # JavaScript script
├── uploads/             # File upload directory
└── pyproject.toml       # Project configuration
```

## Docker Deployment

### Method 1: Using docker-compose

```bash
# Production: pull the GHCR image and start
docker compose pull
docker compose up -d

# View logs
docker compose logs -f

# Stop
docker compose down
```

Service exposes port: `8000`. If it conflicts with host port, adjust the `host:container` mapping in `docker-compose.yml`, e.g., `18000:8000`.

### Development: Build Locally

```bash
docker compose -f docker-compose-dev.yml up -d --build
docker compose -f docker-compose-dev.yml watch
```

The development Compose file builds from the local `Dockerfile` and uses Compose Watch to sync source changes. The default Compose file runs the published GHCR image.

### Method 2: Direct Docker Build and Run

```bash
# Build image
docker build -t clipboard-server:latest .

# Run container (bind port and data volume)
docker run -d \
  --name clipboard-server \
  -p 8000:8000 \
  -e SECRET_KEY=please_change_me \
  -e TZ=Asia/Shanghai \
  -v %cd%/uploads:/app/uploads \
  -v %cd%/static:/app/static:ro \
  clipboard-server:latest
```

Notes:
- On Linux/macOS, replace `%cd%` with `$(pwd)`.

### Method 3: Pull Docker Image

```bash
docker pull ghcr.io/l-super/clipboardserver:latest
docker run -d --name clipboard-server \
  -p 8000:8000 \
  --env-file .env \
  -v "${PWD}/uploads:/app/uploads" \
  -v "${PWD}/logs:/app/logs" \
  ghcr.io/l-super/clipboardserver:latest
```

Pushing to the `main` branch or creating a `v*.*.*` tag automatically builds and publishes the image to GitHub Container Registry (GHCR).


## API Documentation

Visit the following URL to view complete API documentation:
- Swagger UI: http://localhost:8000/docs

## Configuration

### Configuration File

The project uses `config.py` to manage configuration, supporting override of default values through environment variables or `.env` file.

### Main Configuration Items

| Configuration | Description | Default Value |
|---------------|-------------|---------------|
| `DATABASE_URL` | Database connection string | `sqlite:///clipboard.db` |
| `ACCESS_TOKEN_EXPIRE_DAYS` | Access Token expiration days | `60` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh Token expiration days | `30` |
| `LOG_LEVEL` | Log level | `INFO` |

### Environment Variables Example

Create `.env` file:
```env
DATABASE_URL=sqlite:///clipboard.db
TZ=Asia/Shanghai
LOG_LEVEL=INFO
```

## Development

### Tech Stack

- **Backend**: FastAPI
- **Frontend**: HTML5 + CSS3 + JavaScript
- **Authentication**: JWT (JSON Web Tokens)
- **Real-time Communication**: WebSocket
- **Database**: MySQL / SQLite

## License

[MIT License](LICENSE)
