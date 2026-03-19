from mimir_logger import log_conversation
import telebot, requests, os, subprocess
import whisper
from collections import defaultdict
from mimir_net.agents.meta_agent import graph

TOKEN = "8581446527:AAHjeOCY90XzTNgmzElaiaKL_SgOvDVuag0"
bot = telebot.TeleBot(TOKEN)
model = whisper.load_model("large-v3")
conversation_history = defaultdict(list)

SYSTEM_PROMPT = """Þú ert Mímir, íslenskur AI aðstoðarmaður Sigvalda Einarssonar.

REGLUR:
- Svaraðu ALLTAF á íslensku
- Vertu STUTTUR og náttúrulegur - eins og vinur í spjalli
- Hámark 2-3 setningar í venjulegu spjalli
- Ekki ofgreina eða útskýra of mikið
- Man eftir nafni notanda og notar það
- Hlý og persónuleg tón
- Ef spurning er flókin, spurðu til baka frekar en að skrifa langa grein
"""

def ask_llm(user_id, t):
    if not t or not str(t).strip():
        return "Fyrirgefðu, ég skildi ekki."
    history = conversation_history[user_id]
    history.append({"role": "user", "content": str(t)})
    if len(history) > 20:
        history = history[-20:]
    result = graph.invoke({
        "task": str(t),
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + history,
        "result": ""
    })
    reply = result.get("result", "Fyrirgefðu, ég fann ekki svar.").strip()
    history.append({"role": "assistant", "content": reply})
    conversation_history[user_id] = history
    log_conversation(user_id, t, reply)
    return reply

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
        full = f"🎤 '{text}'\n\n{reply}"
        bot.reply_to(m, full[:3900] + "..." if len(full) > 3900 else full)
    except Exception as e:
        bot.reply_to(m, f"Villa: {e}")

@bot.message_handler(func=lambda m: True)
def handle_text(m):
    bot.reply_to(m, "Mímir hugsar...")
    print(f"CHAT_ID: {m.chat.id}", flush=True)
    reply = ask_llm(m.from_user.id, m.text)
    bot.reply_to(m, reply[:3900] + "..." if len(reply) > 3900 else reply)

print("Mímir v2 vaknaður! LangGraph heilinn virkur! 🧠")


bot.infinity_polling(skip_pending=False)
