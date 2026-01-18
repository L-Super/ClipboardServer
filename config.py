from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # DATABASE_URL: str = "mysql+pymysql://user:password@localhost/clipboard_db"
    DATABASE_URL: str = "sqlite:///clipboard.db"
    SECRET_KEY: str = "clipboard_key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    TZ: str = "Asia/Shanghai"

    # log config
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT:str = "[%(asctime)s - %(levelname)s (%(name)s) %(filename)s:%(lineno)d] %(message)s"
    LOG_FILE_PATH: str = "logs/app_log.log"
    LOG_MAX_BYTES: int = 102400 # 100KB
    LOG_BACKUP_COUNT: int = 3
    LOG_ENABLE_CONSOLE: bool = True
    LOG_ENABLE_FILE: bool = True

    # use env file to get var
    class Config:
        env_file = ".env"


settings = Settings()