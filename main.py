import mimetypes
import os
from datetime import datetime, timedelta, timezone

import uvicorn
from fastapi import FastAPI, HTTPException, status, Depends, WebSocket, WebSocketDisconnect, BackgroundTasks, \
    UploadFile, Form, File, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

import crud
from config import settings
from connection_manager import ConnectionManager
from database import get_db, create_db
import models
import auth
import schemas
import log

UPLOAD_DIR = "uploads"


def save_upload_file(file: UploadFile) -> str:
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)
    ext = os.path.splitext(file.filename)[-1]
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    return file_path


def get_file_url(file_path: str) -> str:
    # 假设静态文件通过 /files/ 访问
    filename = os.path.basename(file_path)
    return f"/files/{filename}"


# FastAPI应用
app = FastAPI(
    title="Clipboard Sync API",
    description="API for cross-device clipboard synchronization",
    version="1.0.0"
)

# 挂载静态文件
app.mount("/files", StaticFiles(directory="uploads", check_dir=False), name="files")
app.mount("/static", StaticFiles(directory="static"), name="static")

# WebSocket连接管理器
manager = ConnectionManager()


# 应用程序启动前运行
@app.on_event("startup")
def on_startup():
    log.setup_logging()

    # 创建数据库表
    create_db()


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    log.info('app was shut down')


# 根路由 - 返回登录页面
@app.get("/", response_class=HTMLResponse)
async def root():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


# 登录页面路由
@app.get("/login", response_class=HTMLResponse)
async def login_page():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


