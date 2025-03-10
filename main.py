from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, ChatMemberOwner
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
LOGGER_GROUP = int(os.environ.get("LOGGER_GROUP"))
START_IMAGE_URL = os.environ.get("START_IMAGE_URL")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

client = pymongo.MongoClient(MONGODB_URI)
db = client["EmikoBotDB"]
chats_collection = db["chats"]
sudoers_collection = db["sudoers"]
blocked_collection = db["blocked"]
authorized_collection = db["authorized"]

# ==================== HELPER FUNCTIONS ====================

def is_owner(user_id: int) -> bool:
    return user_id == ADMIN_ID

def is_sudo(user_id: int) -> bool:
    return sudoers_collection.find_one({"user_id": user_id}) is not None

async def is_bot_admin(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        bot_member = await context.bot.get_chat_member(chat_id, context.bot.id)
        return bot_member.status in ["administrator", "creator"]
    except Exception as e:
        print(f"Bot Admin Check Error: {e}")
        return False

async def is_group_admin(chat_id: int, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        user_member = await context.bot.get_chat_member(chat_id, user_id)
        return user_member.status in ["administrator", "creator"]
    except Exception as e:
        print(f"Admin Check Error: {e}")
        return False

async def get_stats():
    total_groups = chats_collection.count_documents({"type": "group"})
    total_users = chats_collection.count_documents({"type": "private"})
    blocked_users = blocked_collection.count_documents({})
    sudoers_count = sudoers_collection.count_documents({})
    return total_groups, total_users, blocked_users, sudoers_count

# ==================== CORE FUNCTIONS ====================

async def delete_edited(update: Update, context: ContextTypes.DEFAULT_TYPE):
    edited_message = update.edited_message
    if not edited_message:
        return
    
    # सिर्फ टेक्स्ट/कैप्शन एडिट्स को चेक करें ✅
    has_text = edited_message.text or (edited_message.caption and len(edited_message.caption) > 0)
    if not has_text:
        return  # रिएक्शन/मीडिया बदलावों को इग्नोर करें
    
    user = edited_message.from_user
    chat = edited_message.chat

    # अथॉराइज्ड यूजर्स को चेक करें
    is_authorized = authorized_collection.find_one({
        "user_id": user.id,
        "chat_id": chat.id
    })
    if is_authorized:
        return

    # मैसेज डिलीट करें
    try:
        await edited_message.delete()
        await context.bot.send_message(
            chat_id=chat.id,
            text=f"🌸 Nyaa~ {user.first_name}! (≧ω≦)\nNo sneaky edits~ Stay tidy! ✨💕",
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Delete Error: {e}")

async def log_event(event_type: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        chat = update.effective_chat
        
        username = f"@{user.username}" if user.username else "None"
        group_username = f"@{chat.username}" if chat.username else "None"
        group_title = chat.title if chat.title else "None"

        if event_type == "private_start":
            log_text = f"""
🌸 **New User Started Bot** 🌸
┌ 👤 User: [{user.first_name}](tg://user?id={user.id}) ({username})
├ 🆔 ID: `{user.id}`
└ 📅 Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
            """
        
        elif event_type == "group_add":
            log_text = f"""
👥 **Bot Added to Group** 👥
┌ 📛 Group: {group_title} ({group_username})
├ 🆔 ID: `{chat.id}`
├ 👤 Added By: [{user.first_name}](tg://user?id={user.id}) ({username})
└ 📅 Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
            """

        elif event_type == "group_remove":
            log_text = f"""
🗑️ **Bot Removed from Group** 🗑️
┌ 📛 Group: {group_title} ({group_username})
├ 🆔 ID: `{chat.id}`
├ 👤 Removed By: [{user.first_name}](tg://user?id={user.id}) ({username})
└ 📅 Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
            """

        await context.bot.send_message(
            chat_id=LOGGER_GROUP,
            text=log_text.strip(),
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Logger Error: {e}")

async def store_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if not chats_collection.find_one({"chat_id": chat.id}):
        chat_type = "group" if chat.type in ["group", "supergroup"] else "private"
        chats_collection.insert_one({"chat_id": chat.id, "type": chat_type})
        
        if chat_type == "group":
            await log_event("group_add", update, context)

# ==================== COMMANDS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await store_chat_id(update, context)
    
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
        caption="🌸 **Hii~ I'ᴍ Emiko!** 🌸\n\nI'm here to keep your group clean & fun! (≧▽≦)\n╰☆✿ **Auto-delete edited messages** ✨\n╰☆✿ **Easy message broadcasting** 📢\n\nUse the buttons below to explore my features! (✿◕‿◕)♡",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not (is_owner(update.effective_user.id) or is_sudo(update.effective_user.id)):
        await update.message.reply_text("🚫 You don't have permission!", parse_mode="Markdown")
        return
    
    groups, users, blocked, sudoers = await get_stats()
    bot_name = f"[Emiko Bot](https://t.me/{context.bot.username})"
    stats_text = f"""
**{bot_name} sᴛᴀᴛs ᴀɴᴅ ɪɴғᴏʀᴍᴀᴛɪᴏɴ :**
**ʙʟᴏᴄᴋᴇᴅ :** `{blocked}`
**ᴄʜᴀᴛs :** `{groups}`
**ᴜsᴇʀs :** `{users}`
**sᴜᴅᴏᴇʀs :** `{sudoers}`
    """
    await update.message.reply_text(stats_text.strip(), parse_mode="Markdown")

async def add_sudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("🚫 Owner-only command!", parse_mode="Markdown")
        return
    
    target_user = None
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
    elif context.args:
        try:
            user_input = context.args[0]
            if user_input.startswith("@"):
                user = await context.bot.get_chat(user_input)
                target_user = user
            else:
                target_user = await context.bot.get_chat(int(user_input))
        except Exception as e:
            print(f"Sudo Error: {e}")
    
    if not target_user:
        await update.message.reply_text("Reply to user or provide username/ID!", parse_mode="Markdown")
        return
    
    sudoers_collection.update_one(
        {"user_id": target_user.id},
        {"$set": {"user_id": target_user.id, "username": target_user.username}},
        upsert=True
    )
    await update.message.reply_text(f"✅ Added {target_user.first_name} to sudoers!", parse_mode="Markdown")

async def remove_sudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("🚫 Owner-only command!", parse_mode="Markdown")
        return
    
    target_user = None
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
    elif context.args:
        try:
            user_input = context.args[0]
            if user_input.startswith("@"):
                user = await context.bot.get_chat(user_input)
                target_user = user
            else:
                target_user = await context.bot.get_chat(int(user_input))
        except Exception as e:
            print(f"Sudo Error: {e}")
    
    if not target_user:
        await update.message.reply_text("Reply to user or provide username/ID!", parse_mode="Markdown")
        return
    
    sudoers_collection.delete_one({"user_id": target_user.id})
    await update.message.reply_text(f"❌ Removed {target_user.first_name} from sudoers!", parse_mode="Markdown")

async def sudo_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not (is_owner(update.effective_user.id) or is_sudo(update.effective_user.id)):
        await update.message.reply_text("🚫 You don't have permission!", parse_mode="Markdown")
        return
    
    sudoers = list(sudoers_collection.find({}))
    if not sudoers:
        await update.message.reply_text("No sudo users found!", parse_mode="Markdown")
        return
    
    sudo_list = []
    for user in sudoers:
        username = f"@{user['username']}" if user.get("username") else "No Username"
        sudo_list.append(f"• {username} (`{user['user_id']}`)")
    
    list_text = "**Sudo Users List:**\n" + "\n".join(sudo_list)
    await update.message.reply_text(list_text, parse_mode="Markdown")

async def help_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    help_text = """
🎀 *Emiko Edit Help Menu* 🎀

✨ *Features:*
• /broadcast - Send message to all users (Admin)
• Auto-deletes edited messages

✨ *How to use:*
1. Add me to your group
2. Make me Admin
3. I'll auto-delete edited messages!

🌸 Made with love by [Samurais Network](https://t.me/Samurais_network)
    """
    
    try:
        await query.edit_message_caption(
            caption=help_text.strip(),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="start_menu")]
            ])
        )
    except Exception as e:
        print(f"Help Error: {e}")

async def start_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add me in your Group", url=f"https://t.me/{context.bot.username}?startgroup=true")],
            [InlineKeyboardButton("❓ Help and Commands", callback_data="help_menu")],
            [
                InlineKeyboardButton("👤 Owner", url="https://t.me/Itz_Marv1n"),
                InlineKeyboardButton("💬 Support", url="https://t.me/Anime_Group_chat_en")
            ],
            [InlineKeyboardButton("📢 Channel", url="https://t.me/Samurais_network")]
        ])
        
        await query.edit_message_media(
            media=InputMediaPhoto(
                media=START_IMAGE_URL,
                caption="🌸 **Hii~ I'ᴍ Emiko!** 🌸\n\nI'm here to keep your group clean & fun! (≧▽≦)\n╰☆✿ **Auto-delete edited messages** ✨\n╰☆✿ **Easy message broadcasting** 📢\n\nUse the buttons below to explore my features! (✿◕‿◕)♡",
                parse_mode="Markdown"
            ),
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"Back Button Error: {e}")

