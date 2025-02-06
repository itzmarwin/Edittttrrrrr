from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from datetime import datetime
import os
import pymongo

# MongoDB Setup
MONGODB_URI = os.environ.get("MONGODB_URI")
client = pymongo.MongoClient(MONGODB_URI)
db = client["DevilBotDB"]
afk_collection = db["afk"]
chats_collection = db["chats"]

# ------------------- Delete Edited Messages -------------------
async def delete_edited(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.edited_message.delete()
    except Exception as e:
        print(f"Delete Error: {e}")

# ------------------- Store Chat IDs -------------------
async def store_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if not chats_collection.find_one({"chat_id": chat_id}):
        chats_collection.insert_one({"chat_id": chat_id})

# ------------------- Start Command -------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await store_chat_id(update, context)
    await update.message.reply_text("🚀 **Dᴇᴠɪʟ 樣 ɪs ᴀʟɪᴠᴇ!**\nUse `/afk` to set AFK.", parse_mode="Markdown")

# ------------------- AFK Feature -------------------
async def set_afk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    now = datetime.now()
    afk_collection.update_one(
        {"user_id": user.id},
        {"$set": {"afk": True, "time": now}},
        upsert=True
    )
    await update.message.reply_text(f"⏸️ **{user.first_name} 樣 ɪs ɴᴏᴡ ᴀғᴋ!**", parse_mode="Markdown")

async def handle_afk_return(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    afk_data = afk_collection.find_one({"user_id": user.id})
    if afk_data:
        afk_time = afk_data["time"]
        now = datetime.now()
        delta = now - afk_time
        seconds = delta.total_seconds()
        afk_collection.delete_one({"user_id": user.id})
        await update.message.reply_text(
            f"🎉 **{user.first_name} 樣 ɪs ʙᴀᴄᴋ ᴏɴʟɪɴᴇ!**\n"
            f"⏱️ ᴀᴡᴀʏ ғᴏʀ `{int(seconds)}s`",
            parse_mode="Markdown"
        )

async def afk_mention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.entities:
        for entity in update.message.entities:
            if entity.type == "mention" or entity.type == "text_mention":
                mentioned_user = entity.user
                afk_data = afk_collection.find_one({"user_id": mentioned_user.id})
                if afk_data:
                    afk_time = afk_data["time"]
                    now = datetime.now()
                    delta = now - afk_time
                    seconds = delta.total_seconds()
                    await update.message.reply_text(
                        f"⚠️ **{mentioned_user.first_name} ɪs ᴀғᴋ!**\n"
                        f"⏰ ᴀᴡᴀʏ sɪɴᴄᴇ `{int(seconds)}s`",
                        parse_mode="Markdown"
                    )

# ------------------- Broadcast -------------------
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != int(os.environ.get("ADMIN_ID")):
        await update.message.reply_text("❌ **Yᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ!**", parse_mode="Markdown")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: `/broadcast <message>`", parse_mode="Markdown")
        return
    
    message = " ".join(context.args)
    all_chats = chats_collection.find()
    sent = 0
    failed = 0
    for chat in all_chats:
        try:
            await context.bot.send_message(
                chat_id=chat["chat_id"],
                text=f"📢 **Bʀᴏᴀᴅᴄᴀsᴛ:**\n{message}",
                parse_mode="Markdown"
            )
            sent += 1
        except Exception as e:
            print(f"Error in broadcast: {e}")
            failed += 1
    
    await update.message.reply_text(
        f"✅ **Bʀᴏᴀᴅᴄᴀsᴛ Rᴇsᴜʟᴛ:**\n"
        f"• Sᴇɴᴛ: `{sent}`\n"
        f"• Fᴀɪʟᴇᴅ: `{failed}`",
        parse_mode="Markdown"
    )

# ------------------- Main Function -------------------
def main():
    app = Application.builder().token(os.environ.get("TOKEN")).build()
    
    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("afk", set_afk))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.UpdateType.EDITED_MESSAGE, delete_edited))  # Fixed
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_afk_return))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, afk_mention))
    app.add_handler(MessageHandler(filters.ALL, store_chat_id))
    
    # Webhook Setup
    PORT = int(os.environ.get("PORT", 10000))
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=os.environ.get("WEBHOOK_URL"),
        secret_token=os.environ.get("SECRET_TOKEN")
    )

if __name__ == "__main__":
    main()
