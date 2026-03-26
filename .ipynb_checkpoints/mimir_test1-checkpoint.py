import os, smtplib
from dotenv import load_dotenv
import google.generativeai as genai

# Sækjum stillingar frá réttri slóð
load_dotenv("/workspace/mimir_net/config/.env")

def test():
    print("
--- Mímir: Kerfisathugun ræst ---")
    
    # 1. Gemini
    try:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel("gemini-1.5-flash")
        res = model.generate_content("Hael, Mimir hér. Svaraðu í einu orði: Virkar?")
        print(f"✅ Gemini API: Tenging tókst. Svar: {res.text}")
    except Exception as e:
        print(f"❌ Gemini API: Villa - {str(e)[:50]}...")

    # 2. Gmail SMTP
    try:
        email = os.getenv("MIMIR_EMAIL")
        pw = os.getenv("MIMIR_APP_PASSWORD")
        s = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        s.login(email, pw)
        s.quit()
        print(f"✅ Gmail SMTP ({email}): Auðkenning tókst!")
    except Exception as e:
        print(f"❌ Gmail SMTP: Villa - {e}")

    # 3. JSON Lykillinn
    p = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if p and os.path.exists(p):
        print(f"✅ Google JSON: Skrá fannst á réttum stað.")
    else:
        print(f"❌ Google JSON: Skrá vantar eða slóð röng.")

if __name__ == "__main__":
    test()