# ==================== BROADCAST SYSTEM ====================

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not (is_owner(user.id) or is_sudo(user.id)):
        await update.message.reply_text("❌ You're not authorized!", parse_mode="Markdown")
        return
    
    reply_msg = update.message.reply_to_message
    if not reply_msg:
        await update.message.reply_text("Reply to a message to broadcast!", parse_mode="Markdown")
        return
    
    all_chats = chats_collection.find()
    groups = 0
    users = 0
    failed = 0
    
    for chat in all_chats:
        try:
            if reply_msg.forward_from_chat or reply_msg.forward_from:
                await reply_msg.forward(chat_id=chat["chat_id"])
            else:
                await reply_msg.copy(chat_id=chat["chat_id"])
            
            if chat["type"] == "group":
                groups +=1
            else:
                users +=1
        except Exception as e:
            print(f"Broadcast Error: {e}")
            failed +=1
            blocked_collection.update_one(
                {"chat_id": chat["chat_id"]},
                {"$set": {"chat_id": chat["chat_id"]}},
                upsert=True
            )
    
    await update.message.reply_text(
        f"✅ **Broadcast Report:**\n👥 Groups: `{groups}`\n👤 Users: `{users}`\n❌ Failed: `{failed}`",
        parse_mode="Markdown"
    )

