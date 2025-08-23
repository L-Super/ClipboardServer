import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # DATABASE_URL: str = "mysql+pymysql://user:password@localhost/clipboard_db"
    DATABASE_URL: str = "sqlite:///clipboard.db"
    SECRET_KEY: str = "clipboard_key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    TZ: str = "Asia/Shanghai"

    class Config:
        env_file = ".env"


settings = Settings()
