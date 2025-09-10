from sqlalchemy.orm import Session
import models
import schemas
from auth import get_password_hash
import uuid
import hashlib


def get_user(db: Session, user_id: str) -> type[models.User] | None:
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> type[models.User] | None:
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        id=str(uuid.uuid4()),
        email=user.email,
        password_hash=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_or_create_device(db: Session, user_id: str, device_id: str, device_name: str, device_type: str,
                         is_active=False) -> models.Device:
    # 查询是否存在该设备并更新在线状态
    existing_device = db.query(models.Device).filter(models.Device.id == device_id).first()
    if existing_device:
        existing_device.is_active = is_active
        db.commit()
        db.refresh(existing_device)
        return existing_device

    db_device = models.Device(
        id=device_id,
        user_id=user_id,
        name=device_name,
        type=device_type,
        is_active=is_active
    )
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device


def activate_device(db: Session, device_id: str):
    existing_device = db.query(models.Device).filter(models.Device.id == device_id).first()
    if existing_device:
        existing_device.is_active = True
        db.commit()


def get_device(db: Session, device_id: str) -> type[models.Device] | None:
    return db.query(models.Device).filter(models.Device.id == device_id).first()


def create_clipboard_item(db: Session, item: schemas.ClipboardItemCreate, user_id: str,
                          device_id: str) -> models.ClipboardItem:
    content_hash = ''
    if item.type == 'text':
        content_hash = hashlib.md5(item.data.encode('utf-8')).hexdigest()

    db_item = models.ClipboardItem(
        user_id=user_id,
        device_id=device_id,
        item_type=item.type,
        content=item.data,
        content_hash=content_hash,  # 计算内容md5哈希
        meta_data=item.meta,
        is_compressed=True if item.type == 'text' else False
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def get_sync_state(db: Session, user_id: str, device_id: str) -> type[models.SyncState] | None:
    return db.query(models.SyncState).filter(
        models.SyncState.user_id == user_id,
        models.SyncState.device_id == device_id
    ).first()


def get_latest_version(db: Session, user_id: str) -> int:
    last_item = db.query(models.ClipboardItem).filter(
        models.ClipboardItem.user_id == user_id
    ).order_by(models.ClipboardItem.id.desc()).first()
    return last_item.id if last_item else 0


def get_clipboard_items_since(db: Session, user_id: str, last_version: int, limit: int = 50) -> list[
    type[models.ClipboardItem]]:
    return db.query(models.ClipboardItem).filter(
        models.ClipboardItem.user_id == user_id,
        models.ClipboardItem.id > last_version
    ).order_by(models.ClipboardItem.id.asc()).limit(limit).all()
