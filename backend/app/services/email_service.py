import logging
import smtplib
from email.mime.text import MIMEText
from app.core.config import settings

logger = logging.getLogger("careerpilot.email")


def _send(to_email: str, subject: str, body: str) -> None:
    if not settings.SMTP_HOST:
        # Dev / CI fallback — no real SMTP configured, just log it.
        logger.info("=== EMAIL (dev mode, not actually sent) ===")
        logger.info("To: %s | Subject: %s", to_email, subject)
        logger.info(body)
        logger.info("=============================================")
        return

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        if settings.SMTP_USER:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_FROM, [to_email], msg.as_string())


def send_verification_email(to_email: str, token: str) -> None:
    link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    body = (
        f"Welcome to CareerPilot!\n\n"
        f"Please verify your email by visiting:\n{link}\n\n"
        f"This link expires in {settings.EMAIL_TOKEN_EXPIRE_HOURS} hours."
    )
    _send(to_email, "Verify your CareerPilot account", body)


def send_password_reset_email(to_email: str, token: str) -> None:
    link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    body = (
        f"We received a request to reset your CareerPilot password.\n\n"
        f"Reset it here:\n{link}\n\n"
        f"This link expires in {settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} minutes. "
        f"If you didn't request this, you can ignore this email."
    )
    _send(to_email, "Reset your CareerPilot password", body)
