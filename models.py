"""
生成数据库模型
"""
from sqlalchemy import Column, Integer, String, Text, Enum, TIMESTAMP, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(60), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    last_login = Column(TIMESTAMP)
    devices = relationship("Device", back_populates="user")
    clipboard_items = relationship("ClipboardItem", back_populates="user")


class Device(Base):
    __tablename__ = "devices"
    id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    name = Column(String(50), nullable=False)
    type = Column(Enum('ios', 'android', 'windows', 'macos', 'linux', 'web'), nullable=False)
    last_active = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=False)
    user = relationship("User", back_populates="devices")
    sync_state = relationship("SyncState", back_populates="device", uselist=False)


class ClipboardItem(Base):
    __tablename__ = "clipboard_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    device_id = Column(String(36), ForeignKey("devices.id"), nullable=False)
    item_type = Column(Enum('text', 'image', 'file'), nullable=False)
    content_hash = Column(String(64), nullable=False)
    content = Column(Text)
    meta_data = Column(JSON)
    created_at = Column(TIMESTAMP(6), server_default=func.now(6))
    expires_at = Column(TIMESTAMP)
    is_compressed = Column(Boolean, default=False)
    # version = Column(Integer, nullable=False, index=True)
    user = relationship("User", back_populates="clipboard_items")
    device = relationship("Device")


class SyncState(Base):
    __tablename__ = "sync_state"
    user_id = Column(String(36), ForeignKey("users.id"), primary_key=True)
    device_id = Column(String(36), ForeignKey("devices.id"), primary_key=True)
    # 最后一次同步的ID
    last_synced_id = Column(Integer, default=0)
    last_sync = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    device = relationship("Device", back_populates="sync_state")