# -------------------- AUTH/UNATH COMMANDS --------------------
async def auth_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    message = update.effective_message

    # Check bot admin status
    if not await is_bot_admin(chat.id, context):
        await message.reply_text("❌ I need admin privileges to work!")
        return

    # Check user permissions
    if not (is_owner(user.id) or is_sudo(user.id) or await is_group_admin(chat.id, user.id, context)):
        await message.reply_text("🚫 You need admin rights to use this command!")
        return

    # Resolve target user
    target_user = None
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    elif context.args:
        try:
            user_input = context.args[0].strip()
            if user_input.startswith("@"):
                target_user = await context.bot.get_chat(user_input)
            else:
                target_user = await context.bot.get_chat(int(user_input))
        except Exception as e:
            print(f"Auth Error: {e}")
            await message.reply_text("⚠️ Invalid user! Use:\n/auth @username\n/auth 123456\n/reply to message")
            return

    if not target_user:
        await message.reply_text("⚠️ Please reply to a user or provide username/ID")
        return

    # Update database
    authorized_collection.update_one(
        {"user_id": target_user.id, "chat_id": chat.id},
        {"$set": {"user_id": target_user.id, "chat_id": chat.id}},
        upsert=True
    )
    await message.reply_text(f"✅ Authorized {target_user.first_name}!")

async def unauth_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    message = update.effective_message

    # Check bot admin status
    if not await is_bot_admin(chat.id, context):
        await message.reply_text("❌ I need admin privileges to work!")
        return

    # Check user permissions
    if not (is_owner(user.id) or is_sudo(user.id) or await is_group_admin(chat.id, user.id, context)):
        await message.reply_text("🚫 You need admin rights to use this command!")
        return

    # Resolve target user
    target_user = None
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    elif context.args:
        try:
            user_input = context.args[0].strip()
            if user_input.startswith("@"):
                target_user = await context.bot.get_chat(user_input)
            else:
                target_user = await context.bot.get_chat(int(user_input))
        except Exception as e:
            print(f"Unauth Error: {e}")
            await message.reply_text("⚠️ Invalid user! Use:\n/unauth @username\n/unauth 123456\n/reply to message")
            return

    if not target_user:
        await message.reply_text("⚠️ Please reply to a user or provide username/ID")
        return

    # Update database
    authorized_collection.delete_one(
        {"user_id": target_user.id, "chat_id": chat.id}
    )
    await message.reply_text(f"❌ Removed {target_user.first_name}'s editing privileges")

# ==================== MAIN ====================

def main():
    app = Application.builder().token(os.environ.get("TOKEN")).build()
    
    app.add_handler(CommandHandler("auth", auth_user))
    app.add_handler(CommandHandler("unauth", unauth_user))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("addsudo", add_sudo))
    app.add_handler(CommandHandler("rmsudo", remove_sudo))
    app.add_handler(CommandHandler("sudolist", sudo_list))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CallbackQueryHandler(help_button, pattern="^help_menu$"))
    app.add_handler(CallbackQueryHandler(start_menu, pattern="^start_menu$"))
    app.add_handler(MessageHandler(
        filters.UpdateType.EDITED_MESSAGE & filters.ChatType.GROUPS,
        delete_edited
    ))
    app.add_handler(MessageHandler(filters.ALL, store_chat_id))
    
    PORT = int(os.environ.get("PORT", 10000))
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=os.environ.get("WEBHOOK_URL"),
        secret_token=os.environ.get("SECRET_TOKEN")
    )

if __name__ == "__main__":
    main()
