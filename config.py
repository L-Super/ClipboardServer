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

    # upload config
    MAX_UPLOAD_SIZE_MB: int = 20  # 上传文件最大大小（MB）

    # email config
    SMTP_HOST: str = ""  # SMTP 服务器地址
    SMTP_PORT: int = 587  # SMTP 端口，587 为 TLS 加密端口
    SMTP_USER: str = ""  # SMTP 登录用户名（通常为邮箱地址）
    SMTP_PASSWORD: str = ""  # SMTP 授权码（非邮箱登录密码）
    SMTP_FROM_EMAIL: str = ""  # 发件人邮箱地址
    EMAIL_CODE_EXPIRE_MINUTES: int = 5  # 验证码有效期（分钟）

    # use env file to get var
    class Config:
        env_file = ".env"


settings = Settings()