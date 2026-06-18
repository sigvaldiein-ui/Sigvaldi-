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

Takk fyrir að gefa Alvitri tækifæri. Hér er aðgangslykillinn þinn:

AÐGANGSLYKILL:
{url}

Þennan lykil notarðu til að skrá þig inn á alvitur.is/login (flipinn „Aðgangslykill").

---

Alvitur.is er eins manns framtak, styrkt af erlendu tæknifyrirtæki sem gerir okkur kleift að hafa afnot af öflugri tölvu til að keyra kerfið á. Verkefnið er unnið af fullum krafti en reksturinn er viðkvæmur og því þarf að halda vel utan um fjármagnið.

Með netfanginu þínu hefur þú aðgang að:
- 20 fyrirspurnum á dag í Vitann og Hvelfinguna
- Vefleit — leitað á netinu með heimildum

Næstu skref (koma fljótlega):
- Stórmeistarinn — öflugustu mállíkön heims svara spurningunum þínum
- Erindrekinn — stafrænn starfsmaður sem framkvæmir verk fyrir þig

Ef þú vilt sjá Alvitur lifa og dafna geturðu styrkt verkefnið með því að smella á „Styðja verkefnið" í valstikunni. Hver króna fer beint í að halda þessu gangandi.

Kveðja,
Alvitur teymið

---
Þessi póstur var sendur á netfangið þitt vegna skráningar á alvitur.is. Ef þú vilt ekki fá frekari tölvupósta skaltu svara þessum pósti með orðinu „hætta".
"""
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = "Alvitur — þú ert komin/n inn 🐢🇮🇸"
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
