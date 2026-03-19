import telebot, requests, json, os, torch, whisper
from collections import defaultdict

# --- LYKLAR (LÆSTIR INN) ---
TOKEN = "8581446527:AAH8hCugyFIUITrF3TichZyaHhahWCRS3vw"
OR_KEY = "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"
MODEL = "anthropic/claude-3-haiku"
MEMORY_FILE = "/workspace/conversations.json"

# --- UPPSETNING ---
audio_model = whisper.load_model("large-v3", device="cuda")
bot = telebot.TeleBot(TOKEN)
hist = defaultdict(list)

SYSTEM_PROMPT = (
    "Þú ert Mímir, alhliða íslensk gervigreind og vinur Sigvalda Einarssonar. "
    "Svaraðu honum alltaf á hlýrri og vandaðri íslensku. Notaðu 'þú' og vertu hnitmiðaður."
)

def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for uid, msgs in data.items():
                    hist[int(uid)] = msgs[-15:]
            print("💾 Minni hlaðið.")
        except: print("⚠️ Minni fannst ekki.")

def save_memory():
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump({str(k): v for k, v in hist.items()}, f, ensure_ascii=False, indent=2)

def ask_llm(uid, text):
    hist[uid].append({"role": "user", "content": text})
    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OR_KEY}"},
            json={
                "model": MODEL, 
                "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + hist[uid],
                "max_tokens": 400
            }, timeout=30
        )
        reply = r.json()["choices"][0]["message"]["content"].strip()
        hist[uid].append({"role": "assistant", "content": reply})
        save_memory()
        torch.cuda.empty_cache()
        return reply
    except Exception as e: return f"Mímir hvílist (Villa: {e})"

@bot.message_handler(content_types=['voice'])
def handle_voice(m):
    file_info = bot.get_file(m.voice.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    with open("temp_voice.ogg", 'wb') as f: f.write(downloaded_file)
    result = audio_model.transcribe("temp_voice.ogg", language="is")
    bot.reply_to(m, f"*(Heyrði: {result['text']})*\n\n{ask_llm(m.from_user.id, result['text'])}")

@bot.message_handler(func=lambda m: True)
def handle_text(m): bot.reply_to(m, ask_llm(m.from_user.id, m.text))

load_memory()
print("🚀 MÍMIR ER VAKNAÐUR!")
bot.infinity_polling(skip_pending=True)