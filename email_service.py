"""
邮件发送服务
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone
import random
import string
import config
import log


def generate_verification_code(length: int = 6) -> str:
    """生成指定长度的数字验证码"""
    return ''.join(random.choices(string.digits, k=length))


def send_verification_code_email(to_email: str, code: str) -> bool:
    """
    发送验证码邮件
    
    Args:
        to_email: 收件人邮箱
        code: 验证码
        
    Returns:
        bool: 发送是否成功
    """
    try:
        # 创建邮件对象，同时支持HTML和Plain格式
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Floward 验证码登录'
        msg['From'] = config.settings.SMTP_FROM_EMAIL
        msg['To'] = to_email

        # HTML 格式
        html_content = f"""
        <html>
          <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
              <h2 style="color: #333; text-align: center;">Floward 验证码</h2>
              <p style="color: #666; font-size: 16px;">您的登录验证码是：</p>
              <div style="background-color: #f5f5f5; padding: 20px; text-align: center; margin: 20px 0; border-radius: 5px;">
                <h1 style="color: #007bff; font-size: 32px; margin: 0; letter-spacing: 5px;">{code}</h1>
              </div>
              <p style="color: #999; font-size: 14px;">验证码有效期为 {config.settings.EMAIL_CODE_EXPIRE_MINUTES} 分钟，请勿泄露给他人。</p>
              <p style="color: #999; font-size: 14px;">如果这不是您的操作，请忽略此邮件。</p>
              <div style="margin-top: 30px; font-size: 12px; color: #95a5a6; text-align: center">
                此为系统自动发送邮件，请勿直接回复！
              </div>
            </div>
          </body>
        </html>
        """

        # 纯文本格式
        text_content = f"""
        Floward 验证码
        
        您的登录验证码是：{code}
        
        验证码有效期为 {config.settings.EMAIL_CODE_EXPIRE_MINUTES} 分钟，请勿泄露给他人。
        如果这不是您的操作，请忽略此邮件。
        此为系统自动发送邮件，请勿直接回复！
        """

        # 添加文本和HTML版本，会优先显示 HTML，不支持时回退到纯文本
        msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))

        # 连接SMTP服务器并发送
        with smtplib.SMTP_SSL(config.settings.SMTP_HOST, config.settings.SMTP_PORT) as server:
            server.login(config.settings.SMTP_USER, config.settings.SMTP_PASSWORD)
            server.send_message(config.settings)

        log.info(f"Verification code email sent to {to_email}")
        return True

    except Exception as e:
        log.error(f"Failed to send verification code email to {to_email}: {e}", logger_name=__name__)
        return False


def get_code_expires_at() -> datetime:
    """获取验证码过期时间"""
    return datetime.now(timezone.utc) + timedelta(minutes=config.settings.EMAIL_CODE_EXPIRE_MINUTES)
