import os
import smtplib
from dotenv import load_dotenv
import google.generativeai as genai

# 1. Hlaða inn stillingum frá algildri slóð samkvæmt SOP
env_path = "/workspace/mimir_net/config/.env"
load_dotenv(env_path)

def test_config():
    print("\n" + "="*40)
    print("   MÍMIR: KERFISATHUGUN (RÆSING)   ")
    print("="*40)
    
    # --- PRÓF 1: Gemini API (Alhliða gervigreind) ---
    gemini_key = os.getenv("GEMINI_API_KEY")
    print(f"\n[1] Athuga Gemini API...")
    try:
        if not gemini_key:
            raise ValueError("Lykill fannst ekki í .env skrá!")
            
        genai.configure(api_key=gemini_key)
        
        # Notum 'gemini-flash-latest' sem er staðfest virkt í þínu umhverfi
        model = genai.GenerativeModel('gemini-flash-latest')
        response = model.generate_content("Hæ Mímir, staðfestu tengingu í einu orði.")
        
        print(f"✅ Gemini API: Virkar! Svar: {response.text.strip()}")
    except Exception as e:
        print(f"❌ Gemini API: Villa - {e}")

    # --- PRÓF 2: Gmail SMTP (Mímir kerfisreikningur) ---
    email = os.getenv("MIMIR_EMAIL")
    password = os.getenv("MIMIR_APP_PASSWORD")
    print(f"\n[2] Athuga Gmail SMTP ({email})...")
    try:
        if not email or not password:
            raise ValueError("Auðkenni vantar í .env skrá!")
            
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(email, password)
        server.quit()
        print(f"✅ Gmail SMTP: Auðkenning tókst!")
    except Exception as e:
        print(f"❌ Gmail SMTP: Villa - {e}")

    # --- PRÓF 3: Google JSON Skilríki (Drive/Cloud) ---
    json_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    print(f"\n[3] Athuga Google JSON skrá...")
    if json_path and os.path.exists(json_path):
        print(f"✅ Google JSON: Skrá fannst á réttum stað.")
    else:
        print(f"❌ Google JSON: Skrá vantar eða slóð er röng!")

    print("\n" + "="*40)
    print("      ATHUGUN LOKIÐ - KERFI KLÁRT      ")
    print("="*40 + "\n")

if __name__ == "__main__":
    test_config()