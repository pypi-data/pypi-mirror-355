import os
import smtplib
from email.message import EmailMessage
from email.utils import make_msgid, formataddr
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.environ.get("SMTP_HOST")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
SMTP_FROM_ADDRESS = os.environ.get("SMTP_FROM_ADDRESS")
SMTP_FROM_NAME = os.environ.get("SMTP_FROM_NAME")


def send_email(to_email: str, subject: str, plain_body: str = None, html_body: str = None, attachments: list = None):
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = formataddr((SMTP_FROM_NAME, SMTP_FROM_ADDRESS))
        msg["To"] = to_email

        if not plain_body and not html_body:
            return False, f"Failed to send email: Content is empty"
        if isinstance(plain_body, str) and plain_body.strip():
            msg.set_content(plain_body)
        if isinstance(html_body, str) and html_body.strip():
            msg.add_alternative(html_body, subtype='html')

        if attachments:
            for file in attachments:
                filename = file.get("filename")
                content = file.get("content")
                if not content:
                    continue
                mime_type = file.get("mime_type", "application/octet-stream")
                maintype, subtype = mime_type.split("/", 1)
                msg.add_attachment(content, maintype=maintype, subtype=subtype, filename=filename)

        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
            smtp.send_message(msg)
        return True, "Email send success"

    except Exception as e:
        return False, f"Failed to send email: {e}"
