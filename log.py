import logging
import logging.handlers
import os
import sys
from config import settings


class LoggingConfig:
    """日志配置类"""

    def __init__(self):
        self.log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
        self.log_format = settings.LOG_FORMAT
        self.log_file_path = settings.LOG_FILE_PATH
        self.max_bytes = settings.LOG_MAX_BYTES
        self.backup_count = settings.LOG_BACKUP_COUNT
        self.enable_console = settings.LOG_ENABLE_CONSOLE
        self.enable_file = settings.LOG_ENABLE_FILE

        # 确保日志目录存在
        if self.enable_file:
            log_dir = os.path.dirname(self.log_file_path)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)

    def setup_logging(self) -> None:
        """设置日志配置"""
        root_logger = logging.getLogger()

        # 设置根日志级别
        root_logger.setLevel(self.log_level)

        # 创建格式化器
        formatter = logging.Formatter(self.log_format)

        # 控制台处理器
        if self.enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.log_level)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)

        # 文件处理器（使用RotatingFileHandler日志轮转）
        if self.enable_file:
            file_handler = logging.handlers.RotatingFileHandler(
                self.log_file_path,
                maxBytes=self.max_bytes,
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(self.log_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志记录器"""
    return logging.getLogger(name)


def setup_logging() -> None:
    """设置应用程序日志"""
    config = LoggingConfig()
    config.setup_logging()


def info(message: str, logger_name: str = "app") -> None:
    """记录信息日志"""
    logger = get_logger(logger_name)
    # stacklevel=2 -> 跳过当前这一层 helper，指向真正的调用处
    logger.info(message, stacklevel=2)


def warning(message: str, logger_name: str = "app") -> None:
    """记录警告日志"""
    logger = get_logger(logger_name)
    logger.warning(message, stacklevel=2)


def error(message: str, logger_name: str = "app", exc_info: bool = False) -> None:
    """记录错误日志"""
    logger = get_logger(logger_name)
    logger.error(message, stacklevel=2, exc_info=exc_info)


def debug(message: str, logger_name: str = "app") -> None:
    """记录调试日志"""
    logger = get_logger(logger_name)
    logger.debug(message, stacklevel=2)


def critical(message: str, logger_name: str = "app", exc_info: bool = False) -> None:
    """记录严重错误日志"""
    logger = get_logger(logger_name)
    logger.critical(message, stacklevel=2, exc_info=exc_info)
