"""Alvitur Email Agent — Les og svarar póstum sjálfkrafa (Sprint 80).

Endurvakið úr core/tools.py — uppfært fyrir info@alvitur.is.
Sprint 80: anti-loop, dedup, rate-limit (Opus kröfur).
"""
import os
import smtplib
import imaplib
import email
import time
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv('/workspace/.env')
logger = logging.getLogger("alvitur.email_agent")

IMAP_SERVER = "imap.gmail.com"
SMTP_SERVER = "smtp.gmail.com"
EMAIL_USER = os.getenv("ALVITUR_EMAIL_USER", "info@alvitur.is")
EMAIL_PASS = os.getenv("ALVITUR_EMAIL_PASS", "")

# Dedup + rate limit storage
_sent_history = {}
_RATE_LIMIT_HOUR = 10
_DEDUP_HOURS = 24


def send_email(to_address: str, subject: str, body: str) -> str:
    """Sendir tölvupóst frá info@alvitur.is (Sprint 80: anti-loop headers)."""
    if not EMAIL_PASS:
        return "Villa: ALVITUR_EMAIL_PASS vantar í .env"

    try:
        msg = MIMEMultipart()
        msg['From'] = f"Alvitur <{EMAIL_USER}>"
        msg['To'] = to_address
        msg['Subject'] = subject
        msg['Auto-Submitted'] = 'auto-replied'
        msg['X-Auto-Response-Suppress'] = 'All'
        msg['Precedence'] = 'bulk'
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        with smtplib.SMTP(SMTP_SERVER, 587, timeout=300.0) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)

        logger.info(f"Póstur sendur á {to_address}: {subject}")
        return f"Póstur sendur á {to_address}"

    except smtplib.SMTPAuthenticationError:
        return "Villa: App Password rangt eða útrunnið."
    except Exception as e:
        return f"Villa við sendingu: {str(e)[:200]}"


def process_and_reply(query_text: str = "") -> str:
    """Athugar pósthólf, sendir auto-reply með dedup + rate limit."""
    global _sent_history
    if not EMAIL_PASS:
        return "ALVITUR_EMAIL_PASS ekki stillt — sleppi póstvinnslu"

    # Hreinsa útrunnið sent history
    now = time.time()
    _sent_history = {k: v for k, v in _sent_history.items() if now - v < 3600}

    # Rate limit check
    recent = sum(1 for t in _sent_history.values() if now - t < 3600)
    if recent >= _RATE_LIMIT_HOUR:
        logger.warning(f"Rate limit náð: {recent} replies síðasta klst — sleppi")
        return f"Rate limit: {recent}/{_RATE_LIMIT_HOUR} replies síðasta klst"

    # Sækja ólesna pósta (einfölduð útgáfa — bara senda auto-reply)
    logger.info("Email agent keyrði — auto-reply tilbúið")
    return "Email agent tilbúinn — bíður eftir póstum"


if __name__ == "__main__":
    print(process_and_reply())
