from pyrogram import __version__, filters, Client
from bot import Bot
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message, InputMediaPhoto
from pyrogram.errors import FloodWait, PeerIdInvalid
import time
import asyncio
import random
import logging
from pymongo import InsertOne
from helper_func import *
from database.database import *
from tqdm import tqdm  # Progress bar library
from config import *
from datetime import datetime, timedelta, timezone
from pyromod import listen
from bson.objectid import ObjectId
from pyrogram.enums import ParseMode
from plugins.channel_post import *

conversation_collection = conversation_collection
logger = logging.getLogger(__name__)

@Bot.on_callback_query(filters.regex("^video$"))
async def send_random_video_callback(client: Client, query: CallbackQuery):
    try:
        user_id = query.from_user.id
        user = await user_data.find_one({'_id': user_id})
        is_premium = user and user.get('premium', False)
        premium_badge = "👑 PREMIUM" if is_premium else "⭐️ FREE USER"
        user_plan = await get_user_plan_group(user_id)

        # Force Subscribe Check
        buttons = []
        force_text = (
            "⭐️ <b>Please Join Our Channels First!</b>\n"
            "1️⃣ Click the channel buttons below\n"
            "2️⃣ Join all channels\n"
            "3️⃣ Come back and try again\n"
            "Need help? Use /help command 🤝\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "⭐️ <b>कृपया पहले हमारे चैनल्स को ज्वाइन करें!</b>\n"
            "1️⃣ नीचे दिए गए चैनल बटन पर क्लिक करें\n"
            "2️⃣ सभी चैनल्स को ज्वाइन करें\n" 
            "3️⃣ वापस आकर दोबारा कोशिश करें\n"
            "मदद चाहिए? /help कमांड का उपयोग करें 🤝"
        )

        temp_buttons = []
        for i, channel in enumerate(FORCE_SUB_CHANNELS):
            try:
                chat = await client.get_chat(channel)
                try:
                    member = await client.get_chat_member(channel, user_id)
                    if member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]:
                        continue
                except Exception:
                    pass

                invite_link = client.invitelinks[i]
                btn = InlineKeyboardButton(f"👾 {chat.title}", url=invite_link)
                temp_buttons.append(btn)

                if len(temp_buttons) == 2:
                    buttons.append(temp_buttons)
                    temp_buttons = []

            except Exception as e:
                logger.error(f"Error checking subscription status for {channel}: {e}")
                continue

        if temp_buttons:
            buttons.append(temp_buttons)

        if buttons:
            await query.message.reply_photo(
                photo=FORCE_PIC,
                caption=force_text,
                reply_markup=InlineKeyboardMarkup(buttons),
                quote=True
            )
            return

        # Show category selection for videos
        keyboard = []
        temp_row = []

        for category, details in MEDIA_CATEGORIES.items():
            points = details['video']
            category_btn = InlineKeyboardButton(
                f"{details['emoji']} {category.title()} ({points} pts)",
                callback_data=f"view_video_{category}"
            )
            temp_row.append(category_btn)

            if len(temp_row) == 2:
                keyboard.append(temp_row)
                temp_row = []

        if temp_row:
            keyboard.append(temp_row)

        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="backtostart")])

        await query.message.edit_text(
            "🎥 <b>Choose Your Video Category</b>\n\n"
            "💫 Each category offers unique content\n"
            "💎 Points shown next to categories\n"
            "🔥 If You Want More Category msg @NyxKingX\n\n"
            "<i>Click any category button below 👇</i>",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        logger.error(f"Critical error in video callback: {str(e)}")
        await query.answer("⚠️ Something went wrong. Try again later!", show_alert=True)


@Bot.on_callback_query(filters.regex("^pic$"))
async def send_random_pic_callback(client: Client, query: CallbackQuery):
    try:
        user_id = query.from_user.id
        user = await user_data.find_one({'_id': user_id})

        premium_badge = "👑 PREMIUM" if is_premium else "⭐️ FREE USER"
        user_plan = await get_user_plan_group(user_id)

        # Force Subscribe Check
        buttons = []
        force_text = (
            "⭐️ <b>Please Join Our Channels First!</b>\n"
            "1️⃣ Click the channel buttons below\n"
            "2️⃣ Join all channels\n"
            "3️⃣ Come back and try again\n"
            "Need help? Use /help command 🤝\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "⭐️ <b>कृपया पहले हमारे चैनल्स को ज्वाइन करें!</b>\n"
            "1️⃣ नीचे दिए गए चैनल बटन पर क्लिक करें\n"
            "2️⃣ सभी चैनल्स को ज्वाइन करें\n" 
            "3️⃣ वापस आकर दोबारा कोशिश करें\n"
            "मदद चाहिए? /help कमांड का उपयोग करें 🤝"
        )

        temp_buttons = []
        for i, channel in enumerate(FORCE_SUB_CHANNELS):
            try:
                chat = await client.get_chat(channel)
                try:
                    member = await client.get_chat_member(channel, user_id)
                    if member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]:
                        continue
                except Exception:
                    pass

                invite_link = client.invitelinks[i]
                btn = InlineKeyboardButton(f"👾 {chat.title}", url=invite_link)
                temp_buttons.append(btn)

                if len(temp_buttons) == 2:
                    buttons.append(temp_buttons)
                    temp_buttons = []

            except Exception as e:
                logger.error(f"Error checking subscription status for {channel}: {e}")
                continue

        if temp_buttons:
            buttons.append(temp_buttons)

        if buttons:
            await query.message.reply_photo(
                photo=FORCE_PIC,
                caption=force_text,
                reply_markup=InlineKeyboardMarkup(buttons),
                quote=True
            )
            return

        # Show category selection for photos
        keyboard = []
        temp_row = []

        for category, details in MEDIA_CATEGORIES.items():
            points = details['pic']
            category_btn = InlineKeyboardButton(
                f"{details['emoji']} {category.title()} ({points} pts)",
                callback_data=f"view_photo_{category}"
            )
            temp_row.append(category_btn)

            if len(temp_row) == 2:
                keyboard.append(temp_row)
                temp_row = []

        if temp_row:
            keyboard.append(temp_row)
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="backtostart")])

        await query.message.edit_text(
            "🎥 <b>Choose Your Picture Category</b>\n\n"
            "💫 Each category offers unique content\n"
            "💎 Points shown next to categories\n"
            "🔥  If You Want More Category msg @NyxKingX\n\n"
            "<i>Click any category button below 👇</i>",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        logger.error(f"Critical error in pic callback: {str(e)}")
        await query.answer("⚠️ Something went wrong. Try again later!", show_alert=True)