# 仪表板页面路由
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    with open("static/dashboard.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


# 设备指纹测试页面路由
@app.get("/test-fingerprint", response_class=HTMLResponse)
async def test_fingerprint():
    with open("static/test_fingerprint.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


def create_token(user_id: str, device_id: str) -> tuple[str, str]:
    # 创建访问令牌
    access_token_expires = timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
    a_token = auth.create_access_token(
        data={"sub": user_id, "device_id": device_id},
        expires_delta=access_token_expires
    )

    # 创建刷新令牌
    r_token = auth.create_refresh_token(
        data={"sub": user_id},
    )
    return a_token, r_token


# 注册
@app.post("/auth/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # 检查邮箱是否已注册
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # 创建用户
    db_user = crud.create_user(db, user)

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User registration failed"
        )

    log.info(f"User {db_user.email} registered")

    return {
        "code": 0,
        "message": "User registration successfully"
    }


# 登录
@app.post("/auth/login", response_model=schemas.Token)
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    # 验证用户
    db_user = crud.get_user_by_email(db, email=user.email)
    if not db_user or not auth.verify_password(user.password, db_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # 获取所有允许的设备类型
    allowed_types = ['ios', 'android', 'windows', 'macos', 'linux', 'web']

    if user.device_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid device type"
        )

    # 创建设备并激活设备
    device = crud.get_or_create_device(db, user_id=db_user.id, device_id=user.device_id, device_name=user.device_name,
                                       device_type=user.device_type, is_active=True)
    # 更新用户的上线时间
    db_user.last_login = datetime.now(timezone.utc)
    db.commit()

    # 创建令牌
    access_token, refresh_token = create_token(db_user.id, device.id)

    log.info(f"User {db_user.email} logged in")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@app.get("/auth/verify-token")
def verify_token(authorization: str = Header(...)):
    """
    校验 access_token 是否有效（通过 Authorization 头）
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )
    token = authorization.removeprefix("Bearer ").strip()
    try:
        user_id, device_id = auth.decode_token(token)
        return {"code": 0, "message": "Token is valid", "user_id": user_id, "device_id": device_id}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired"
        )


@app.post("/auth/refresh", response_model=schemas.Token)
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = crud.get_user(db, user_id)
    if not user:
        raise credentials_exception

    # 获取当前设备
    device = db.query(models.Device).filter(
        models.Device.user_id == user_id).order_by(models.Device.last_active.desc()).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active device found"
        )

    # 创建新令牌
    access_token, new_refresh_token = create_token(user_id, device.id)

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


# 获取设备列表
@app.get("/devices", response_model=list[schemas.DeviceBase])
def get_devices(
        current_user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(get_db)
):
    devices = db.query(models.Device).filter(
        models.Device.user_id == current_user.id
    ).all()
    return devices


@app.patch("/devices/{device_id}/rename")
def rename_device(
        device_id: str,
        new_name: str,
        current_user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(get_db)
):
    device = db.query(models.Device).filter(
        models.Device.id == device_id,
        models.Device.user_id == current_user.id
    ).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    device.name = new_name
    db.commit()
    return {"code": 0, "message": "Device renamed successfully"}


@app.delete("/devices/{device_id}")
def delete_device(
        device_id: str,
        current_user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(get_db)
):
    """
    TODO:未验证
    :param device_id:
    :param current_user:
    :param db:
    :return:
    """
    device = db.query(models.Device).filter(
        models.Device.id == device_id,
        models.Device.user_id == current_user.id
    ).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    # 先删除子表数据（外键约束所在表）
    db.query(models.ClipboardItem).filter(
        models.ClipboardItem.device_id == device_id
    ).delete(synchronize_session=False)
    # 再删除父表数据
    db.delete(device)
    db.commit()
    return {"code": 0, "message": "Device delete successfully"}


# 上传剪贴板内容
@app.post("/clipboard", response_model=schemas.ClipboardItemResponse)
async def upload_clipboard_item(background_tasks: BackgroundTasks,
                                type: str = Form(...),
                                data: str = Form(None),
                                file: UploadFile = File(None),
                                current_user: models.User = Depends(auth.get_current_user),
                                current_device: models.Device = Depends(auth.get_current_active_device),
                                db: Session = Depends(get_db)
                                ):
    meta = {}
    file_url: str = ''
    content_type: str = ''

    if type in ("image", "file") and file:
        file_path = save_upload_file(file)
        file_url = get_file_url(file_path)

        content = file_url
        content_type = file.content_type or mimetypes.guess_type(file.filename)[0]
        meta = {
            "filename": file.filename,
            "content_type": content_type,
            "size": file.size,
        }
        log.info(f'file name:{file.filename} type:{file.content_type} size:{file.size} path:{file_path} url:{file_url}')
    else:
        content = data

    clipboard_item = schemas.ClipboardItemCreate(
        type=type,
        data=content,
        meta=meta
    )

    # 创建剪贴板条目
    db_item = crud.create_clipboard_item(db, clipboard_item, current_device.user_id, current_device.id)

    # 通知其他设备（后台任务）
    background_tasks.add_task(
        notify_devices_of_update,
        current_user.id,
        current_device.id,
        db_item,
        db
    )

    if type in ("image", "file"):
        return {
            "id": db_item.id,
            "created_at": db_item.created_at,
            "file_info": {
                "url": file_url,  # 文件访问URL
                "filename": file.filename,  # 原始文件名
                "size": file.size,  # 文件大小
                "content_type": content_type,  # 文件类型
            }
        }

    return {
        "id": db_item.id,
        "created_at": db_item.created_at,
    }


# WebSocket实时通知，客户端连接，监听消息
@app.websocket("/sync/notify")
async def websocket_endpoint(
        websocket: WebSocket,
        token: str,
        db: Session = Depends(get_db)
):
    # 验证token
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        device_id: str = payload.get("device_id")
        if not user_id or not device_id:
            log.error(f'user:{user_id} or device:{device_id} not found in token')
            # WS_1008_POLICY_VIOLATION: 由于收到不符合约定的数据而断开连接。
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    except JWTError:
        log.error(f'verify token failed. token: {token}')
        await websocket.close(code=3000, reason='token expired')
        return

    # 检查设备是否存在
    device = db.query(models.Device).filter(
        models.Device.id == device_id,
        models.Device.user_id == user_id
    ).first()

    if not device:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    crud.activate_device(db, device_id)
    # 连接WebSocket
    await manager.connect(websocket, user_id, device_id)

    try:
        while True:
            data = await websocket.receive_text()
            log.debug('received message:', data)
            # 客户端可以发送心跳或其他控制消息
            # 在此实现中我们主要处理服务器推送
    except WebSocketDisconnect as e:
        log.warning(f'user: {user_id} device: {device_id} websocket offline. reason: {e}')
        # 断开时，将数据库里的device的is_active状态置为false
        device = db.query(models.Device).filter(
            models.Device.id == device_id,
            models.Device.user_id == user_id
        ).first()
        if device:
            device.is_active = False
            db.commit()
        manager.disconnect(user_id, device_id)

    except Exception as e:
        log.error(f'user: {user_id} device: {device_id} websocket except. reason: {e}')
        manager.disconnect(user_id, device_id)


# 通知其他设备有新内容
async def notify_devices_of_update(user_id: str, source_device_id: str, item: models.ClipboardItem, db: Session):
    # 获取当前用户的所有活动设备（除了源设备）
    devices = db.query(models.Device).filter(
        models.Device.user_id == user_id,
        models.Device.id != source_device_id,
        models.Device.is_active == True
    ).all()

    if not devices:
        return

    log.info('notify devices of update. device count:', len(devices))
    # 准备通知消息
    message = schemas.WebSocketMessage(
        action="update",
        type=item.item_type,
        data=item.content,
        data_hash=item.content_hash,
        meta=item.meta_data or {}
    ).model_dump_json()

    # 向所有相关设备发送通知
    for device in devices:
        log.info(f'notify user:{user_id}  from device:{source_device_id} to device:{device.id}')
        log.debug(f'send websocket message:{message}')
        await manager.send_personal_message(message, user_id, device.id)


# 错误处理
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.detail.get("code") if isinstance(exc.detail, dict) else "UNKNOWN_ERROR",
                "message": exc.detail.get("message") if isinstance(exc.detail, dict) else exc.detail
            }
        }
    )


# 启动应用
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    # if not os.path.exists(UPLOAD_DIR):
    #     os.makedirs(UPLOAD_DIR)
    # pass
