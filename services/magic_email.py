"""Magic Link póstsending — þróun: Gmail SMTP, framleiðsla: íslenskt relay."""
import os, smtplib, logging
from email.mime.text import MIMEText

logger = logging.getLogger("alvitur.magic_email")

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "sigvaldimimir@gmail.com")
SMTP_PASS = os.environ.get("SMTP_PASS", "")

def send_magic_link(email: str, token: str) -> bool:
    url = f"https://alvitur.is/login?token={token}"
    body = f"""Halló,

Hér er innskráningartengill fyrir Alvitur:

{url}

Tengillinn gildir í 10 mínútur og er einnota.

Kveðja,
Alvitur
"""
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = "Innskráningartengill — Alvitur"
    msg["From"] = SMTP_USER
    msg["To"] = email
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
        logger.info(f"Magic link sendur til {email}")
        return True
    except Exception as e:
        logger.error(f"Magic link póstsending mistókst: {e}")
        return False
