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
LOGGER_GROUP = int(os.environ.get("LOGGER_GROUP"))  # अपना Logger Group ID डालें
START_IMAGE_URL = os.environ.get("START_IMAGE_URL")  # Image URL (जैसे: https://telegra.ph/file/...jpg)

client = pymongo.MongoClient(MONGODB_URI)
db = client["EmikoBotDB"]
afk_collection = db["afk"]
chats_collection = db["chats"]

# ------------------- Logger Function -------------------
async def log_event(event_type: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        chat = update.effective_chat
        
        if event_type == "private_start":
            log_text = f"""
🌸 **New User Started Bot** 🌸
┌ 👤 User: [{user.first_name}](tg://user?id={user.id})
├ 🆔 ID: `{user.id}`
└ 📅 Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
            """
        
        elif event_type == "group_add":
            log_text = f"""
👥 **Bot Added to Group** 👥
┌ 📛 Group: {chat.title}
├ 🆔 ID: `{chat.id}`
├ 👤 Added By: [{user.first_name}](tg://user?id={user.id})
└ 📅 Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
            """

        await context.bot.send_message(
            chat_id=LOGGER_GROUP,
            text=log_text.strip(),
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Logger Error: {e}")

# ------------------- Store Chat IDs -------------------
async def store_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if not chats_collection.find_one({"chat_id": chat.id}):
        chat_type = "group" if chat.type in ["group", "supergroup"] else "private"
        chats_collection.insert_one({"chat_id": chat.id, "type": chat_type})
        
        if chat_type == "group":
            await log_event("group_add", update, context)

# ------------------- Start Command with Image -------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await store_chat_id(update, context)
    
    # Private Start Log
    if update.message.chat.type == "private":
        await log_event("private_start", update, context)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add me in your Group", url=f"https://t.me/{context.bot.username}?startgroup=true")],
        [InlineKeyboardButton("❓ Help and Commands", callback_data="help_menu")],
        [
            InlineKeyboardButton("👤 Owner", url="https://t.me/Itz_Marv1n"),
            InlineKeyboardButton("💬 Support", url="https://t.me/Anime_Group_chat_en")
        ],
        [InlineKeyboardButton("📢 Channel", url="https://t.me/Samurais_network")]
    ])
    
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=START_IMAGE_URL,
        caption="""
🌸 **Welcome to Emiko Edit!** 🌸

I'm your cute anime-style assistant to manage groups!
★ Edit Message Cleaner ✨
★ AFK System ⏰
★ Broadcast Tools 📢

Use buttons below to explore my features~""",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# ------------------- Help Menu (Fixed) -------------------
async def help_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    help_text = """
🎀 *Emiko Edit Help Menu* 🎀

✨ *Features:*
• `/afk` - Set AFK status
• `/broadcast` - Send message to all users (Admin)
• Auto-deletes edited messages

⚙️ *How to Use:*
1. Add me to your group
2. Make me admin
3. I'll auto-delete edited messages!

🌸 Made with love by [Samurais Network](https://t.me/Samurais_network)
    """
    
    try:
        # Edit the original message's caption
        await query.edit_message_caption(
            caption=help_text.strip(),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="start_menu")]
            ])
        )
    except Exception as e:
        print(f"Help Menu Error: {e}")
        await query.message.reply_text(
            text=help_text.strip(),
            parse_mode="Markdown",
            disable_web_page_preview=True
        )

# ------------------- Back to Start Menu -------------------
async def start_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await start(update, context)  # Reuse the start function

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
    app.add_handler(CallbackQueryHandler(start_menu, pattern="^start_menu$"))
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
