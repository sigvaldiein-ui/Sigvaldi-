import os
import sys
import telebot
from telebot import util
import threading
import subprocess
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(BASE_DIR)

from core.agent_core_v4 import analyze_query
from skills.multimodal_reader import analyze_multimodal

load_dotenv(os.path.join(BASE_DIR, 'config', '.env'))
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN') or os.getenv('TELEGRAM_TOKEN')

bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=True, num_threads=5)
SANDBOX_DIR = os.path.join(BASE_DIR, "sandbox")
os.makedirs(SANDBOX_DIR, exist_ok=True)

def safe_send_reply(chat_id, status_msg_id, text):
    """Snjall-Bútari: Brýtur löng svör snyrtilega niður og grípur Markdown villur!"""
    if not text:
        text = "❌ Engin niðurstaða fékkst úr greiningu."
    chunks = util.smart_split(text, chars_per_string=3000)
    for i, chunk in enumerate(chunks):
        if i == 0:
            try: bot.edit_message_text(chunk, chat_id=chat_id, message_id=status_msg_id, parse_mode="Markdown")
            except Exception: bot.edit_message_text(chunk, chat_id=chat_id, message_id=status_msg_id)
        else:
            try: bot.send_message(chat_id, chunk, parse_mode="Markdown")
            except Exception: bot.send_message(chat_id, chunk)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "🏛️ **Mímir v6.0 (Ótakmörkuð Skynfæri)**\n\nSendu mér texta, skjöl, myndir, vídeó eða raddskilaboð. Ég greini allt!")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    texti = message.text.strip()
    if texti.startswith('/'): return
    status_msg = bot.reply_to(message, "⏳ *Kveiki á Ratsjá og Kafara...*", parse_mode="Markdown")

    def process_request():
        try:
            bot.edit_message_text("🧠 *Kafarinn fann gögn. Greini...*", chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode="Markdown")
            svar = analyze_query(texti)
            safe_send_reply(message.chat.id, status_msg.message_id, svar)
        except Exception as e:
            try: bot.edit_message_text(f"🛑 **Kerfisvilla:** {str(e)[:200]}", chat_id=message.chat.id, message_id=status_msg.message_id)
            except: pass

    threading.Thread(target=process_request).start()

@bot.message_handler(content_types=['voice', 'audio', 'document', 'photo', 'video'])
def handle_files(message):
    status_msg = bot.reply_to(message, "⏳ *Móttek skrá...*", parse_mode="Markdown")
    
    def process_file():
        local_path = ""
        try:
            file_info_id = None
            if message.content_type == 'photo': file_info_id = message.photo[-1].file_id
            elif message.content_type == 'document': file_info_id = message.document.file_id
            elif message.content_type == 'video': file_info_id = message.video.file_id
            elif message.content_type in ['audio', 'voice']: file_info_id = getattr(message, message.content_type).file_id
                
            if not file_info_id: return
            file_info = bot.get_file(file_info_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            ext = file_info.file_path.split('.')[-1]
            local_path = os.path.join(SANDBOX_DIR, f"{message.content_type}_{message.message_id}.{ext}")
            
            with open(local_path, 'wb') as new_file:
                new_file.write(downloaded_file)

            bot.edit_message_text("👁️👂 *Sendi skrá í örugga greiningu í skýið...*", chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode="Markdown")
            
            user_prompt = message.caption if message.caption else ""
            svar = analyze_multimodal(local_path, user_prompt)
            safe_send_reply(message.chat.id, status_msg.message_id, svar)
            
        except Exception as e:
            try: bot.edit_message_text(f"🛑 **Villa:** {str(e)[:200]}", chat_id=message.chat.id, message_id=status_msg.message_id)
            except: pass
        finally:
            if local_path and os.path.exists(local_path):
                try: subprocess.run(["shred", "-u", "-z", local_path], check=True)
                except: os.remove(local_path)

    threading.Thread(target=process_file).start()

if __name__ == "__main__":
    print("🚀 [Mímir Core v6.0] OMNI-BOT RÆSTUR MEÐ SNJALLBÚTARA.")
    bot.infinity_polling(skip_pending=True)
