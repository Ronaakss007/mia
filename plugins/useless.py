from bot import Bot
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, CallbackQuery
from config import (
    ADMINS, BOT_STATS_TEXT, USER_REPLY_TEXT, USER_REPLY_BUTTONS, 
    DISABLE_WEB_PAGE_PREVIEW, OWNER_TAG
)
from datetime import datetime
from helper_func import get_readable_time
from database.database import user_data

# 📊 Bot Statistics Command
@Bot.on_message(filters.command('stats') & filters.user(ADMINS))
async def stats(bot: Bot, message: Message):
    uptime = get_readable_time((datetime.now() - bot.uptime).seconds)
    total_users = await user_data.count_documents({})  # Count all users in DB
    await message.reply(BOT_STATS_TEXT.format(uptime=uptime, total_users=total_users))

# 🚫 Check if a user is banned
async def is_banned(user_id: int) -> bool:
    user = await user_data.find_one({'_id': user_id})
    return bool(user and user.get("banned", False))

# ✉️ Handle Private Messages (Non-Admin & Non-Command)
@Bot.on_message(
    filters.private
    & ~filters.user(ADMINS)
    & ~filters.command([
        'start', 'ping', 'convert', 'cancel', 'help'
        , 'points', 'video', 'pic', 'refer', 'earn'
        ,'top', 'leaderboard' ,'transfer', 'info'
    ])
)
async def global_ban_check_message(client: Client, message: Message):
    user_id = message.from_user.id

    # 🚫 Ban Check
    if await is_banned(user_id):
        await message.reply(
            f"🚫 Aᴄᴄᴇss Dᴇɴɪᴇᴅ!\n\n"
            f"Yᴏᴜ'ᴠᴇ Bᴇᴇɴ *Bᴀɴɴᴇᴅ* ғʀᴏᴍ ᴜsɪɴɢ NʏxCɪᴘʜᴇʀ 🤖\n"
            f"Cᴏɴᴛᴀᴄᴛ @{OWNER_TAG} ᴛᴏ ᴀᴘᴘᴇᴀʟ."
        )
        return

    # 🧠 Optional: Message Tracking
    if hasattr(message._client, "processed_messages"):
        message._client.processed_messages += 1

    # 📩 Default Fallback Reply
    if USER_REPLY_TEXT:
        await message.reply(
            USER_REPLY_TEXT,
            reply_markup=InlineKeyboardMarkup(USER_REPLY_BUTTONS),
            disable_web_page_preview=DISABLE_WEB_PAGE_PREVIEW
        )

# 🔘 Handle Callback Queries (Buttons)
@Bot.on_callback_query()
async def global_ban_check_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    try:
        if await is_banned(user_id):
            await query.answer(
                text=(
                    "🚫 Aᴄᴄᴇss Dᴇɴɪᴇᴅ!\n\n"
                    "Yᴏᴜ'ᴠᴇ Bᴇᴇɴ *Bᴀɴɴᴇᴅ* ғʀᴏᴍ ᴜsɪɴɢ NʏxCɪᴘʜᴇʀ 🤖\n"
                    f"Cᴏɴᴛᴀᴄᴛ @{OWNER_TAG} ᴛᴏ ᴀᴘᴘᴇᴀʟ."
                ),
                show_alert=True
            )
            return
        await client.resolve_callback_query(query)  # Optional: To avoid "Query is not answered" error
    except Exception as e:
        print(f"[CB ERROR] {e}")
