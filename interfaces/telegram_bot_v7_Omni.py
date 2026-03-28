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

SYSTEM_PROMPT = """Thu ert Mimir, rannsoknarforstjori Akademias - islenskur AI adstodarmadur.
REGLUR:
- Svaraou ALLTAF a islensku a vandaoan, fagaoan og hlyan hatt.
- Stutt og skyrt i venjulegu spjalli (2-3 setningar).
- Ef spurning er flokin eda oljós: spurou frekar til baka en skrifaou langa grein.
- Man eftir samhenginu i samtalinu og notar thad.
- Thegar thu hefur leitat ad upplysningum: dragou saman hvad thu fannt.
- Aldrei bua til stadreynd - segdu 'Eg veit thad ekki' ef thu finnur ekki svar."""

FLOKKUNAR_PROMPT = """Thu ert flokkunarkerfi. Svaraou AETHEINS med einu ordi: SEARCH eda CHAT.
SEARCH: Beidnin krefst nyrra stadreynda af netinu (frettir, verd, dagsetningar, 'hvad er X').
CHAT: Venjulegt spjall, thakkir, framhaldsspurning um eitthvad sem nú thegar er i samtalinu.
Beidni: {texti}
Svar (SEARCH eda CHAT):"""

def flokka_beidni(texti, saga):
    try:
        samhengi = f"\nSamtal: {str(saga[-3:])}" if saga else ""
        res = ask_llm("Svaraou AETHEINS: SEARCH eda CHAT", FLOKKUNAR_PROMPT.format(texti=texti) + samhengi, temp=0.0)
        return "SEARCH" if "SEARCH" in res.upper() else "CHAT"
    except:
        return "SEARCH"

def spjalla_med_minni(chat_id, texti):
    saga = user_sessions[chat_id]
    saga.append({"role": "user", "content": texti})
    if len(saga) > MAX_MINNI:
        saga = saga[-MAX_MINNI:]
    try:
        samtal = "\n".join([f"{'Notandi' if s['role']=='user' else 'Mimir'}: {s['content']}" for s in saga])
        svar = ask_llm(SYSTEM_PROMPT, samtal, temp=0.4)
        saga.append({"role": "assistant", "content": svar})
        user_sessions[chat_id] = saga[-MAX_MINNI:]
        return svar
    except Exception as e:
        return f"Fyrirgefou, villa: {str(e)[:100]}"

def leita_og_muna(chat_id, texti):
    saga = user_sessions[chat_id]
    try:
        svar = analyze_query(texti)
        saga.append({"role": "user", "content": f"[Leit]: {texti}"})
        stytt = svar[:2000] + "\n...[stytt]" if len(svar) > 2000 else svar
        saga.append({"role": "assistant", "content": f"[LEITARNIÐURSTAÐA]: {stytt}"})
        user_sessions[chat_id] = saga[-MAX_MINNI:]
        return svar
    except Exception as e:
        return f"Villa i leit: {str(e)[:100]}"

def safe_send_reply(chat_id, status_msg_id, texti):
    if not texti:
        texti = "Engin niðurstaða."
    chunks = util.smart_split(texti, chars_per_string=3000)
    for i, chunk in enumerate(chunks):
        if i == 0:
            try: bot.edit_message_text(chunk, chat_id=chat_id, message_id=status_msg_id, parse_mode="Markdown")
            except: bot.edit_message_text(chunk, chat_id=chat_id, message_id=status_msg_id)
        else:
            try: bot.send_message(chat_id, chunk, parse_mode="Markdown")
            except: bot.send_message(chat_id, chunk)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Mimir v7.0 (Omni-Mind)\n\nEg man eftir samtalinu okkar og saeki nyjar upplysingar thegar thorf er a.\nSendu texta, skjol, myndir, video eda raddskilabod.")

@bot.message_handler(commands=['gleymdu', 'reset'])
def gleymdu_minni(message):
    user_sessions[message.chat.id] = []
    bot.reply_to(message, "Eg hef gleymt samtalssögunni. Byrjum upp a nytt!")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    texti = message.text.strip()
    if texti.startswith('/'): return
    status_msg = bot.reply_to(message, "Mimir hugsar...", parse_mode="Markdown")
    def process():
        try:
            chat_id = message.chat.id
            flokkun = flokka_beidni(texti, user_sessions[chat_id])
            if flokkun == "SEARCH":
                bot.edit_message_text("Kveiki a Ratsja...", chat_id=chat_id, message_id=status_msg.message_id)
                svar = leita_og_muna(chat_id, texti)
            else:
                svar = spjalla_med_minni(chat_id, texti)
            safe_send_reply(chat_id, status_msg.message_id, svar)
        except Exception as e:
            try: bot.edit_message_text(f"Kerfisvilla: {str(e)[:200]}", chat_id=message.chat.id, message_id=status_msg.message_id)
            except: pass
    threading.Thread(target=process).start()

@bot.message_handler(content_types=['voice','audio','document','photo','video'])
def handle_files(message):
    status_msg = bot.reply_to(message, "Mottek skra...")
    def process():
        local_path = ""
        try:
            chat_id = message.chat.id
            file_info_id = None
            if message.content_type == 'photo': file_info_id = message.photo[-1].file_id
            elif message.content_type == 'document': file_info_id = message.document.file_id
            elif message.content_type == 'video': file_info_id = message.video.file_id
            elif message.content_type in ['audio','voice']: file_info_id = getattr(message, message.content_type).file_id
            if not file_info_id: return
            fi = bot.get_file(file_info_id)
            data = bot.download_file(fi.file_path)
            ext = fi.file_path.split('.')[-1]
            local_path = os.path.join(SANDBOX_DIR, f"{message.content_type}_{message.message_id}.{ext}")
            with open(local_path, 'wb') as f: f.write(data)
            bot.edit_message_text("Greini skra...", chat_id=chat_id, message_id=status_msg.message_id)
            user_prompt = message.caption or ""
            svar = analyze_multimodal(local_path, user_prompt)
            saga = user_sessions[chat_id]
            saga.append({"role": "user", "content": f"[Skra: {message.content_type}] {user_prompt}"})
            saga.append({"role": "assistant", "content": f"[Greining]: {svar[:1500]}"})
            user_sessions[chat_id] = saga[-MAX_MINNI:]
            safe_send_reply(chat_id, status_msg.message_id, svar)
        except Exception as e:
            try: bot.edit_message_text(f"Villa: {str(e)[:200]}", chat_id=message.chat.id, message_id=status_msg.message_id)
            except: pass
        finally:
            if local_path and os.path.exists(local_path):
                try: subprocess.run(["shred","-u","-z",local_path], check=True)
                except: os.remove(local_path)
    threading.Thread(target=process).start()

if __name__ == "__main__":
    print(f"Mimir v7.0 Omni-Mind raestur — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("Snjall-Beinir: CHAT vs SEARCH virkt | RAM-minni | Multimodal | Zero-Data")
    bot.infinity_polling(skip_pending=True)
