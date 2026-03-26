import os
import sys
import threading
import telebot
import requests
from dotenv import load_dotenv

# 1. SOP: Samstilla slóðir og hlaða eldsneyti
BASE_DIR = "/workspace"
sys.path.append(os.path.join(BASE_DIR, "mimir_net"))
load_dotenv(os.path.join(BASE_DIR, ".env"))

TOKEN = os.getenv('TELEGRAM_TOKEN')
OR_KEY = os.getenv('OPENROUTER_API_KEY')

# Öryggisventill: Stöðva ef tankurinn er tómur
if not TOKEN or not OR_KEY:
    print(f"❌ VILLA: Lykla vantar í .env skrána!")
    sys.exit(1)

# Ræsum TeleBot (notum 10 þræði fyrir samhliða vinnslu)
bot = telebot.TeleBot(TOKEN, num_threads=10)

# 2. Tenging við Höllina (Skills)
try:
    from skills.drive_reader import MimirVision
    vision = MimirVision()
    VISION_READY = True
    print("✅ MimirVision tengt við Höllina.")
except Exception as e:
    VISION_READY = False
    print(f"⚠️ MimirVision ekki virkt: {e}")

# 3. Greindin (OpenRouter / Gemini)
def analyze_with_llm(text_content, user_question):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OR_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "google/gemini-2.0-flash-001",
        "messages": [
            {"role": "system", "content": "Þú ert Mímir v3.5. Svaraðu á kjarnyrtri íslensku byggt á gögnunum."},
            {"role": "user", "content": f"GÖGN ÚR HÖLLINNI:\n---\n{text_content[:700000]}\n---\n\nSPURNING: {user_question}"}
        ],
        "temperature": 0.2
    }
    response = requests.post(url, headers=headers, json=payload, timeout=120)
    return response.json()["choices"][0]["message"]["content"]

# 4. Skipanir (Söludeildin)
@bot.message_handler(commands=['start', 'restart'])
def welcome(message):
    bot.reply_to(message, "🏛️ **Mímir v3.5 ONLINE.**\n\n"
                          "👉 `/skjol` - Sjá gögn í Höllinni\n"
                          "👉 `/spurning skjal | spurning` - Rýna í gögn", parse_mode="Markdown")

@bot.message_handler(commands=['skjol'])
def handle_skjol(message):
    if not VISION_READY: return bot.reply_to(message, "❌ Höllin er lokuð.")
    msg = bot.reply_to(message, "⏳ *Fletti upp í Höllinni...*", parse_mode="Markdown")
    try:
        files = vision.list_pdfs()
        svar = "📂 **Gögn tiltæk:**\n\n" + "\n".join([f"📄 `{f['name']}`" for f in files])
        bot.edit_message_text(svar, message.chat.id, msg.message_id, parse_mode="Markdown")
    except Exception as e:
        bot.edit_message_text(f"❌ Villa: {e}", message.chat.id, msg.message_id)

@bot.message_handler(commands=['spurning'])
def handle_spurning(message):
    input_text = message.text.replace("/spurning", "").strip()
    if "|" not in input_text: 
        return bot.reply_to(message, "⚠️ Notaðu: `/spurning skjal | spurning`")
    
    skjal_nafn, spurning = [i.strip() for i in input_text.split("|", 1)]
    status = bot.reply_to(message, f"⏳ 1/3: Leita að `{skjal_nafn}`...", parse_mode="Markdown")

    def worker():
        try:
            bot.edit_message_text("📥 2/3: Les úr Höllinni...", message.chat.id, status.message_id)
            # Kallar á read_pdf í drive_reader.py
            content = vision.read_pdf(skjal_nafn)
            
            bot.edit_message_text("🧠 3/3: Mímir rýnir í gögnin...", message.chat.id, status.message_id)
            answer = analyze_with_llm(content, spurning)
            
            bot.edit_message_text(f"🤖 **Mímir svarar:**\n\n{answer}", message.chat.id, status.message_id, parse_mode="Markdown")
        except Exception as e:
            bot.edit_message_text(f"❌ Villa: {str(e)}", message.chat.id, status.message_id)

    threading.Thread(target=worker).start()

if __name__ == "__main__":
    print("🚀 Mímir v3.5 ræstur. Hlustar á skipanir...")
    bot.infinity_polling(skip_pending=True)