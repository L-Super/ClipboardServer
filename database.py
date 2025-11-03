from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from config import settings

# 数据库配置
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL
engine = create_engine(SQLALCHEMY_DATABASE_URL,
                       pool_recycle=3600,  # 回收连接时间（1小时），应小于MySQL的wait_timeout
                       pool_pre_ping=True,  # 使用前ping检查连接是否有效
                       pool_size=20,  # 连接池大小
                       max_overflow=5,  # 增加溢出连接数
                       pool_timeout=10,  # 增加超时时间到10秒
                       pool_reset_on_return=True,  # 归还时回滚
                       pool_use_lifo=True)  # 使用LIFO提高连接复用
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def create_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    """
    return: db session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Session:
    """Context manager for manual database session management"""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
