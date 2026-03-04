"""
Send report by email via SMTP (Gmail-compatible).
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import config


def send_report(plain_text: str, html_text: str, subject: str | None = None) -> None:
    """Send digest report to configured email."""
    if not config.SMTP_PASSWORD:
        raise ValueError(
            "DIGEST_SMTP_PASSWORD is not set. "
            "Use a Gmail App Password: https://support.google.com/accounts/answer/185833"
        )
    if subject is None:
        subject = "Long-read sequencing & metagenomics digest"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config.EMAIL_FROM
    msg["To"] = config.EMAIL_TO

    msg.attach(MIMEText(plain_text, "plain", "utf-8"))
    msg.attach(MIMEText(html_text, "html", "utf-8"))

    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
        server.starttls()
        server.login(config.SMTP_USER, config.SMTP_PASSWORD)
        server.sendmail(config.EMAIL_FROM, [config.EMAIL_TO], msg.as_string())
