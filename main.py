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
ADMIN_ID = int(os.environ.get("ADMIN_ID"))  # Render पर ADMIN_ID सेट करें

# ------------------- Start Command -------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Bot Started! Use /afk to set AFK.")

# ------------------- Delete Edited Messages -------------------
async def delete_edited(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.edited_message.delete()
    except Exception as e:
        print(f"Delete Error: {e}")

# ------------------- AFK Feature -------------------
async def set_afk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    context.user_data['afk'] = True
    await update.message.reply_text(f"⏸️ {user.first_name} is now AFK!")

# ------------------- Broadcast (Admin Only) -------------------
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized!")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return
    
    message = " ".join(context.args)
    # यहाँ आप सभी groups/users को message भेजने का logic add करें
    # उदाहरण: await context.bot.send_message(chat_id=GROUP_ID, text=message)
    await update.message.reply_text("✅ Broadcast sent!")

# ------------------- Main Function -------------------
def main():
    app = Application.builder().token(TOKEN).build()
    
    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("afk", set_afk))
    app.add_handler(CommandHandler("broadcast", broadcast))
    
    # Edited Messages Handler
    app.add_handler(MessageHandler(filters.UpdateType.EDITED_MESSAGE, delete_edited))
    
    # Render Webhook Setup (Port 10000)
    PORT = int(os.environ.get("PORT", 10000))
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url="https://edittttrrrrr.onrender.com",  # अपना URL डालें
        secret_token="12345SECRET"  # कोई भी secret token
    )

if __name__ == "__main__":
    main()
