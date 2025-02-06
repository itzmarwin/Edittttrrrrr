from telegram import Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
    Application
)
import os

TOKEN = os.environ.get("TOKEN")  # Render पर Environment Variable से लेगा

# Start Command
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Hi! I'm your bot. Use /afk to set AFK.")

# Delete Edited Messages
async def delete_edited(update: Update, context: CallbackContext):
    try:
        await update.edited_message.delete()
    except Exception as e:
        print(f"Error deleting message: {e}")

# AFK Feature (Basic)
async def set_afk(update: Update, context: CallbackContext):
    user = update.effective_user
    context.user_data['afk'] = True
    await update.message.reply_text(f"{user.first_name} is now AFK.")

# Broadcast Feature (Admin Only)
async def broadcast(update: Update, context: CallbackContext):
    user = update.effective_user
    if user.id != ADMIN_ID:  # Replace ADMIN_ID with your Telegram ID
        return
    message = " ".join(context.args)
    # Send message to all groups (इसे अपने हिसाब से customize करें)
    # ...

def main():
    app = Application.builder().token(TOKEN).build()
    
    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("afk", set_afk))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.EDITED_MESSAGE, delete_edited))
    
    # Render पर Webhook के बजाय Polling use करें (Render की Limitations के कारण)
    app.run_polling()

if __name__ == "__main__":
    main()
