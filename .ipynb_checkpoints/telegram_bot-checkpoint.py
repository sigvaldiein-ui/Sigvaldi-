import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv

# Flytjum inn sjónina og greindina úr skills möppunni
from mimir_net.skills.drive_reader import MimirVision

# 1. Stillingar og Lyklar (SOP)
ENV_PATH = '/workspace/mimir_net/config/.env'
load_dotenv(ENV_PATH)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") # Sækir úr lykla-möppunni
mimir = MimirVision()

# 2. Skipun: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Sæll Sigvaldi! Mímir er vaknaður. Ég hef fullan aðgang að 30 TB Höllinni þinni.")

# 3. Skipun: /spyrja [spurning]
async def spyrja(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("Hverju viltu að ég leiti að í MBA ritgerðinni þinni?")
        return

    msg = await update.message.reply_text("🧠 Mímir rýnir í gögnin...")
    
    try:
        # Sækjum gögnin úr Drive
        files = mimir.list_files()
        texti = mimir.read_pdf(files[0]['id']) # Lesum nýjasta skjalið
        
        # Fáum greiningu frá Claude (OpenRouter)
        svar = mimir.ask_mimir(texti[:15000], query)
        
        await msg.edit_text(f"✨ **Niðurstaða Mímis:**\n\n{svar}", parse_mode='Markdown')
    except Exception as e:
        await msg.edit_text(f"❌ Villa kom upp: {e}")

# 4. Ræsum botann
if __name__ == '__main__':
    print("🚀 Mímir er að ræsa Telegram-brúna...")
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("spyrja", spyrja))
    
    print("✅ Mímir er kominn á vaktina í Telegram.")
    app.run_polling()