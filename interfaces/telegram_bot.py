import os, sys, telebot
from dotenv import load_dotenv
load_dotenv("/workspace/mimir_net/config/.env")
TOKEN = os.getenv('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TOKEN)
try:
    sys.path.append("/workspace/mimir_net")
    from skills.drive_reader import MimirVision
    vision = MimirVision()
    VR = True
except:
    VR = False
@bot.message_handler(commands=['start', 'restart'])
def welcome(message):
    bot.reply_to(message, "🏛️ Mímir v3.5 ONLINE.\nLyklar staðfestir hjá Sigvalda.")
@bot.message_handler(commands=['skjol'])
def handle_skjol(message):
    if not VR: return bot.reply_to(message, "❌ Höll lokuð.")
    files = vision.list_pdfs()
    listi = "\n".join([f"📄 {f['name']}" for f in files])
    bot.reply_to(message, f"📂 **Skjöl:**\n{listi}")
if __name__ == "__main__":
    print("🚀 Mímir ræstur..."); bot.infinity_polling()
