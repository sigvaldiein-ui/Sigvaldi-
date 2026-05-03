#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools.py
--------
Mimir verkfaeri - timi og toluvpostur
Uppfaert skv. SOP v5.0 og urskurdi Adals Arkitektsins

Reglur:
- ALDREI hardkoda netfong eda lykilord - alltaf ur .env
- Alltaf try/except - villa kraschar aldrei hradinn
- sigvaldimimir@gmail.com er Mimis vinnunetfang
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import zoneinfo
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv('/workspace/.env')


@tool
def get_current_time(query: str = "") -> str:
    """Skilar nakvamri dagsetningu og tima a Islandi."""
    try:
        tz = zoneinfo.ZoneInfo("Atlantic/Reykjavik")
    except Exception:
        tz = zoneinfo.ZoneInfo("UTC")
    now = datetime.now(tz)
    dagar = ["Manudagur","Gridudagur","Midvikudagur","Fimmtudagur","Fostudagur","Laugardagur","Sunnudagur"]
    manudir = ["januar","februar","mars","april","mai","juni","juli","agust","september","oktober","november","desember"]
    return (f"I dag er {dagar[now.weekday()]}, {now.day}. {manudir[now.month-1]} {now.year}. "
            f"Klukkan a Islandi er nakvaemlega {now.strftime('%H:%M:%S')}.")


@tool
def send_email(to_address: str, subject: str, body: str) -> str:
    """Sendir toluvpost i gegnum Mimis vinnunetfang (sigvaldimimir@gmail.com)."""
    # Saekja skilriki ur .env - aldrei hardkodad
    sender = os.getenv("MIMIR_EMAIL_USER")
    password = os.getenv("MIMIR_EMAIL_PASS")

    if not sender or not password:
        return "Villa: MIMIR_EMAIL_USER eda MIMIR_EMAIL_PASS vantar i .env"

    try:
        msg = MIMEMultipart()
        msg['From'] = f"Mimir AI <{sender}>"
        msg['To'] = to_address
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        # Port 587 med STARTTLS - skv. urskurdi Adals
        with smtplib.SMTP('smtp.gmail.com', 587, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(sender, password)
            server.send_message(msg)

        return f"Toluvpostur sendur a {to_address}!"

    except smtplib.SMTPAuthenticationError:
        return "Villa: App Password ranlegt eda urunnid. Bua til nytt a myaccount.google.com/apppasswords"
    except smtplib.SMTPRecipientsRefused:
        return f"Villa: Netfangid {to_address} hafnadi postinum."
    except smtplib.SMTPException as e:
        return f"Villa i SMTP: {str(e)[:200]}"
    except TimeoutError:
        return "Villa: Gmail SMTP svarar ekki (timeout)."
    except Exception as e:
        return f"Ovaent villa: {str(e)[:200]}"


if __name__ == "__main__":
    print(get_current_time.invoke({}))
    print("tools.py tilbuin")
