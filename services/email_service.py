"""SMTP email delivery service."""

import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr

from config import Config


class EmailServiceError(Exception):
    """Base exception for email delivery errors."""


class EmailConfigurationError(EmailServiceError):
    """Raised when SMTP configuration is missing or invalid."""


class EmailSendingError(EmailServiceError):
    """Raised when an email cannot be delivered to the SMTP server."""


def send_email(
        to_email: str,
        subject: str,
        body: str,
        html_body: str | None = None,
) -> None:
    """Send an email using the configured SMTP server.

    SMTP credentials are read from Config. The function does not log
    credentials or include SMTP server details in public-facing errors.

    Raises:
        ValueError: If the recipient, subject, or body is empty.
        EmailConfigurationError: If SMTP configuration is invalid.
        EmailSendingError: If SMTP delivery fails.
    """
    if not to_email or not to_email.strip():
        raise ValueError("Recipient email must not be empty")

    if not subject or not subject.strip():
        raise ValueError("Email subject must not be empty")

    if not body and not html_body:
        raise ValueError("Email body must not be empty")

    if not Config.smtp_host.strip():
        raise EmailConfigurationError("SMTP_HOST is not configured")

    if not Config.smtp_from_email.strip():
        raise EmailConfigurationError("SMTP_FROM_EMAIL is not configured")

    if Config.smtp_port < 1 or Config.smtp_port > 65535:
        raise EmailConfigurationError("SMTP_PORT is invalid")

    if Config.smtp_timeout <= 0:
        raise EmailConfigurationError("SMTP_TIMEOUT must be positive")

    if Config.smtp_security not in {"starttls", "ssl", "none"}:
        raise EmailConfigurationError(
            "SMTP_SECURITY must be starttls, ssl, or none"
        )

    if bool(Config.smtp_username) != bool(Config.smtp_password):
        raise EmailConfigurationError(
            "SMTP_USERNAME and SMTP_PASSWORD must be configured together"
        )

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = formataddr(
        (Config.smtp_from_name, Config.smtp_from_email)
    )
    message["To"] = to_email
    message.set_content(body)

    if html_body:
        message.add_alternative(html_body, subtype="html")

    try:
        if Config.smtp_security == "ssl":
            with smtplib.SMTP_SSL(
                    Config.smtp_host,
                    Config.smtp_port,
                    timeout=Config.smtp_timeout,
                    context=ssl.create_default_context(),
            ) as server:
                _send_message(server, message)

        else:
            with smtplib.SMTP(
                    Config.smtp_host,
                    Config.smtp_port,
                    timeout=Config.smtp_timeout,
            ) as server:
                server.ehlo()

                if Config.smtp_security == "starttls":
                    server.starttls(context=ssl.create_default_context())
                    server.ehlo()

                _send_message(server, message)

    except (OSError, smtplib.SMTPException) as exc:
        raise EmailSendingError("Failed to send email") from exc


def _send_message(
        server: smtplib.SMTP,
        message: EmailMessage,
) -> None:
    """Authenticate if configured and submit the message."""
    if Config.smtp_username:
        server.login(Config.smtp_username, Config.smtp_password)

    refused_recipients = server.send_message(message)

    if refused_recipients:
        raise EmailSendingError(
            "The SMTP server refused one or more recipients"
        )
