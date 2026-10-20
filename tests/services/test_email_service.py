import smtplib
from unittest.mock import patch

import pytest

from config import Config
from services.email_service import (
    EmailConfigurationError,
    EmailSendingError,
    send_email,
)


@pytest.fixture
def smtp_config(monkeypatch):
    monkeypatch.setattr(Config, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(Config, "smtp_port", 587)
    monkeypatch.setattr(Config, "smtp_username", "sender@example.com")
    monkeypatch.setattr(Config, "smtp_password", "test-password")
    monkeypatch.setattr(Config, "smtp_from_email", "sender@example.com")
    monkeypatch.setattr(Config, "smtp_from_name", "KWS Station")
    monkeypatch.setattr(Config, "smtp_security", "starttls")
    monkeypatch.setattr(Config, "smtp_timeout", 10.0)


def test_send_email_uses_starttls(smtp_config):
    with patch("services.email_service.smtplib.SMTP") as smtp_class:
        server = smtp_class.return_value.__enter__.return_value
        server.send_message.return_value = {}

        send_email(
            to_email="recipient@example.com",
            subject="Test subject",
            body="Test message",
        )

        smtp_class.assert_called_once_with(
            "smtp.example.com",
            587,
            timeout=10.0,
        )
        server.ehlo.assert_called()
        server.starttls.assert_called_once()
        server.login.assert_called_once_with(
            "sender@example.com",
            "test-password",
        )
        server.send_message.assert_called_once()

        message = server.send_message.call_args.args[0]
        assert message["To"] == "recipient@example.com"
        assert message["Subject"] == "Test subject"


def test_send_email_supports_html(smtp_config):
    with patch("services.email_service.smtplib.SMTP") as smtp_class:
        server = smtp_class.return_value.__enter__.return_value
        server.send_message.return_value = {}

        send_email(
            to_email="recipient@example.com",
            subject="HTML message",
            body="Plain text",
            html_body="<h1>Hello</h1>",
        )

        message = (
            smtp_class.return_value
            .__enter__.return_value
            .send_message.call_args.args[0]
        )

        assert message.is_multipart()
        assert len(message.get_payload()) == 2


def test_send_email_uses_ssl(smtp_config, monkeypatch):
    monkeypatch.setattr(Config, "smtp_security", "ssl")
    monkeypatch.setattr(Config, "smtp_port", 465)

    with patch("services.email_service.smtplib.SMTP_SSL") as smtp_ssl_class:
        server = smtp_ssl_class.return_value.__enter__.return_value
        server.send_message.return_value = {}

        send_email(
            to_email="recipient@example.com",
            subject="SSL test",
            body="Message",
        )

        smtp_ssl_class.assert_called_once()
        server.starttls.assert_not_called()
        server.send_message.assert_called_once()


def test_send_email_fails_without_smtp_host(smtp_config, monkeypatch):
    monkeypatch.setattr(Config, "smtp_host", "")

    with pytest.raises(EmailConfigurationError, match="SMTP_HOST"):
        send_email(
            to_email="recipient@example.com",
            subject="Test",
            body="Message",
        )


def test_send_email_rejects_incomplete_credentials(
        smtp_config,
        monkeypatch,
):
    monkeypatch.setattr(Config, "smtp_password", "")

    with pytest.raises(EmailConfigurationError, match="configured together"):
        send_email(
            to_email="recipient@example.com",
            subject="Test",
            body="Message",
        )


def test_send_email_wraps_smtp_errors(smtp_config):
    with patch(
            "services.email_service.smtplib.SMTP",
            side_effect=smtplib.SMTPException("SMTP failure"),
    ):
        with pytest.raises(EmailSendingError, match="Failed to send"):
            send_email(
                to_email="recipient@example.com",
                subject="Test",
                body="Message",
            )


@pytest.mark.parametrize(
    ("recipient", "subject", "body"),
    [
        ("", "Subject", "Body"),
        ("recipient@example.com", "", "Body"),
        ("recipient@example.com", "Subject", ""),
    ],
)
def test_send_email_rejects_empty_fields(
        smtp_config,
        recipient,
        subject,
        body,
):
    with pytest.raises(ValueError):
        send_email(
            to_email=recipient,
            subject=subject,
            body=body,
        )
