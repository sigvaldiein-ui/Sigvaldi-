import telebot, requests, os, subprocess
import whisper
from collections import defaultdict

TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENROUTER_KEY = os.environ.get("OPENROUTER_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

bot = telebot.TeleBot(TOKEN)
model = whisper.load_model("large-v3")

# Samtalsminnir - man síðustu 20 skilaboð per notanda
conversation_history = defaultdict(list)

SYSTEM_PROMPT = "Þú ert Mímir, íslenskur AI aðstoðarmaður. Svaraðu alltaf á íslensku. Þú ert gáfaður, hjálpsamur og hlý. Þú keyrir á RunPod server. Ef spurt er um endurræsingu: opna JupyterLab terminal, .bashrc ræsir þig sjálfkrafa, eða keyra: bash /workspace/start_all.sh"

def ask_llm(user_id, t):
    if not t or not str(t).strip():
        return "Fyrirgefðu, ég skildi ekki."
    history = conversation_history[user_id]
    history.append({"role": "user", "content": str(t)})
    if len(history) > 20:
        history = history[-20:]
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history
    h = {"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"}
    p = {"model": "openai/gpt-4o-mini", "messages": messages, "max_tokens": 1024}
    try:
        r = requests.post(OPENROUTER_URL, headers=h, json=p, timeout=30)
        result = r.json()["choices"][0]["message"]["content"]
        reply = result.strip() if result else "Fyrirgefðu, ég fann ekki svar."
        history.append({"role": "assistant", "content": reply})
        conversation_history[user_id] = history
        return reply
    except Exception as e:
        return f"Villa: {e}"

@bot.message_handler(content_types=["voice"])
def handle_voice(m):
    bot.reply_to(m, "Mímir hlustar...")
    try:
        f = bot.get_file(m.voice.file_id)
        url = f"https://api.telegram.org/file/bot{TOKEN}/{f.file_path}"
        ogg = "/tmp/voice.ogg"
        mp3 = "/tmp/voice.mp3"
        subprocess.run(["wget", "-q", "-O", ogg, url])
        subprocess.run(["ffmpeg", "-y", "-i", ogg, mp3], capture_output=True)
        result = model.transcribe(mp3, language="is", initial_prompt="Þetta er íslenskt tal. Skráðu nákvæmlega það sem sagt er á íslensku.")
        text = result["text"].strip()
        if not text:
            bot.reply_to(m, "Fyrirgefðu, ég heyrði ekki vel.")
            return
        reply = ask_llm(m.from_user.id, text)
        bot.reply_to(m, f"🎤 '{text}'\n\n{reply}")
    except Exception as e:
        bot.reply_to(m, f"Villa: {e}")

@bot.message_handler(func=lambda m: True)
def handle_text(m):
    bot.reply_to(m, "Mímir hugsar...")
    print(f"CHAT_ID: {m.chat.id}", flush=True)
    reply = ask_llm(m.from_user.id, m.text)
    bot.reply_to(m, reply)

print("Mímir vaknaður!")
bot.infinity_polling(skip_pending=True)
