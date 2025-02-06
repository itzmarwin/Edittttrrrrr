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

# Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot Started! Use /afk to set AFK.")

# Delete Edited Messages
async def delete_edited(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.edited_message.delete()
    except Exception as e:
        print(f"Error: {e}")

# AFK Command
async def set_afk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    context.user_data['afk'] = True
    await update.message.reply_text(f"{user.first_name} is AFK now!")

def main():
    app = Application.builder().token(TOKEN).build()
    
    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("afk", set_afk))
    
    # EDITED_MESSAGE को सही filter के साथ
    app.add_handler(MessageHandler(filters.UpdateType.EDITED_MESSAGE, delete_edited))
    
    # Render पर Polling चलाएं
    app.run_polling()

if __name__ == "__main__":
    main()
