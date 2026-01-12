"""
验证码内存缓存管理
使用内存字典存储验证码，支持自动过期清理
"""
import threading
from datetime import datetime, timezone
from typing import Optional

import log


class VerificationCodeCache:
    """验证码内存缓存类"""

    def __init__(self):
        self._cache: dict[str, dict] = {}  # {email: {code: str, expires_at: datetime, is_used: bool}}
        self._lock = threading.RLock()  # 线程安全锁
        self._cleanup_interval = 60  # 清理间隔（秒）
        self._last_cleanup = datetime.now(timezone.utc)

    def save(self, email: str, code: str, expires_at: datetime):
        """
        存储验证码
        
        Args:
            email: 邮箱地址
            code: 验证码
            expires_at: 过期时间
        """
        with self._lock:
            self._cache[email] = {
                'code': code,
                'expires_at': expires_at,
                'is_used': False,
                'created_at': datetime.now(timezone.utc)
            }
            log.debug(f"Verification code cached for {email}")

    def verify(self, email: str, code: str) -> bool:
        """
        验证验证码是否有效
        
        Args:
            email: 邮箱地址
            code: 验证码
            
        Returns:
            bool: 验证码是否有效
        """
        with self._lock:
            self._cleanup_expired()  # 清理过期数据

            if email not in self._cache:
                return False

            cached = self._cache[email]
            now = datetime.now(timezone.utc)

            # 检查是否过期
            if cached['expires_at'] <= now:
                del self._cache[email]
                return False

            # 检查是否已使用
            if cached['is_used']:
                return False

            # 检查验证码是否匹配
            if cached['code'] != code:
                return False

            return True

    def mark_as_used(self, email: str, code: str) -> bool:
        """
        标记验证码为已使用
        
        Args:
            email: 邮箱地址
            code: 验证码
            
        Returns:
            bool: 是否成功标记
        """
        with self._lock:
            if email not in self._cache:
                return False

            cached = self._cache[email]

            # 验证码必须匹配
            if cached['code'] != code:
                return False

            # 标记为已使用
            cached['is_used'] = True
            log.debug(f"Verification code marked as used for {email}")
            return True

    def _cleanup_expired(self):
        """清理过期的验证码"""
        now = datetime.now(timezone.utc)

        # 每60秒清理一次，避免频繁清理
        if (now - self._last_cleanup).total_seconds() < self._cleanup_interval:
            return

        expired_emails = [
            email for email, data in self._cache.items()
            if data['expires_at'] <= now or data['is_used']
        ]

        for email in expired_emails:
            del self._cache[email]

        if expired_emails:
            log.debug(f"Cleaned up {len(expired_emails)} expired verification codes")

        self._last_cleanup = now

    def clear(self, email: Optional[str] = None):
        """
        清除验证码
        
        Args:
            email: 如果提供，只清除该邮箱的验证码；否则清除所有
        """
        with self._lock:
            if email:
                self._cache.pop(email, None)
            else:
                self._cache.clear()


# 全局验证码缓存实例
code_cache = VerificationCodeCache()
