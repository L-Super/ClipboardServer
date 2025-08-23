from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    device_id: str
    device_name: str
    device_type: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class DeviceBase(BaseModel):
    id: str
    name: str
    type: str
    last_active: datetime
    is_active: bool

    class Config:
        orm_mode = True


class ClipboardItemCreate(BaseModel):
    type: str
    data: str  # 对于图片，是URL
    meta: Optional[dict] = None


class FileInfo(BaseModel):
    url: str
    filename: str
    size: int
    content_type: str


class ClipboardItemResponse(BaseModel):
    id: int
    created_at: datetime
    file_info: Optional[FileInfo] = None


class WebSocketMessage(BaseModel):
    action: str
    type: str
    data: str  # 对于图片，是URL
    data_hash: str
    meta: Optional[dict] = None
