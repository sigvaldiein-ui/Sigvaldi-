import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import zoneinfo
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv('/workspace/mimir_net/config/.env')

@tool
def get_current_time(query: str = "") -> str:
    """Skilar nákvæmri dagsetningu og tíma á Íslandi."""
    try:
        tz = zoneinfo.ZoneInfo("Atlantic/Reykjavik")
    except:
        tz = zoneinfo.ZoneInfo("UTC")
    now = datetime.now(tz)
    dagar = ["Mánudagur", "Þriðjudagur", "Miðvikudagur", "Fimmtudagur", "Föstudagur", "Laugardagur", "Sunnudagur"]
    manudir = ["janúar", "febrúar", "mars", "apríl", "maí", "júní", "júlí", "ágúst", "september", "október", "nóvember", "desember"]
    return f"Í dag er {dagar[now.weekday()]}, {now.day}. {manudir[now.month - 1]} {now.year}. Klukkan á Íslandi er nákvæmlega {now.strftime('%H:%M:%S')}."

@tool
def send_email(to_address: str, subject: str, body: str) -> str:
    """Sendir tölvupóst í gegnum sigvaldiein@gmail.com."""
    sender_email = "sigvaldiein@gmail.com" 
    app_password = os.getenv("GMAIL_SEND_PASSWORD") 
    if not app_password:
        return "❌ Villa: GMAIL_SEND_PASSWORD vantar í .env."
    msg = MIMEMultipart()
    msg['From'] = f"Mímir AI <{sender_email}>"
    msg['To'] = to_address
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, app_password)
            server.send_message(msg)
        return f"✅ Tölvupóstur sendur á {to_address}!"
    except Exception as e:
        return f"❌ Mistókst að senda póst: {str(e)}"