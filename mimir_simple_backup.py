import os
import requests
import whisper
import torch
import json
from telebot import TeleBot
from collections import defaultdict
from dotenv import load_dotenv
from datetime import datetime

# 1. UPPSETNING OG LYKLAR
load_dotenv('/workspace/mimir_net/config/.env')
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OR_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "anthropic/claude-3-haiku"

# 2. HLAÐA WHISPER (EYRUN)
print("👂 Hleð Whisper large-v3 á GPU... Þetta tekur um 30-60 sekúndur.")
audio_model = whisper.load_model("large-v3", device="cuda")

bot = TeleBot(TOKEN)
hist = defaultdict(list)

def ask_llm(uid, text):
    """Sér um rökhugsun Mímis og samskipti við OpenRouter"""
    # Bæta við því sem Sigvaldi sagði í minnið
    hist[uid].append({"role": "user", "content": text})
    
    # Halda sögunni hæfilegri (síðustu 10 skilaboð)
    if len(hist[uid]) > 10: 
        hist[uid] = hist[uid][-10:]
    
    # --- STRÖNG SJÁLFSVITUND ---
    # Hér segjum við honum nákvæmlega hver hann er og hver þú ert
    system_prompt = (
        "Þú ert Mímir, alhliða íslensk gervigreind. "
        "Manneskjan sem þú ert að tala við NÚNA heitir Sigvaldi Einarsson. "
        "Sigvaldi er skapari þinn og meistari. "
        "Þú átt ALLTAF að ávarpa hann sem Sigvalda eða vin og svara honum af virðingu, "
        "hlýju og vitsmunum. Svaraðu alltaf á vandaðri íslensku. "
        "Vertu hnitmiðaður en kláraðu alltaf hugsanir þínar."
    )

    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OR_KEY}"},
            json={
                "model": MODEL,
                "messages": [{"role": "system", "content": system_prompt}] + hist[uid],
                "max_tokens": 450,  # Nóg af bensíni svo hann klippi ekki af sér málið
                "temperature": 0.7
            }, 
            timeout=30
        )
        
        res = r.json()
        if "choices" in res:
            reply = res["choices"][0]["message"]["content"].strip()
            
            # MIKILVÆGT: Bæta svari Mímis við minnið svo hann muni hvað hann sagði
            hist[uid].append({"role": "assistant", "content": reply})
            return reply
        else:
            print(f"⚠️ API Villa: {res}")
            return "Mímir þarf stutta hvíld (API villa)."
            
    except Exception as e:
        print(f"❌ Tengivilla: {e}")
        return "Ég náði ekki sambandi við heilann minn í bili."

# 3. HANDVERK FYRIR RADDSKEYTI (VOICE)
@bot.message_handler(content_types=['voice'])
def handle_voice(m):
    print("🎤 Fékk raddskeyti frá Sigvalda, vinn úr því...")
    try:
        # Sækja skrána frá Telegram
        file_info = bot.get_file(m.voice.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Vista tímabundið
        with open("temp_voice.ogg", 'wb') as f:
            f.write(downloaded_file)
        
        # Whisper breytir hljóði í íslenskan texta
        result = audio_model.transcribe("temp_voice.ogg", language="is")
        user_text = result["text"]
        print(f"🗣️ Sigvaldi sagði: {user_text}")
        
        # Senda textann í LLM heilann
        reply = ask_llm(m.from_user.id, user_text)
        
        # Svara í Telegram
        bot.reply_to(m, f"*(Heyrði: {user_text})*\n\n{reply}")
        
    except Exception as e:
        print(f"❌ Villa í raddvinnslu: {e}")
        bot.reply_to(m, "Mér tókst ekki að heyra alveg hvað þú sagðir, meistari.")

# 4. HANDVERK FYRIR TEXTA (TEXT)
@bot.message_handler(func=lambda m: True)
def handle_text(m):
    reply = ask_llm(m.from_user.id, m.text)
    bot.reply_to(m, reply)

# 5. RÆSING
print("-" * 30)
print("🚀 MÍMIR ALHLIÐA ER VAKNAÐUR!")
print("👉 Hann þekkir Sigvalda og hlustar á raddir.")
print("-" * 30)

bot.infinity_polling(skip_pending=True)