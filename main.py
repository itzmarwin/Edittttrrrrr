from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
import os

TOKEN = os.environ.get("TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))  # 0 को अपने ID से replace करें

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot Started!")

async def delete_edited(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.edited_message.delete()
    except Exception as e:
        print(f"Error: {e}")

def main():
    app = Application.builder().token(TOKEN).build()
    
    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.UpdateType.EDITED_MESSAGE, delete_edited))
    
    # Render Webhook Setup
    PORT = int(os.environ.get("PORT", 10000))
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url="https://edittttrrrrr.onrender.com",  # अपना URL डालें
        secret_token="12345SECRET"  # कोई भी random token
    )

if __name__ == "__main__":
    main()
