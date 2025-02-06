from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CallbackQueryHandler
)
from datetime import datetime
import os
import pymongo

# MongoDB Setup
MONGODB_URI = os.environ.get("MONGODB_URI")
client = pymongo.MongoClient(MONGODB_URI)
db = client["EmikoBotDB"]
afk_collection = db["afk"]
chats_collection = db["chats"]

# ------------------- Delete Edited Messages -------------------
async def delete_edited(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.edited_message.chat.type in ["group", "supergroup"]:
        try:
            user = update.edited_message.from_user
            await update.edited_message.delete()
            await context.bot.send_message(
                chat_id=update.edited_message.chat_id,
                text=f"🌸 **Dear {user.first_name},**\nYour edited message was deleted to keep our chat clean! ✨",
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Delete Error: {e}")

# ------------------- Store Chat IDs -------------------
async def store_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if not chats_collection.find_one({"chat_id": chat.id}):
        chat_type = "group" if chat.type in ["group", "supergroup"] else "private"
        chats_collection.insert_one({
            "chat_id": chat.id,
            "type": chat_type
        })

# ------------------- Start Command -------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await store_chat_id(update, context)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{context.bot.username}?startgroup=true")],
        [InlineKeyboardButton("📚 Help", callback_data="help_menu")],
        [
            InlineKeyboardButton("👑 Owner", url="https://t.me/YourUsername"),
            InlineKeyboardButton("💬 Support", url="https://t.me/YourSupportGroup")
        ],
        [InlineKeyboardButton("🔔 Channel", url="https://t.me/YourChannel")]
    ])
    
    await update.message.reply_text(
        "🌸 **Welcome to Emiko Edit!** 🌸\n\n"
        "I'm your cute anime-style assistant to manage groups!\n"
        "★ Edit Message Cleaner ✨\n"
        "★ AFK System ⏰\n"
        "★ Broadcast Tools 📢\n\n"
        "Use buttons below to explore my features~",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# ------------------- Help Menu -------------------
async def help_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    help_text = (
        "🎀 **Emiko Edit Help Menu** 🎀\n\n"
        "✨ **Features:**\n"
        "➤ `/afk` - Set AFK status\n"
        "➤ `/broadcast` - Send message to all users (Admin)\n"
        "➤ Auto-deletes edited messages\n\n"
        "⚙️ **How to Use:**\n"
        "1. Add me to your group\n"
        "2. Make me admin\n"
        "3. I'll auto-delete edited messages!\n\n"
        "🌸 Made with love by @YourUsername"
    )
    await query.edit_message_text(
        text=help_text,
        parse_mode="Markdown"
    )

# ------------------- Broadcast -------------------
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != int(os.environ.get("ADMIN_ID")):
        await update.message.reply_text("❌ You're not authorized!", parse_mode="Markdown")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: `/broadcast Your message here`", parse_mode="Markdown")
        return
    
    message = " ".join(context.args)
    all_chats = chats_collection.find()
    
    user_count = 0
    group_count = 0
    failed = 0
    
    for chat in all_chats:
        try:
            await context.bot.send_message(
                chat_id=chat["chat_id"],
                text=message,
                parse_mode="Markdown"
            )
            if chat["type"] == "private":
                user_count += 1
            else:
                group_count += 1
        except Exception as e:
            print(f"Broadcast Error: {e}")
            failed += 1
    
    await update.message.reply_text(
        f"✅ **Broadcast Report:**\n👤 Users: {user_count}\n👥 Groups: {group_count}\n❌ Failed: {failed}",
        parse_mode="Markdown"
    )

# ------------------- AFK System -------------------
async def set_afk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type in ["group", "supergroup"]:
        user = update.effective_user
        now = datetime.now()
        afk_collection.update_one(
            {"user_id": user.id},
            {"$set": {"afk": True, "time": now}},
            upsert=True
        )
        await update.message.reply_text(f"⏸️ **{user.first_name} ɪs ɴᴏᴡ ᴀғᴋ!**", parse_mode="Markdown")

async def handle_afk_return(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type in ["group", "supergroup"]:
        user = update.effective_user
        afk_data = afk_collection.find_one({"user_id": user.id})
        if afk_data:
            afk_time = afk_data["time"]
            now = datetime.now()
            delta = now - afk_time
            seconds = delta.total_seconds()
            afk_collection.delete_one({"user_id": user.id})
            await update.message.reply_text(
                f"🎉 **{user.first_name} ɪs ʙᴀᴄᴋ ᴏɴʟɪɴᴇ!**\n⏱️ ᴀᴡᴀʏ ғᴏʀ `{int(seconds)}s`",
                parse_mode="Markdown"
            )

async def afk_mention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type in ["group", "supergroup"] and update.message.entities:
        for entity in update.message.entities:
            if entity.type in ["mention", "text_mention"]:
                mentioned_user = entity.user
                afk_data = afk_collection.find_one({"user_id": mentioned_user.id})
                if afk_data:
                    afk_time = afk_data["time"]
                    now = datetime.now()
                    delta = now - afk_time
                    seconds = delta.total_seconds()
                    await update.message.reply_text(
                        f"⚠️ **{mentioned_user.first_name} ɪs ᴀғᴋ!**\n⏰ ᴀᴡᴀʏ sɪɴᴄᴇ `{int(seconds)}s`",
                        parse_mode="Markdown"
                    )

# ------------------- Main Function -------------------
def main():
    app = Application.builder().token(os.environ.get("TOKEN")).build()
    
    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("afk", set_afk))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CallbackQueryHandler(help_button, pattern="^help_menu$"))
    app.add_handler(MessageHandler(filters.UpdateType.EDITED_MESSAGE & filters.ChatType.GROUPS, delete_edited))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS, handle_afk_return))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS, afk_mention))
    app.add_handler(MessageHandler(filters.ALL, store_chat_id))
    
    # Webhook
    PORT = int(os.environ.get("PORT", 10000))
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=os.environ.get("WEBHOOK_URL"),
        secret_token=os.environ.get("SECRET_TOKEN")
    )

if __name__ == "__main__":
    main()
