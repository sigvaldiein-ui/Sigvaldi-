#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, threading, subprocess
from collections import defaultdict
from datetime import datetime
import telebot
from telebot import util
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(BASE_DIR)
from core.agent_core_v4 import analyze_query, ask_llm
from skills.multimodal_reader import analyze_multimodal

load_dotenv(os.path.join(BASE_DIR, 'config', '.env'))
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN') or os.getenv('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=True, num_threads=5)
SANDBOX_DIR = os.path.join(BASE_DIR, "sandbox")
os.makedirs(SANDBOX_DIR, exist_ok=True)

MAX_MINNI = 10
user_sessions = defaultdict(list)
memory_lock = threading.Lock()

SYSTEM_PROMPT = """Thu ert Mimir, rannsoknarforstjori Akademias - islenskur AI adstodarmadur.
REGLUR: Svaraou ALLTAF a islensku. Stutt og skyrt. Manst eftir samhengi. Aldrei bua til stadreyndir."""

FLOKKUNAR_PROMPT = """Thu ert nakvamt flokkunarkerfi. Svaraou AETHEINS med einu ordi: SEARCH eda CHAT.
Daemi 1: "Saell Mimir, eg heiti Sigvaldi." -> CHAT
Daemi 2: "Hvad er nyjaста skjakortid fra NVIDIA?" -> SEARCH
Daemi 3: "Hver er stan a hlutabrefum Tesla i dag?" -> SEARCH
Daemi 4: "Geturdu dregid thessa ritgerd saman?" -> CHAT
Daemi 5: "Hvad sagdi eg ao eg heti adan?" -> CHAT
Daemi 6: "Finndu nyjastu frettir um gervigreind." -> SEARCH
Regla: Ef spurning krefst nyrra stadreynd um fyrirtaeki, vorur, frettir eda taekni: SEARCH. Jafnvel thott thu haldur ao thu vitir! Annars CHAT.
Beidni: {texti}
Svar (SEARCH eda CHAT):"""

def flokka_beidni(texti):
    try:
        res = ask_llm("Svaraou AETHEINS: SEARCH eda CHAT", FLOKKUNAR_PROMPT.format(texti=texti), temp=0.0)
        return "CHAT" if "CHAT" in res.upper() else "SEARCH"
    except: return "SEARCH"

def get_history(chat_id):
    with memory_lock: return list(user_sessions[chat_id])

def add_memory(chat_id, role, content):
    with memory_lock:
        user_sessions[chat_id].append({"role": role, "content": content})
        if len(user_sessions[chat_id]) > MAX_MINNI: del user_sessions[chat_id][0]

def spjalla(chat_id, texti):
    add_memory(chat_id, "user", texti)
    saga = get_history(chat_id)
    samtal = "\n".join([f"{'Notandi' if s['role']=='user' else 'Mimir'}: {s['content']}" for s in saga])
    try:
        svar = ask_llm(SYSTEM_PROMPT, samtal, temp=0.4)
        add_memory(chat_id, "assistant", svar)
        return svar
    except Exception as e: return f"Villa: {str(e)[:100]}"

def leita(chat_id, texti):
    add_memory(chat_id, "user", f"[Leit]: {texti}")
    try:
        svar = analyze_query(texti)
        add_memory(chat_id, "assistant", f"[LEITARNIÐURSTAÐA]: {svar[:1500]}")
        return svar
    except Exception as e: return f"Villa i leit: {str(e)[:100]}"

def safe_reply(chat_id, msg_id, texti):
    if not texti: texti = "Engin nidurstaeda."
    chunks = util.smart_split(texti, chars_per_string=3000)
    for i, chunk in enumerate(chunks):
        try:
            if i == 0: bot.edit_message_text(chunk, chat_id=chat_id, message_id=msg_id, parse_mode="Markdown")
            else: bot.send_message(chat_id, chunk, parse_mode="Markdown")
        except:
            if i == 0: bot.edit_message_text(chunk, chat_id=chat_id, message_id=msg_id)
            else: bot.send_message(chat_id, chunk)

@bot.message_handler(commands=['start','help'])
def welcome(m): bot.reply_to(m, "Mimir v7.1 Omni-Mind - Minnis-Las og Few-Shot Beinir virkur!")

@bot.message_handler(commands=['gleymdu','reset'])
def gleymdu(m):
    with memory_lock: user_sessions[m.chat.id].clear()
    bot.reply_to(m, "Minni hreinsad. Byrjum upp a nytt!")

@bot.message_handler(content_types=['text'])
def handle_text(m):
    texti = m.text.strip()
    if texti.startswith('/'): return
    sm = bot.reply_to(m, "Mimir hugsar...")
    def run():
        try:
            cid = m.chat.id
            if flokka_beidni(texti) == "SEARCH":
                bot.edit_message_text("Kveiki a Ratsja...", chat_id=cid, message_id=sm.message_id)
                svar = leita(cid, texti)
            else: svar = spjalla(cid, texti)
            safe_reply(cid, sm.message_id, svar)
        except Exception as e:
            try: bot.edit_message_text(f"Kerfisvilla: {str(e)[:200]}", chat_id=m.chat.id, message_id=sm.message_id)
            except: pass
    threading.Thread(target=run).start()

@bot.message_handler(content_types=['voice','audio','document','photo','video'])
def handle_files(m):
    sm = bot.reply_to(m, "Mottek skra...")
    def run():
        lp = ""
        try:
            cid = m.chat.id
            fid = m.photo[-1].file_id if m.content_type=='photo' else getattr(m, m.content_type).file_id
            fi = bot.get_file(fid)
            data = bot.download_file(fi.file_path)
            lp = os.path.join(SANDBOX_DIR, f"{m.content_type}_{m.message_id}.{fi.file_path.split('.')[-1]}")
            with open(lp,'wb') as f: f.write(data)
            bot.edit_message_text("Greini skra...", chat_id=cid, message_id=sm.message_id)
            svar = analyze_multimodal(lp, m.caption or "")
            add_memory(cid, "user", f"[Skra: {m.content_type}]")
            add_memory(cid, "assistant", f"[Greining]: {svar[:1500]}")
            safe_reply(cid, sm.message_id, svar)
        except Exception as e:
            try: bot.edit_message_text(f"Villa: {str(e)[:200]}", chat_id=m.chat.id, message_id=sm.message_id)
            except: pass
        finally:
            if lp and os.path.exists(lp):
                try: subprocess.run(["shred","-u","-z",lp], check=True)
                except: os.remove(lp)
    threading.Thread(target=run).start()

if __name__ == "__main__":
    print(f"Mimir v7.1 raestur — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("Thread-Safe minni og Few-Shot Beinir virkur!")
    bot.infinity_polling(skip_pending=True)
