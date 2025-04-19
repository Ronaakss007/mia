import asyncio
import os
import random
import sys
import time
import logging
import imaplib
from datetime import datetime, timedelta
from plugins.admin import *
import re
import pyrogram
import string
from pyrogram.types import InputMediaVideo
import traceback
from pymongo import ASCENDING
import base64
from bson import ObjectId
from plugins.cache import *
import psutil
from pyrogram import Client, filters, __version__   
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message, InputMediaPhoto
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, PeerIdInvalid

from bot import *
from config import  *
from helper_func import *
from database.database import *
from pymongo.operations import InsertOne  # Add this line to fix the NameError
from pyrogram import Client, filters, enums
from pyrogram.types import Message, ReplyKeyboardMarkup, ReplyKeyboardRemove
from config import  *
from pyrogram.enums import ChatType 
from cachetools import TTLCache
from functools import lru_cache

@lru_cache(maxsize=1)  # Cache the result for faster access
async def get_hall_of_fame_data():
    premium_users = premium_cache["premium_users"]
    user_ids = [user['_id'] for user in premium_users[:5]]
    peer_data_list = await database.peers.find({"_id": {"$in": user_ids}}).to_list(length=len(user_ids))
    peer_map = {peer['_id']: peer['peer_id'] for peer in peer_data_list}
    user_plans = await asyncio.gather(*[get_user_plan_group(user_id) for user_id in user_ids])
    return premium_users, peer_map, user_plans

    
premium_cache = {
    "premium_users": None,
    "premium_number": None,
    "premium_badge": None,
    "last_fetched": None
}

@Bot.on_callback_query(filters.regex(r"^halloffame$"))
async def hall_of_fame(client: Bot, query: CallbackQuery):
        premium_users = premium_cache.get("premium_users", [])
        premium_number = premium_cache["premium_number"]
        if not premium_users:
            hall_of_fame = "🚀 No legendary members yet! Be the first to shine! ✨"
        else:
            user_ids = [user['_id'] for user in premium_users[:4]]

        # Fetch user plans and first names in parallel
            user_data = await asyncio.gather(
                *[get_user_plan_group(user_id) for user_id in user_ids],
                *[client.get_users(user_id) for user_id in user_ids],
                return_exceptions=True
            )

            plan_map = {user_id: plan for user_id, plan in zip(user_ids, user_data[:len(user_ids)])}
            peer_map = {peer.id: (peer.first_name or "Unknown") for peer in user_data[len(user_ids):] if isinstance(peer, pyrogram.types.User)}

            medals = ["👑", "🥈", "🥉", "🎖️"]
            hall_of_fame_lines = [
                f"{medals[index] if index < len(medals) else '🎖️'}<b> <a href='tg://user?id={user_id}'>{peer_map.get(user_id, 'Unknown')}</a> | {plan_map[user_id]}</b>"
                for index, user_id in enumerate(user_ids)
            ]
            hi_msg = await query.message.reply_text("<b>👁️ Lᴇɢᴇɴᴅs</b> 🏴‍☠️")
            await asyncio.sleep(0.5)
            await hi_msg.edit("<b>👁️‍🗨️ Lᴇɢᴇɴᴅs Aʀᴇ</b> 🕶️")
            await asyncio.sleep(0.5)
            await hi_msg.edit("<b>🔺 Lᴇɢᴇɴᴅs Aʀᴇ Hᴇʀᴇ</b> 💀")
            await asyncio.sleep(0.5)
            await hi_msg.delete()

            hall_of_fame = "🔺 <b>Tʜᴇ Cʜᴏsᴇɴ Oɴᴇ - Wᴏʀᴛʜʏ</b> 🏆\n━━━━\n" + "\n".join(hall_of_fame_lines)
            hall_of_fame += f"\n━━━━━━━━━━━━━\n<b>Tᴏᴛᴀʟ Wᴏʀᴛʜʏ Mᴇᴍʙᴇʀs : {len(premium_number)}</b>\n💀 Wᴇ Oʙsᴇʀᴠᴇ. Wᴇ Cᴏɴᴛʀᴏʟ. 💀"
            

        hall_of_fame_message = await client.send_message(
                chat_id=query.message.chat.id,
                text=hall_of_fame,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Cʟᴏsᴇ ✖ ", callback_data="close")]]
                ),
                parse_mode=enums.ParseMode.HTML
            )


@Bot.on_callback_query(filters.regex("^about$"))
async def cb_handler(client: Bot, query: CallbackQuery):
    bot_name = (await client.get_me()).first_name 
    about_pic = ABOUT_PIC  # Ensure this is a valid URL or InputFile

    caption_text = f"""
🎩 <b>{bot_name} – Tʜᴇ Cʜᴏsᴇɴ Oɴᴇ</b>

👨🏻‍💻 <i>Created by</i>: <a href="https://t.me/NyxKingX">NʏxKɪɴɢ 🔥</a>

💀 <i>Dᴇᴄᴏᴅɪɴɢ Fᴀᴛᴇ...</i>
"""


    buttons = [
        [
            InlineKeyboardButton("🛡️ Bᴀᴄᴋᴜᴘ", url="https://t.me/jffmain"),
            InlineKeyboardButton("🧾 Pʀᴏᴏғs", url="https://t.me/jffpayment")
        ],
        [
            InlineKeyboardButton("🔧 Sᴜᴘᴘᴏʀᴛ", callback_data="support"),
            InlineKeyboardButton("👁️ Rᴇᴛᴜʀɴ", callback_data="backtostart")
        ]
    ]

    try:
        await query.message.edit_media(
            media=InputMediaPhoto(media=about_pic, caption=caption_text),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except Exception as e:
        print(f"Error updating media: {e}")
        await query.message.edit_caption(caption=caption_text, reply_markup=InlineKeyboardMarkup(buttons))


@Bot.on_callback_query(filters.regex("close$"))
async def close_callback(client: Bot, query: CallbackQuery):    
    await query.message.delete()

@Bot.on_callback_query(filters.regex(r"^(redeem|redeem_\d+_\d+)$"))
async def handle_redeem(client: Bot, query: CallbackQuery):
    data = query.data

    rewards = [
        {"name": "🏆 1 Dᴀʏ Pʀᴇᴍɪᴜᴍ", "cost": 25, "time": 86400 * 1},
        {"name": "🏆 7 Dᴀʏs Pʀᴇᴍɪᴜᴍ", "cost": 99, "time": 86400 * 7},
        {"name": "🏆 1 Mᴏɴᴛʜ Pʀᴇᴍɪᴜᴍ", "cost": 249, "time": 86400 * 30},
        {"name": "🏆 3 Mᴏɴᴛʜs Pʀᴇᴍɪᴜᴍ", "cost": 649, "time": 86400 * 90},
        {"name": "🏆 6 Mᴏɴᴛʜs Pʀᴇᴍɪᴜᴍ", "cost": 999, "time": 86400 * 180},
        {"name": "🏆 1 Yᴇᴀʀ Pʀᴇᴍɪᴜᴍ", "cost": 1799, "time": 86400 * 365}
    ]

    if data == "redeem":
        if not REFER:
            await query.answer("Rᴇғᴇʀ Sʏsᴛᴇᴍ Is Cᴜʀʀᴇɴᴛʟʏ Dɪsᴀʙʟᴇᴅ.", show_alert=True)
            return

        user_id = query.from_user.id
        user = await user_data.find_one({'_id': user_id})

        if not user:
            await query.answer("🚫 You are not in the database. Please start the bot first.", show_alert=True)
            return

        referral_points = user.get('referral_points', 0)
        purchased_points = user.get('purchased_points', 0)
        total_points = referral_points + purchased_points

        # Format buttons in pairs
        buttons = [
            [
                InlineKeyboardButton(
                    f"{rewards[i]['name']}",
                    callback_data=f"redeem_{rewards[i]['cost']}_{rewards[i]['time']}"
                ),
                InlineKeyboardButton(
                    f"{rewards[i+1]['name']}",
                    callback_data=f"redeem_{rewards[i+1]['cost']}_{rewards[i+1]['time']}"
                )
            ] for i in range(0, len(rewards) - 1, 2)
        ]

        # If odd number of rewards, add the last one separately
        if len(rewards) % 2 != 0:
            buttons.append([
                InlineKeyboardButton(
                    f"{rewards[-1]['name']} ({rewards[-1]['cost']} Pᴏɪɴᴛs)",
                    callback_data=f"redeem_{rewards[-1]['cost']}_{rewards[-1]['time']}"
                )
            ])

        buttons.append([InlineKeyboardButton("Cᴀɴᴄᴇʟ ✖", callback_data="close")])
        reply_markup = InlineKeyboardMarkup(buttons)

        # Stylish reward showcase
        # reward_display = "\n".join([
        #     f"<b>{r['name']}</b>  |  💳 <b>{r['cost']} Pᴏɪɴᴛs</b>\n"
        #     f"››  {'🙋‍♂️ <b>Aᴠᴀɪʟᴀʙʟᴇ</b>\n' if total_points >= r['cost'] else '🙅🏽 <b>Nᴏᴛ Eɴᴏᴜɢʜ Pᴏɪɴᴛs</b>\n'}"
        #     for r in rewards
        # ])

        message_text = f"""
<b>🔮 Rᴇᴡᴀʀᴅ Rᴇᴅᴇᴍᴘᴛɪᴏɴ Cᴇɴᴛᴇʀ</b>

💰 <b>Yᴏᴜʀ Bᴀʟᴀɴᴄᴇ:</b> <code>{total_points}</code> Pᴏɪɴᴛs
⚡ <b>Cʟᴀɪᴍ Exᴄʟᴜsɪᴠᴇ Pʀᴇᴍɪᴜᴍ Rᴇᴡᴀʀᴅs !</b>



🔜 <b>Mᴏʀᴇ Rᴇᴡᴀʀᴅs Cᴏᴍɪɴɢ Sᴏᴏɴ !</b>
"""

        await query.message.reply_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )


    elif data.startswith("redeem_"):
        _, callback_cost, duration = data.split("_")
        duration = int(duration)

        # Fetch latest reward cost from defined rewards list
        reward = next((r for r in rewards if r["time"] == duration), None)
        if not reward:
            await query.answer("Invalid reward selection.", show_alert=True)
            return

        cost = reward["cost"]  # Ensure latest cost is used

        user_id = query.from_user.id
        user = await user_data.find_one({'_id': user_id})

        if not user:
            await query.answer("You are not in the database. Please start the bot first.", show_alert=True)
            return

        referral_points = user.get('referral_points', 0)
        purchased_points = user.get('purchased_points', 0)
        total_points = referral_points + purchased_points

        if total_points < cost:
            await query.answer("✖ Not enough points to redeem this reward.", show_alert=True)
            return

        points_to_deduct = cost
        if points_to_deduct <= referral_points:
            new_referral_points = referral_points - points_to_deduct
            new_purchased_points = purchased_points
        else:
            points_to_deduct -= referral_points
            new_referral_points = 0
            new_purchased_points = purchased_points - points_to_deduct

        await user_data.update_one({'_id': user_id}, {'$set': {'referral_points': new_referral_points, 'purchased_points': new_purchased_points}})


        time_index = next((i for i, r in enumerate(rewards) if r["time"] == duration), 0)
        await premiumreward(user_id, time_index)  # Use the correct index


        await query.answer("✅ Successfully redeemed! Premium activated.", show_alert=True)

        remaining_points = new_referral_points + new_purchased_points

        premium_badge = (
            "⚡ VIP" if duration <= 7 * 86400 else
            "🔥 Pro" if duration <= 30 * 86400 else
            "💫 Elite" if duration <= 90 * 86400 else
            "⭐ Prestige" if duration <= 180 * 86400 else
            "👑 Royal" if duration <= 365 * 86400 else
            "👑 Ultimate"
        )

        notification_text = (
            f"📢 OɴʟʏF@ɴs Aʟʙᴜᴍ Usᴇʀ Rᴇᴅᴇᴇᴍᴇᴅ A Rᴇᴡᴀʀᴅ \n"
            f"👤 User ID: [{query.from_user.first_name}](tg://user?id={user_id})\n"
            f"🎁 Rᴇᴅᴅᴇᴍᴇᴅ: {cost} Pᴏɪɴᴛs\n"
            f"⭐ Rᴇᴍᴀɪɴɪɴɢ Pᴏɪɴᴛs: {remaining_points}\n"
            f"⏳ Pʟᴀɴ Dᴜʀᴀᴛɪᴏɴ: {duration // 86400} Dᴀʏs\n"
        )

        try:
            await client.send_message(DUMB_CHAT, notification_text, parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            logger.error(f"Failed to notify bot owner: {e}")

        buttons = [[InlineKeyboardButton("⏳ Cʜᴇᴄᴋ Pʟᴀɴ", callback_data="myplan")]]

        await query.message.edit_text(
            f"🎉 <b>Congratulations!</b> 🎊\n"
            "━━━━━━━━━\n"
            f"✅ <b>{cost} Pᴏɪɴᴛs</b> Rᴇᴅᴇᴇᴍᴇᴅ Fᴏʀ Rᴇᴡᴀʀᴅ 🎁\n"
             "━━━━━\n"
            f"🏆 <b>{premium_badge} Pʀᴇᴍɪᴜᴍ Aᴄᴛɪᴠᴀᴛᴇᴅ!</b>\n"
            f"📅 <b>Duration:</b> {duration // 86400} Dᴀʏs\n"
            "🚀 <b>Enjoy Exclusive Benefits & Features!</b>\n",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.HTML
        )

@Bot.on_callback_query(filters.regex(r"^buy_point$"))
async def handle_buy_points(client: Bot, query: CallbackQuery):
    """Handles the automated buy points feature dynamically."""
    
    settings = await get_settings()
    BUY_POINT = settings.get("BUY_POINT", True)  # Fetch setting from DB
    UPI_IMAGE_URL = settings.get("UPI_IMAGE_URL")
    UPI_ID = settings.get("UPI_ID")
    SCREENSHOT_URL = settings.get("SCREENSHOT_URL")
    
    if not BUY_POINT:
        await query.answer("🚫 Pᴏɪɴᴛ Pᴜʀᴄʜᴀꜱɪɴɢ Iꜱ Cᴜʀʀᴇɴᴛʟʏ Dɪꜱᴀʙʟᴇᴅ!", show_alert=True)
        return

    try:
        # ✅ Dynamic Pricing (Fetched from Database)
        pricing = [
            {"price": 29, "points": 50, "bonus": 10},
            {"price": 49, "points": 100, "bonus": 20},
            {"price": 99, "points": 200, "bonus": 50},
            {"price": 199, "points": 400, "bonus": 100},
            {"price": 299, "points": 600, "bonus": 150},
            {"price": 499, "points": 1000, "bonus": 300},
        ]

        # ✅ Generate Pricing List Dynamically
        pricing_text = "\n".join(
            [f"💰 ₹ {p['price']}  ➜  {p['points']} Pᴏɪɴᴛs  + 🎁 {p['bonus']} Bᴏɴᴜs" for p in pricing]
        )

        # ✅ Generate Message with Dynamic Payment Details
        response = f"""
<b>👋 Hᴇʏ {query.from_user.first_name},</b>

💎 <b>Pᴏɪɴᴛs Pʀɪᴄɪɴɢ</b> 💎
━━━━━━━━━━━━━
{pricing_text}
━━━━━━━━━━━━━

📌 <b>Pᴀʏᴍᴇɴᴛ Dᴇᴛᴀɪʟs:</b>  
🆔 <b>UPI ID:</b> <code>{UPI_ID}</code>  
📸 <b>Sᴄᴀɴ QR:</b> <a href="{UPI_IMAGE_URL}">🔗 Cʟɪᴄᴋ Hᴇʀᴇ</a>

✅ <b>Hᴏᴡ Tᴏ Cʟᴀɪᴍ?</b>  
1️⃣ Mᴀᴋᴇ A Pᴀʏᴍᴇɴᴛ Uꜱɪɴɢ Tʜᴇ UPI ID Oʀ QR Cᴏᴅᴇ.  
2️⃣ Tᴀᴋᴇ A Sᴄʀᴇᴇɴꜱʜᴏᴛ Oꜰ Tʜᴇ Tʀᴀɴꜱᴀᴄᴛɪᴏɴ.  
3️⃣ Sᴇɴᴅ Tʜᴇ Sᴄʀᴇᴇɴꜱʜᴏᴛ Tᴏ Aᴅᴍɪɴ Tᴏ Rᴇᴄᴇɪᴠᴇ Pᴏɪɴᴛꜱ.  

🚀 <b>Eɴᴊᴏʏ Pʀᴇᴍɪᴜᴍ Aᴄᴄᴇꜱꜱ & Uɴʟᴏᴄᴋ Exᴄʟᴜꜱɪᴠᴇ Fᴇᴀᴛᴜʀᴇꜱ!</b>
"""

        # ✅ Interactive Buttons
        buttons = [
            # [InlineKeyboardButton("💳 Pᴀʏ Nᴏᴡ", url=f"upi://pay?pa={UPI_ID}&pn=Bot&cu=INR")],
            [InlineKeyboardButton("📸 Sᴜʙᴍɪᴛ Sᴄʀᴇᴇɴꜱʜᴏᴛ", url=SCREENSHOT_URL)],
            [
                InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="backtostart"),
                InlineKeyboardButton("✖ Cʟᴏꜱᴇ", callback_data="close"),
            ],
        ]

        # ✅ Send Payment Instructions with QR Code
        await query.message.reply_photo(
            photo=UPI_IMAGE_URL,
            caption=response,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.HTML
        )

    except Exception as e:
        await query.answer("⚠️ Sᴏᴍᴇᴛʜɪɴɢ Wᴇɴᴛ Wʀᴏɴɢ. Pʟᴇᴀꜱᴇ Tʀʏ Aɢᴀɪɴ!")
        print(f"Error in buy_point: {e}")


@Client.on_callback_query(filters.regex("^generate_token$"))
async def generate_token_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    token = generate_token()
    settings = await get_settings()
    USE_SHORTLINK = settings["USE_SHORTLINK"]
    U_S_E_P = settings.get("U_S_E_P", False)
    SHORTLINK_API_URLS = settings.get("SHORTLINK_API_URLS", [])
    SHORTLINK_API_KEYS = settings.get("SHORTLINK_API_KEYS", [])
    USE_PAYMENT = settings.get("USE_PAYMENT", False)
    UPI_ID = settings.get("UPI_ID", "ronaksaini922@ybl")  # Ensure UPI_ID is retrieved
    TUT_VID = settings.get("TUT_VID", "https://t.me/c/2396123709/2465")
    VERIFY_EXPIRE = settings.get("VERIFY_EXPIRE")
    FORCE_SUB_CHANNELS = settings["FORCE_SUB_CHANNELS"]
    SECONDS = settings.get("SECONDS", 3600)
    PAID_TIME = settings.get("PAID_TIME", 3600)

    # Get today's date
    today = datetime.utcnow().strftime("%Y-%m-%d")

    # Check how many points the user has earned today
    user_earnings = await token_collection.aggregate([
        {"$match": {"user_id": user_id, "claimed": True, "date": today}},
        {"$group": {"_id": None, "total_points": {"$sum": 10}}}
    ]).to_list(length=1)

    earned_today = user_earnings[0]["total_points"] if user_earnings else 0

    if earned_today >= 50:
        await query.answer(
            "🚫 Dᴀɪʟʏ Lɪᴍɪᴛ Rᴇᴀᴄʜᴇᴅ!\nYᴏᴜ'ᴠᴇ ᴀʟʀᴇᴀᴀᴅʏ ᴇᴀʀɴᴇᴅ 50 ᴘᴏɪɴᴛs ᴛᴏᴅᴀʏ. Tʀʏ ᴀɢᴀɪɴ ᴛᴏᴍᴏʀʀᴏᴡ!",
            show_alert=True
        )
        return

    # Generate shortlink
    shortlink = await get_reward_token(SHORTLINK_API_URLS, SHORTLINK_API_KEYS, f'https://t.me/{client.me.username}?start=daily_{token}')

    # Store token in the database
    await token_collection.insert_one({
        "user_id": user_id,
        "token": token,
        "claimed": False,
        "date": today,
        "created_at": datetime.utcnow()  # Store creation time for deletion
    })

    # Remaining points they can earn today
    remaining_points = 50 - earned_today
    progress = int((earned_today / 50) * 100)

    # Send the shortlink message with an inline button and progress bar
    text = (
        "🏆 <b>Dᴀɪʟʏ Qᴜᴇsᴛ: Lᴏᴏᴛ Hᴜɴᴛ</b> 🎯\n\n"
        f"🎮 <b>Pʟᴀʏᴇʀ:</b> <i>{query.from_user.first_name}</i>\n"
        f"📊 <b>XP Bᴏᴏsᴛ:</b> <b>{earned_today} / 50</b> Pᴏɪɴᴛs\n"
        f"🛡️ <b>Rᴇᴍᴀɪɴɪɴɢ:</b> <b>{remaining_points}</b> ᴘᴏɪɴᴛs ᴛᴏ ᴄʟᴀɪᴍ ᴛᴏᴅᴀʏ\n"
        f"📈 <b>Pʀᴏɢʀᴇss Bᴀʀ:</b> [{progress * '█'}{(100 - progress) * '░'}] {progress}%\n\n"
        "🚩 <i>Qᴜᴇsᴛ Oʙᴊᴇᴄᴛɪᴠᴇ:</i> Cʟᴀɪᴍ ʏᴏᴜʀ ʟᴏᴏᴛ ʟɪɴᴋ ᴀɴᴅ ᴘᴏᴡᴇʀ ᴜᴘ!\n\n"
        f"🔗 <b>Lᴏᴏᴛ Pᴏʀᴛᴀʟ:</b> <a href='{shortlink}'>Cʟᴀɪᴍ Yᴏᴜʀ Rᴇᴡᴀʀᴅ</a>\n\n"
        "⏳ <i>Hᴜʀʀʏ! Lɪɴᴋ sᴇʟғ-ᴅᴇsᴛʀᴜᴄᴛs ᴀғᴛᴇʀ ᴀ sʜᴏʀᴛ ᴛɪᴍᴇ!</i>\n\n"
        "<blockquote expandable>📜 Tᴇʀᴍs & Lᴏʀᴇ:\n"
        "• Mᴀx 50 Pᴏɪɴᴛs ᴘᴇʀ Dᴀʏ.\n"
        "• Lᴏᴏᴛ Lɪɴᴋs ᴇxᴘɪʀᴇ sᴏᴏɴ.\n"
        "• Wᴀᴛᴄʜ Tᴜᴛᴏʀɪᴀʟ ᴛᴏ ᴜɴʟᴏᴄᴋ ʀᴇᴡᴀʀᴅ sᴇᴄʀᴇᴛs.\n"
        "• Fᴏʀ ᴅᴇᴛᴀɪʟs ᴀɴᴅ ᴛᴜᴛᴏʀɪᴀʟ, ᴄʟɪᴄᴋ '📜 Hᴏᴡ Tᴏ Pʟᴀʏ' ʙᴇʟᴏᴡ."
        "</blockquote>"
    )

    await query.message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎯 Cʟᴀɪᴍ Lᴏᴏᴛ +10 XP", url=shortlink)],
            [InlineKeyboardButton("📜 Hᴏᴡ Tᴏ Pʟᴀʏ", callback_data="daily_point")]
        ])
    )

@Bot.on_message((filters.text & filters.regex("🤑 Unlimited Points") | filters.command(['earn', f'earn@{Bot().username}']) & not_banned & (filters.private | filters.group)))
async def generate_token_command(client, message):
    user_id = message.from_user.id
    settings = await get_settings()
    USE_SHORTLINK = settings["USE_SHORTLINK"]
    U_S_E_P = settings.get("U_S_E_P", False)
    SHORTLINK_API_URLS = settings.get("SHORTLINK_API_URLS", [])
    SHORTLINK_API_KEYS = settings.get("SHORTLINK_API_KEYS", [])
    USE_PAYMENT = settings.get("USE_PAYMENT", False)
    UPI_ID = settings.get("UPI_ID", "ronaksaini922@ybl")  # Ensure UPI_ID is retrieved
    TUT_VID = settings.get("TUT_VID", "https://t.me/c/2396123709/2465")
    VERIFY_EXPIRE = settings.get("VERIFY_EXPIRE")
    FORCE_SUB_CHANNELS = settings["FORCE_SUB_CHANNELS"]  
    SECONDS = settings.get("SECONDS", 3600)
    PAID_TIME = settings.get("PAID_TIME", 3600)
    token = generate_token()

    # Get today's date (reset at midnight UTC)
    today = datetime.utcnow().strftime("%Y-%m-%d")

    # Check how many points the user has earned today
    user_earnings = await token_collection.aggregate([
        {"$match": {"user_id": user_id, "claimed": True, "date": today}},
        {"$group": {"_id": None, "total_points": {"$sum": 10}}}
    ]).to_list(length=1)

    earned_today = user_earnings[0]["total_points"] if user_earnings else 0

    if earned_today >= 50:
        await message.reply_text(
            "🚫 <b>Daily Limit Reached</b> 🚫\n\n"
            "You've already earned <b>50 Points</b> today! 🎉\n"
            "Come back tomorrow for more rewards. ⏳",
            parse_mode=ParseMode.HTML
        )
        return

    # Generate shortlink
    shortlink = await get_reward_token(SHORTLINK_API_URLS, SHORTLINK_API_KEYS, f'https://t.me/{client.me.username}?start=daily_{token}')

    # Store token in the database with today's date and expiry timestamp
    await token_collection.insert_one({
        "user_id": user_id,
        "token": token,
        "claimed": False,
        "date": today,
        "created_at": datetime.utcnow()  # Store creation time for deletion
    })

    # Remaining points they can earn today
    remaining_points = 50 - earned_today

    # Send the shortlink to the user with updated UI
    text = (
        "🎁 <b>Daily Reward</b> 🎁\n\n"
        f"💰 <i>You have earned</i> <b>{earned_today} / 50</b> <i>points today!</i>\n"
        f"🔹 You can still earn <b>{remaining_points} more points</b> today.\n\n"
        f"🔗 <b>Reward Link:</b> <a href='{shortlink}'>Claim Now</a>\n\n"
        "⚡ <i>Hurry! Claim before the link expires.</i>"
    )

    await message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎉 Claim 10 Points", url=shortlink)],
            [InlineKeyboardButton("😵‍💫 Tᴜᴛᴏʀɪᴀʟ", callback_data="daily_point")]
        ])
    )

@Client.on_callback_query(filters.regex(r"^(myplan|myplan_refresh)$"))
async def handle_plan_queries(client: Client, query: CallbackQuery):
    try:
        user_id = query.from_user.id
        user = await user_data.find_one({'_id': user_id})

        if not user:
            await query.answer("✖ Pʟᴇᴀꜱᴇ Sᴛᴀʀᴛ Tʜᴇ Bᴏᴛ Fɪʀꜱᴛ!", show_alert=True)
            return

        # ✅ Fetch user plan details
        full_plan_text = await get_user_plan(user_id)

        # ✅ Extract plan name using improved regex
        plan_match = re.match(r"^(.*?) •", full_plan_text.strip())
        current_plan = plan_match.group(1).strip() if plan_match else "🆓 Fʀᴇᴇ Pʟᴀɴ"

        # ✅ Validate extracted plan
        if current_plan not in PLAN_BENEFITS:
            current_plan = "🆓 Fʀᴇᴇ Pʟᴀɴ"  # Default to free plan

        # ✅ Extract remaining duration safely
        remaining_duration = full_plan_text.replace(current_plan, "").strip("• ").strip()
        if not remaining_duration:
            remaining_duration = "N/A"

        # ✅ Get benefits for the current plan
        current_benefits = PLAN_BENEFITS.get(current_plan, {})
        best_plan = "👑 Uʟᴛɪᴍᴀᴛᴇ"
        best_benefits = PLAN_BENEFITS[best_plan]

        # ✅ Identify missing benefits (for comparison to Ultimate plan)
        missing_benefits = [
            f"✖ <b>{key.replace('_', ' ').title()}</b>: {current_benefits.get(key, 'N/A')} ➝ {value}"
            for key, value in best_benefits.items() if current_benefits.get(key) != value
        ]

        # ✅ Fetch the user's free media count
        free_media_count = user.get('free_media_count', 0)
        free_media_limit = FREE_MEDIA_LIMIT.get(current_plan, 2)  # Default to 2 if plan is not found

        # 🎯 **Generate Progress Bar for Free Media Usage**
        progress_percentage = (free_media_count / free_media_limit) * 10
        progress_bar = "█" * int(progress_percentage) + "░" * (10 - int(progress_percentage))

        # ✅ Construct message text with **stylish formatting**
        plan_text = f"""
💃 <b>Pʟᴀɴ Dᴇᴛᴀɪʟꜱ | {query.from_user.first_name}</b>

🗣 <b>Cᴜʀʀᴇɴᴛ Sᴛᴀᴛᴜꜱ:</b> {current_plan}
📅 <b>Rᴇᴍᴀɪɴɪɴɢ Dᴜʀᴀᴛɪᴏɴ:</b> {remaining_duration}

🔹 <b>Pʀᴇᴍɪᴜᴍ Pᴇʀᴋꜱ:</b>
🚀 <b>Sᴘᴇᴇᴅ:</b> {current_benefits.get('speed', '🔻 Nᴏʀᴍᴀʟ')}
📞 <b>Sᴜᴘᴘᴏʀᴛ:</b> {current_benefits.get('support', '🆓 Bᴀꜱɪᴄ')}
🗝️ <b>Aᴄᴄᴇꜱꜱ:</b> {current_benefits.get('access', '🛑 Lɪᴍɪᴛᴇᴅ')}
🔐 <b>Fɪʟᴇ Aᴄᴄᴇꜱꜱ:</b> {current_benefits.get('file_access', '✖ Pᴏɪɴᴛꜱ RᴇQᴜɪʀᴇᴅ')}
♾️ <b>Pᴇʀᴍᴀɴᴇɴᴛ Fɪʟᴇꜱ:</b> {current_benefits.get('permanent_files', '✖ Nᴏ')}
📥 <b>Sᴀᴠᴇᴅ Fɪʟᴇꜱ:</b> {current_benefits.get('saved_files', '✖ Nᴏ')}

⚖️ <b>Fʀᴇᴇ Mᴇᴅɪᴀ Uᴛɪʟɪᴢᴇᴅ:</b> {free_media_count}/{free_media_limit}  
<code>[{progress_bar}]</code>

🚀 <b>Bᴏᴏꜱᴛ Yᴏᴜʀ Bᴇɴᴇꜰɪᴛꜱ:</b>  
{chr(10).join(missing_benefits) if missing_benefits else "🎉 <b>Yᴏᴜ Hᴀᴠᴇ Tʜᴇ Bᴇꜱᴛ Pʟᴀɴ!</b>"}

💫 <b>Wᴀɴᴛ Mᴏʀᴇ Bᴇɴᴇꜰɪᴛꜱ?</b>  
🔥 <b>Uᴘɢʀᴀᴅᴇ Yᴏᴜʀ Pʟᴀɴ</b>  
🎁 <b>Rᴇꜰᴇʀ Fʀɪᴇɴᴅꜱ</b>  
💎 <b>Eᴀʀɴ Pᴏɪɴᴛꜱ</b>  
"""

        # ✅ Buttons with **new layout**
        buttons = [
            [
                InlineKeyboardButton("♻️ Rᴇꜰʀᴇꜱʜ", callback_data="myplan_refresh"),
                InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="backtostart"),
            ],
            [
                InlineKeyboardButton("🎁 Fʀᴇᴇ Pᴏɪɴᴛꜱ", callback_data="free_points"),
                InlineKeyboardButton("💎 Uᴘɢʀᴀᴅᴇ", callback_data="buy_prem"),
            ],
            [InlineKeyboardButton("✖ Tᴇʀᴍɪɴᴀᴛᴇ", callback_data="close")]
        ]

        # ✅ Edit message safely
        await query.message.edit_text(
            text=plan_text,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.HTML
        )

    except Exception:
        await query.answer("⚠️ Uɴᴀʙʟᴇ Tᴏ Fᴇᴛᴄʜ Pʟᴀɴ Dᴇᴛᴀɪʟꜱ. Tʀʏ Aɢᴀɪɴ!", show_alert=True)


@Bot.on_callback_query(filters.regex("^buy_prem$"))
async def buy_premium(client, query):
    settings = await get_settings()
    user_id = query.from_user.id
    user = await user_data.find_one({"_id": user_id})

    # 🔹 Fetch UPI & Pricing Details
    UPI_IMAGE_URL = settings["UPI_IMAGE_URL"]
    UPI_ID = settings["UPI_ID"]
    SCREENSHOT_URL = settings["SCREENSHOT_URL"]
    PRICE1 = settings["PRICES"]["7"]
    PRICE2 = settings["PRICES"]["30"]
    PRICE3 = settings["PRICES"]["90"]
    PRICE4 = settings["PRICES"]["180"]
    PRICE5 = settings["PRICES"]["365"]
    PRICE6 = settings["PRICES"]["730"]

    # 🔹 Fetch User's Premium Status
    premium_status = "✖ Nᴏᴛ Sᴜʙsᴄʀɪʙᴇᴅ"
    if user and user.get("premium_expiry"):
        expiry_date = datetime.utcfromtimestamp(user["premium_expiry"]).strftime('%Y-%m-%d')
        premium_status = f"✅ Aᴄᴛɪᴠᴇ ᴜɴᴛɪʟ {expiry_date}"

    # 🔹 Available Premium Plans
    premium_plans = [
        {"id": "free_trial", "price": 0, "days": 0, "benefits": "🚀 Access for 5 minutes", "is_trial": True},
        {"id": "vip_7", "name": "7 Dᴀʏs", "price": PRICE1, "days": 7, "benefits": "🚀 Faster downloads"},
        {"id": "pro_30", "name": "1 Mᴏɴᴛʜ", "price": PRICE2, "days": 30,"benefits": "🚀 Faster downloads"},
        {"id": "elite_90", "name": "3 Mᴏɴᴛʜs", "price": PRICE3, "days": 90,"benefits": "🚀 Faster downloads"},
        {"id": "prestige_180", "name": "6 Mᴏɴᴛʜs", "price": PRICE4, "days": 180,"benefits": "🚀 Faster downloads"},
        {"id": "royal_365", "name": "1 Yᴇᴀʀ", "price": PRICE5, "days": 365,"benefits": "🚀 Faster downloads"},
        {"id": "ultimate_730", "name": "Uʟᴛɪᴍᴀᴛᴇ", "price": PRICE6, "days": 730,"benefits": "🚀 Faster downloads"},
    ]

    # 🔹 Generate Inline Buttons (Grouped in Pairs)
    buttons = []
    for i in range(0, len(premium_plans), 2):
        row = []
        if premium_plans[i]['id'] == "free_trial":
            row.append(
                InlineKeyboardButton("🧪 Fʀᴇᴇ Tʀɪᴀʟ", callback_data="claim_free_trial")
            )
        else:
            row.append(
                InlineKeyboardButton(f"{premium_plans[i]['name']}", 
                callback_data=f"select_plan_{premium_plans[i]['id']}")
            )
        if i + 1 < len(premium_plans):
            if premium_plans[i + 1]['id'] != "free_trial":
                row.append(
                    InlineKeyboardButton(f"{premium_plans[i+1]['name']}", 
                                         callback_data=f"select_plan_{premium_plans[i+1]['id']}")
                )
        buttons.append(row)

    # 🔹 Payment Instructions (Styled)
    message = f"""
👁 **Tʜᴇ Oʀᴅᴇʀ Hᴀs Cʜᴏsᴇɴ Yᴏᴜ...**  

🛠 <b>Uɴᴛʀᴀᴄᴇᴀʙʟᴇ Pᴀʏᴍᴇɴᴛ Pᴏʀᴛᴀʟ</b>  
🔹 <b>Iɴɪᴛɪᴀᴛᴇ Pᴀʏᴍᴇɴᴛ:</b> <code>{UPI_ID}</code>  
🧩 <b>Aᴄᴄᴇss Kᴇʏ Vᴀʟɪᴅɪᴛʏ:</b> {premium_status}
🔻 **Sᴄᴀɴ Tᴏ Cᴏɴᴛɪɴᴜᴇ**  
<a href="{UPI_IMAGE_URL}">📸 Tʜᴇ Sᴇᴀʟ Aᴡᴀɪᴛs...</a>   

⚔️ <b>Gain Pᴀssᴘᴏʀᴛ Tᴏ Tʜᴇ Iɴɴᴇʀ Sʏɴᴅɪᴄᴀᴛᴇ</b>  
<i>Yᴏᴜʀ Mᴏᴠᴇ, Aɢᴇɴᴛ.</i>
"""

    # 🔹 Send Message with Buttons
    if query.message.photo and "Tʜᴇ Oʀᴅᴇʀ Hᴀs Cʜᴏsᴇɴ Yᴏᴜ" and "Pʀᴏᴄᴇssɪɴɢ Sʏɴᴄʜʀᴏɴɪᴢᴀᴛɪᴏɴ... "in query.message.caption:
        await query.message.edit_caption(
            caption=message,
            reply_markup=InlineKeyboardMarkup(buttons + [
                [
                    InlineKeyboardButton("📜 Mʏ Pʟᴀɴ", callback_data="myplan"),
                    InlineKeyboardButton("Tᴇʀᴍɪɴᴀᴛᴇ ✖", callback_data="close")
                ]
            ])
        )
    else:
        await query.message.reply_photo(
            photo=UPI_IMAGE_URL,
            caption=message,
            reply_markup=InlineKeyboardMarkup(buttons + [
                [
                    InlineKeyboardButton("📜 Mʏ Pʟᴀɴ", callback_data="myplan"),
                    InlineKeyboardButton("Tᴇʀᴍɪɴᴀᴛᴇ ✖", callback_data="close")
                ]
            ])
        )


@Bot.on_callback_query(filters.regex("^select_plan_"))
async def select_plan(client, query):
    settings = await get_settings()
    user_id = query.from_user.id
    plan_id = query.data.split("_", 2)[2]
    PRICE1 = settings["PRICES"]["7"]
    PRICE2 = settings["PRICES"]["30"]
    PRICE3 = settings["PRICES"]["90"]
    PRICE4 = settings["PRICES"]["180"]
    PRICE5 = settings["PRICES"]["365"]
    PRICE6 = settings["PRICES"]["730"]

    # 🔹 Define Available Plans
    premium_plans = {
        "vip_7": {"name": "⚡ 7 Dᴀʏs Vɪᴘ - Aᴄᴄᴇss Tʜᴇ Gʀɪᴅ", "price": PRICE1, "days": 7, "benefits": "<b>🕓 Iɴsᴛᴀɴᴛ Fɪʟᴇ Aᴄᴄᴇss (Zᴇʀᴏ Wᴀɪᴛ)\n🔹 Eɴᴛʀʏ Tᴏ Tʜᴇ Hɪᴅᴅᴇɴ Nᴏᴅᴇ\n🍾 Bᴏɴᴜs 50 Cʀʏᴘᴛᴏ Pᴏɪɴᴛs</b>"},
        "pro_30": {"name": "🔥 1 Mᴏɴᴛʜ Pʀᴏ ( 🏆 Bᴇsᴛ Vᴀʟᴜᴇ..! )", "price": PRICE2, "days": 30, "benefits": "<b>📥 Uɴʟɪᴍɪᴛᴇᴅ Fɪʟᴇ Dᴏᴡɴʟᴏᴀᴅs\n🔹 Aᴜᴛʜᴏʀɪᴢᴇᴅ Dᴇᴇᴘ Wᴇʙ Tᴜɴɴᴇʟs\n🍾 Bᴏɴᴜs 150 Cʀʏᴘᴛᴏ Pᴏɪɴᴛs</b>"},
        "elite_90": {"name": "💫 3 Mᴏɴᴛʜs Eʟɪᴛᴇ ( 🏆 Pᴏᴘᴜʟᴀʀ Cʜᴏɪᴄᴇ..! )", "price": PRICE3, "days": 90, "benefits": "<b>🔓 Pᴀɪᴅ Fɪʟᴇ Aᴄᴄᴇss - Nᴏ Pᴏɪɴᴛs Rᴇǫᴜɪʀᴇᴅ\n🔹 Aᴄᴄᴇss Tᴏ Eɴᴄʀʏᴘᴛᴇᴅ Sᴇʀᴠᴇʀs\n🍾 Bᴏɴᴜs 600 Cʀʏᴘᴛᴏ Pᴏɪɴᴛs</b>"},
        "prestige_180": {"name": "🌟 6 Mᴏɴᴛʜs Pʀᴇsᴛɪɢᴇ - Cᴏɴᴛʀᴏʟ Tʜᴇ Nᴇᴛ  ", "price": PRICE4, "days": 180,"benefits": "<b>📂 Pᴇʀᴍᴀɴᴇɴᴛ Fɪʟᴇ Sᴛᴏʀᴀɢᴇ\n🔹 Bʟɪɴᴅᴇᴅ Gᴏᴠᴇʀɴᴍᴇɴᴛ Tʀᴀᴄᴋᴇʀs\n🍾 Bᴏɴᴜs 1200 Cʀʏᴘᴛᴏ Pᴏɪɴᴛs</b>"},
        "royal_365": {"name": "👑 1 Yᴇᴀʀ Rᴏʏᴀʟ - Mᴀsᴛᴇʀ Oғ Tʜᴇ Sʏɴᴛʜᴇᴛɪᴄ Rᴇᴀʟɪᴛʏ", "price": PRICE5, "days": 365, "benefits": "<b>🎖 Rᴏʏᴀʟ Iᴅᴇɴᴛɪᴛʏ Bᴀᴅɢᴇ\n🔹 Pʀᴏᴛᴇᴄᴛɪᴏɴ Fʀᴏᴍ Dᴀᴛᴀ Hᴜɴᴛᴇʀs\n🍾 Bᴏɴᴜs 2500 Cʀʏᴘᴛᴏ Pᴏɪɴᴛs</b>"},
        "ultimate_730": {"name": "💀 2 Yᴇᴀʀs Uʟᴛɪᴍᴀᴛᴇ - Tʜᴇ Aʀᴄʜɪᴛᴇᴄᴛ’s Lᴇɢᴀᴄʏ", "price": PRICE6, "days": 730, "benefits": "<b>🛡 Aᴅᴍɪɴ Aᴄᴄᴇss - Cᴏɴᴛʀᴏʟ Tʜᴇ Nᴇᴛᴡᴏʀᴋ\n🔹 Eɴᴛʀʏ Tᴏ Tʜᴇ Hɪᴅᴅᴇɴ Cʏʙᴇʀ-Sʏɴᴛʜ\n🍾 Bᴏɴᴜs 5000 Cʀʏᴘᴛᴏ Pᴏɪɴᴛs</b>"},
    }

    plan = premium_plans.get(plan_id)
    if not plan:
        await query.answer("✖ Iɴᴠᴀʟɪᴅ Pʟᴀɴ!", show_alert=True)
        return

    # 🔹 Save Pending Payment in Database
    await user_data.update_one(
        {"_id": user_id},
        {"$set": {
            "pending_payment": {
                "plan_id": plan_id, 
                "price": plan["price"], 
                "days": plan["days"], 
                "timestamp": datetime.utcnow().timestamp()
            }
        }},
        upsert=True
    )

    # 🔹 Show Payment Instructions
    await query.message.edit_text(
        f"""
<b>{plan['name']}</b>  

💰 <b>Dᴀᴛᴀ Tʀᴀɴsᴀᴄᴛɪᴏɴ:</b> ₹{plan['price']}  
📅 <b>Aᴄᴄᴇss Vᴀʟɪᴅɪᴛʏ:</b> {plan['days']} ᴅᴀʏs

🕶 **Bᴇɴᴇғɪᴛs:**  
{plan['benefits']}     

🔄 <i>Pʀᴏᴄᴇssɪɴɢ Sʏɴᴄʜʀᴏɴɪᴢᴀᴛɪᴏɴ...  
Cʟɪᴄᴋ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ᴛᴏ ᴠᴇʀɪғʏ ᴘʀᴏᴄᴇss.</i>
        """,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("👁 Vᴇʀɪғʏ", callback_data="check_payment"),
                InlineKeyboardButton("🔄 Rᴇᴄᴏᴅᴇ Pʟᴀɴ", callback_data="buy_prem")
            ]
        ])
    )

@Bot.on_callback_query(filters.regex("^check_payment$"))
async def check_payment(client, query):
    await query.answer("🔄 Cʜᴇᴄᴋɪɴɢ Pᴀʏᴍᴇɴᴛ, Pʟᴇᴀsᴇ Wᴀɪᴛ...", show_alert=False)
    settings = await get_settings()
    user_id = query.from_user.id
    user = await user_data.find_one({"_id": user_id})

    if not user or "pending_payment" not in user:
        await query.answer("✖ Nᴏ Pᴇɴᴅɪɴɢ Pᴀʏᴍᴇɴᴛ Fᴏᴜɴᴅ.", show_alert=True)
        return

    plan_info = user["pending_payment"]
    plan_price = plan_info["price"]
    plan_days = plan_info.get("days")

    if not plan_days:
        await query.answer("✖ Pʟᴀɴ Dᴇᴛᴀɪʟs Mɪssɪɴɢ. Cᴏɴᴛᴀᴄᴛ Sᴜᴘᴘᴏʀᴛ.", show_alert=True)
        return

    # ✅ Fᴇᴛᴄʜ UPI Tʀᴀɴsᴀᴄᴛɪᴏɴs
    transactions = await fetch_upi_payments()
    if not transactions:
        await query.answer("✖ Nᴏ Nᴇᴡ Pᴀʏᴍᴇɴᴛs Fᴏᴜɴᴅ. Tʀʏ Aɢᴀɪɴ Lᴀᴛᴇʀ.", show_alert=True)
        return

    # ✅ Gᴇᴛ Lɪsᴛ Oғ Aʟʀᴇᴀᴅʏ Usᴇᴅ Tʀᴀɴsᴀᴄᴛɪᴏɴs
    used_txns = {txn["reference_id"] async for txn in used_transactions.find({}, {"reference_id": 1})}

    for txn in transactions:
        txn_id = txn["reference_id"]
        txn_amount = txn["amount"]

        # ✅ Cʜᴇᴄᴋ Iғ Tʀᴀɴsᴀᴄᴛɪᴏɴ Wᴀs Aʟʀᴇᴀᴅʏ Pʀᴏᴄᴇssᴇᴅ
        if txn_id in used_txns:
            continue  # Sᴋɪᴘ Aʟʀᴇᴀᴅʏ Usᴇᴅ Pᴀʏᴍᴇɴᴛs

        # ✅ Mᴀᴛᴄʜ Bᴏᴛʜ Tʜᴇ Tʀᴀɴsᴀᴄᴛɪᴏɴ ID & Aᴍᴏᴜɴᴛ
        if txn_amount == float(plan_price):
            # ✅ Sᴛᴏʀᴇ Tʀᴀɴsᴀᴄᴛɪᴏɴ Bᴇғᴏʀᴇ Aᴄᴛɪᴠᴀᴛɪɴɢ Pʀᴇᴍɪᴜᴍ
            await used_transactions.insert_one({
                "reference_id": txn_id,
                "amount": txn_amount,
                "user_id": user_id,
                "redeemed": True  # Mᴀʀᴋ As Usᴇᴅ
            })

            # ✅ Cʜᴇᴄᴋ Cᴜʀʀᴇɴᴛ Pʀᴇᴍɪᴜᴍ Sᴛᴀᴛᴜs
            current_time = int(time.time())  # Gᴇᴛ Cᴜʀʀᴇɴᴛ Tɪᴍᴇsᴛᴀᴍᴘ
            if user.get("premium") and user.get("premium_expiry", 0) > current_time:
                new_expiry = user["premium_expiry"] + (plan_days * 86400)  # Aᴅᴅ ᴅᴀʏs ᴛᴏ ᴄᴜʀʀᴇɴᴛ ᴇxᴘɪʀʏ
            else:
                new_expiry = current_time + (plan_days * 86400)  # Sᴇᴛ ᴇxᴘɪʀʏ ғʀᴏᴍ ɴᴏᴡ

            # ✅ Uᴘᴅᴀᴛᴇ Pʀᴇᴍɪᴜᴍ Sᴛᴀᴛᴜs ᴏɴ Dᴀᴛᴀʙᴀsᴇ
            await autopayment(user_id, plan_days)

            expiry_date = datetime.utcfromtimestamp(new_expiry).strftime('%Y-%m-%d')

            # ✅ Rᴇᴍᴏᴠᴇ Pᴇɴᴅɪɴɢ Pᴀʏᴍᴇɴᴛ Rᴇǫᴜᴇsᴛ
            await user_data.update_one({"_id": user_id}, {"$unset": {"pending_payment": ""}})

            user = await user_data.find_one({"_id": user_id})
            expiry_date = datetime.utcfromtimestamp(user["premium_expiry"]).strftime('%Y-%m-%d')

            # 🔔 Nᴏᴛɪғʏ Oᴡɴᴇʀ
            owner_message = (
                f"👁‍🗨 **Iʟʟᴜᴍɪɴᴀᴛɪ Aᴄᴛɪᴠᴀᴛɪᴏɴ!**\n"
                f"⚡ <b>Uɴɪᴛ Iᴅᴇɴᴛɪꜰɪᴇᴅ:</b> <a href='tg://user?id={user_id}'>{user.get('first_name', 'Uɴɪᴛ')}</a>\n"
                f"💰 **Tʀᴀɴsᴀᴄᴛɪᴏɴ Vᴀʟᴜᴇ:** ₹{plan_price}\n"
                f"⏳ **Oᴘᴇʀᴀᴛɪᴏɴᴀʟ Pᴇʀɪᴏᴅ:** {plan_days} Dᴀʏs\n"
                f"📅 **Sᴇʀᴠɪᴄᴇ Tᴇʀᴍɪɴᴀᴛɪᴏɴ:** {expiry_date}\n"
                f"🆔 **Dᴇᴄᴏᴅᴇᴅ Tʀᴀɴsᴀᴄᴛɪᴏɴ ID:** `{txn_id}`"
            )
            await client.send_message(DUMB_CHAT, owner_message)

            # 🎉 Sᴇɴᴅ Nᴇᴡ Pʀᴇᴍɪᴜᴍ Aᴄᴛɪᴠᴀᴛɪᴏɴ Mᴇssᴀɢᴇ
            await query.message.reply_text(
                f"🔺 **Iɴɪᴛɪᴀᴛɪɴɢ Pʀᴇᴍɪᴜᴍ Pʀᴏᴛᴏᴄᴏʟ...**\n\n"
                f"🆔 <b>Uɴɪᴛ ID:</b> <code>{user_id}</code>\n"
                f"💎 <b>Sᴇʟᴇᴄᴛᴇᴅ Pʟᴀɴ:</b> <code>{plan_info['days']} Dᴀʏs</code>\n"
                f"💰 <b>Tʀᴀɴsᴀᴄᴛɪᴏɴ Aᴍᴏᴜɴᴛ:</b> ₹{plan_price}\n"
                f"📆 <b>Vᴀʟɪᴅɪᴛʏ Uɴᴛɪʟ:</b> <code>{expiry_date}</code>\n\n"
                f"🔹 <b>Aᴄᴄᴇss Gʀᴀɴᴛᴇᴅ. Wᴇʟᴄᴏᴍᴇ Tᴏ Tʜᴇ Iɴɴᴇʀ Cɪʀᴄʟᴇ. 🔺</b>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📜 Mʏ Aᴄᴄᴇss", callback_data="myplan"),
                     InlineKeyboardButton("Tᴇʀᴍɪɴᴀᴛᴇ", callback_data="close")]
                ])
            )
            return

    # ✖ Nᴏ Mᴀᴛᴄʜɪɴɢ Pᴀʏᴍᴇɴᴛ Fᴏᴜɴᴅ
    await query.message.edit_text(
        "👁‍🗨 **Iɴᴛᴇʀᴄᴇᴘᴛɪᴏɴ Aʟᴇʀᴛ!**\n"
        "✖ <b>Nᴏ Vᴀʟɪᴅ Tʀᴀɴsᴀᴄᴛɪᴏɴ Dᴇᴛᴇᴄᴛᴇᴅ.</b>\n\n"
        "📤 <b>Uᴘʟᴏᴀᴅ Pᴀʏᴍᴇɴᴛ Eᴠɪᴅᴇɴᴄᴇ ғᴏʀ Mᴀɴᴜᴀʟ Vᴇʀɪғɪᴄᴀᴛɪᴏɴ:</b>",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📸 Uᴘʟᴏᴀᴅ Pʀᴏᴏғ", url=settings["SCREENSHOT_URL"]),
             InlineKeyboardButton("🔄 Rᴇᴀɴᴀʟʏᴢᴇ", callback_data="check_payment")],
            [InlineKeyboardButton("🔙 Rᴇᴛᴜʀɴ Tᴏ Sʏsᴛᴇᴍ", callback_data="buy_prem")]
        ])
    )

@Bot.on_callback_query(filters.regex("^claim_free_trial$"))
async def claim_free_trial(client, query):
    user_id = query.from_user.id
    user = await user_data.find_one({"_id": user_id})

    # Check if the user has already claimed the free trial
    if user and user.get("free_trial_claimed", False):
        await query.answer("✖ Aʟʀᴇᴀᴅʏ Cʟᴀɪᴍᴇᴅ..", show_alert=True)
        return

    # Set the premium status for 10 minutes (Free Trial)
    current_time = int(time.time())
    new_expiry = current_time + (10 * 60)  # 10 minutes from now

    # Call freetrial to activate free trial and set premium status
    await freetrial(user_id, 0)  # Use 0 to signify the 10-minute free trial

    # Update the user's premium status in the database
    await user_data.update_one(
        {"_id": user_id},
        {
            "$set": {
                "premium": True,
                "premium_expiry": new_expiry,
                "free_trial_claimed": True  # Mark as claimed
            }
        }
    )

    # Send a message to the user after claiming the trial
    await query.message.reply_text(
        "✅ Aᴄᴄᴇss Gʀᴀɴᴛᴇᴅ!\n"
        "🔥 Yᴏᴜ ʜᴀᴠᴇ sᴜᴄᴄᴇssғᴜʟʟʏ ᴄʟᴀɪᴍᴇᴅ ᴛʜᴇ ғʀᴇᴇ ᴛʀɪᴀʟ!\n\n"
        "⏳ Tʀɪᴀʟ Dᴜʀᴀᴛɪᴏɴ: 10 Mɪɴᴜᴛᴇs\n"
        "🛡️ Aɴᴏɴʏᴍᴏᴜs ID: 0xF7A9B\n"
        "🚀 Sʏsᴛᴇᴍ Aᴄᴛɪᴠᴀᴛᴇᴅ. Eɴᴊᴏʏ ʏᴏᴜʀ ᴀᴄᴄᴇss!"
    )

    # Notify the dump chat about the free trial claim
    dump_chat_id = DUMB_CHAT  # Replace with your actual dump chat ID
    await client.send_message(
        dump_chat_id,
        f"👁‍🗨 **Free Trial Claimed!**\n"
        f"🆔 **User ID:** <code>{user_id}</code>\n"
        f"🎉 **User has claimed a free trial for 10 minutes.**"
    )

@Bot.on_callback_query(filters.regex(r"^(show_premium_users|delete_premium|delete_premium_.*|confirm_delete_.*|add_prem|set_prem_.*)$"))
async def handle_premium_management(client: Bot, query: CallbackQuery):
    data = query.data
    
    if data == "show_premium_users":
        if query.from_user.id != OWNER_ID:
            await query.answer("You are not authorized to view this.", show_alert=True)
            return
        try:
            premium_users = await get_premium_users()
            # print("DEBUG: Premium Users Data:", premium_users)
            if not premium_users:
                await query.message.reply_text("No premium users found.")
                return

            text = "Premium Users:\n\n"
            for user_id, username, remaining_time, premium_status in premium_users:  # ✅ Correct
                try:
                    user = await client.get_users(user_id)
                    text += f"User: @{user.username} (ID: {user_id})\nFirst Name: {user.first_name}\nStatus: {premium_status}\nExpires in: {remaining_time}\n\n"
                except PeerIdInvalid:
                    text += f"User ID: {user_id}\nUsername: {username}\nStatus: {premium_status}\nExpires in: {remaining_time}\n\n"

            await query.message.reply_text(
                text=text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Cʟᴏꜱᴇ", callback_data="close")]
                ])
            )
        except Exception as e:
            print(f"Error fetching premium users: {e}")

    elif data == "delete_premium":
        if query.from_user.id != OWNER_ID:
            await query.answer("You are not authorized to perform this action.", show_alert=True)
            return
            
        premium_users = await get_premium_users()
        if not premium_users:
            await query.message.reply_text("No premium users found.")
            return

        buttons = []
        for user_id, username, remaining_time,premium_status  in premium_users:
            try:
                user = await client.get_users(user_id)
                buttons.append([InlineKeyboardButton(f"Delete @{user.username} ({user.first_name})", callback_data=f"delete_premium_{user_id}")])
            except PeerIdInvalid:
                buttons.append([InlineKeyboardButton(f"Delete User ID: {user_id}", callback_data=f"delete_premium_{user_id}")])

        await query.message.reply_text(
            text="Select a user to delete their premium plan:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("delete_premium_"):
        if query.from_user.id != OWNER_ID:
            await query.answer("You are not authorized to perform this action.", show_alert=True)
            return
            
        user_id = int(data.split("_")[2])
        try:
            user = await client.get_users(user_id)
            await query.message.reply_text(
                text=f"Are you sure you want to delete the premium plan for user @{user.username} ({user.first_name})?",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("Yes", callback_data=f"confirm_delete_{user_id}"),
                        InlineKeyboardButton("No", callback_data="close")
                    ]
                ])
            )
        except PeerIdInvalid:
            await query.message.reply_text(
                text=f"Are you sure you want to delete the premium plan for user ID: {user_id}?",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("Yes", callback_data=f"confirm_delete_{user_id}"),
                        InlineKeyboardButton("No", callback_data="close")
                    ]
                ])
            )
    elif data.startswith("confirm_delete_"):
        if query.from_user.id != OWNER_ID:
            await query.answer("You are not authorized to perform this action.", show_alert=True)
            return
            
        user_id = int(data.split("_")[2])
        try:
            await update_verify_status(user_id, is_verified=False, verified_time=0)
            await user_data.update_one({'_id': user_id}, {'$set': {'premium': False, 'premium_expiry': 0,'premium_status': '⚡ Free'}})
            
            try:
                user = await client.get_users(user_id)
                await query.message.reply_text(f"Premium plan for user @{user.username} ({user.first_name}) has been deleted.")
            except PeerIdInvalid:
                await query.message.reply_text(f"Premium plan for user ID: {user_id} has been deleted.")
                
            await asyncio.sleep(5)
            await query.message.delete()
        except Exception as e:
            print(f"Error deleting premium plan: {e}")

    elif data == "add_prem":
        if query.from_user.id != OWNER_ID:
            await query.answer("You are not authorized to perform this action.", show_alert=True)
            return
            
        await query.message.reply_text(
            text="Please enter the user ID to add premium:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Cancel", callback_data="close")]
            ])
        )
        
        user_id = await client.listen(query.message.chat.id)
        if user_id.text == "/cancel":
            await user_id.reply("Cancelled 😉!")
            await asyncio.sleep(5)
            await query.message.delete()
            return
            
        user_id = int(user_id.text)

        await query.message.reply_text(
            text="Please select the duration for the premium plan, If Button Did Not Work Send TEXT AS \n 0 for 1 Hour\n 1 for 7 Days\n 2 for 1 Month\n 3 for 3 Months \n 4 for 6 Months\n 5 for 1 Year\n6 for Custom Plan (Enter number of days): :",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("1 hour", callback_data=f"set_prem_{user_id}_0"),
                    InlineKeyboardButton("7 days", callback_data=f"set_prem_{user_id}_1")
                ],
                [
                    InlineKeyboardButton("1 month", callback_data=f"set_prem_{user_id}_2"),
                    InlineKeyboardButton("3 months", callback_data=f"set_prem_{user_id}_3")
                ],
                [
                    InlineKeyboardButton("6 months", callback_data=f"set_prem_{user_id}_4"),
                    InlineKeyboardButton("1 year", callback_data=f"set_prem_{user_id}_5"),
                    InlineKeyboardButton("Custom Plan", callback_data=f"set_prem_{user_id}_6")
                ],
                [InlineKeyboardButton("Cancel", callback_data="close")]
            ])
        )

        duration = await client.listen(query.message.chat.id)
        if duration.text == "/cancel":
            await duration.reply("Cancelled 😉!")
            await asyncio.sleep(5)
            await query.message.delete()
            return

        if duration.text == "6":
            await query.message.reply_text("Please enter the number of days for the custom plan:")
            custom_days = await client.listen(query.message.chat.id)
            if custom_days.text == "/cancel":
                await custom_days.reply("Cancelled 😉!")
                await asyncio.sleep(5)
                await query.message.delete()
                return
            try:
                duration = int(custom_days.text)
            except ValueError:
                await query.message.reply_text("Invalid number of days. Please try again.")
                return
        else:
            duration = int(duration.text)

        duration_days = [1/24, 7, 30, 90, 180, 365][duration] if duration < 6 else duration  # 1 hour = 1/24 days

        from datetime import timezone as tz 
        expiry_utc = datetime.now(tz.utc) + timedelta(days=duration_days)
        ist = pytz.timezone("Asia/Kolkata")
        expiry_ist = expiry_utc.astimezone(ist).strftime('%Y-%m-%d %H:%M:%S')

        timestring = ["1 Hᴏᴜʀ", "7 Dᴀʏs", "1 Mᴏɴᴛʜ", "3 Mᴏɴᴛʜ", "6 Mᴏɴᴛʜ", "1 Yᴇᴀʀ"][duration] if duration < 6 else f"{duration} Days"

        try:
            await increasepremtime(user_id, duration)
            await query.message.reply_text(f"Premium plan of {timestring} added to user {user_id}.")

            try:
                user = await client.get_users(user_id)
                await client.send_message(
                    chat_id=user_id,
                    text=f"Cᴏɴɢʀᴀᴛᴜʟᴀᴛɪᴏɴ 🎉\n\n"
                         f"🎖 **Yᴏᴜʀ Pʀᴇᴍɪᴜᴍ Pʟᴀɴ:** `{timestring}`\n"
                         f"🕐 **Eɴᴅs Oɴ:** `{expiry_ist}`\n\n"
                         "<b>Yᴏᴜʀ Bᴇɴᴇғɪᴛs:</b>\n"
                         f"✔ Aᴅs-Fʀᴇᴇ Exᴘᴇʀɪᴇɴᴄᴇ\n"
                         f"✔ Uɴʟɪᴍɪᴛᴇᴅ Cᴏɴᴛᴇɴᴛ Aᴄᴄᴇss\n"
                         f"✔ Dɪʀᴇᴄᴛ Fɪʟᴇ Dᴏᴡɴʟᴏᴀᴅs\n"
                         f"✔ Sᴀᴠᴇ Tᴏ Gᴀʟʟᴇʀʏ\n",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔍 Vɪᴇᴡ Pʟᴀɴ", callback_data="myplan")]
                    ])
                )
            except PeerIdInvalid:
                pass

            await asyncio.sleep(5)
            await query.message.delete()
        except Exception as e:
            print(f"Error adding premium plan: {e}")


@Bot.on_callback_query(filters.regex(r"^set_prem_\d+_\d+$"))
async def handle_set_prem_callback(client, query):
    try:
        print(f"Processing callback: {query.data}")  # Debugging
        data_parts = query.data.split("_")  
        user_id = int(data_parts[2])  
        duration_index = int(data_parts[3])  

        # Define duration mapping - convert index to actual days
        duration_days = [1/24, 7, 30, 90, 180, 365][duration_index] if duration_index < 6 else duration_index  

        from datetime import timezone as tz
        expiry_utc = datetime.now(tz.utc) + timedelta(days=duration_days)
        ist = pytz.timezone("Asia/Kolkata")
        expiry_ist = expiry_utc.astimezone(ist).strftime('%Y-%m-%d %H:%M:%S')

        timestring = ["1 Hᴏᴜʀ", "7 Dᴀʏs", "1 Mᴏɴᴛʜ", "3 Mᴏɴᴛʜs", "6 Mᴏɴᴛʜs", "1 Yᴇᴀʀ"][duration_index] if duration_index < 6 else f"{duration_index} Dᴀʏs"

        # ✅ Update user premium status - FIXED: Pass the actual duration in days
        await increasepremtime(user_id, duration_days)

        # ✅ Edit the message for confirmation
        await query.message.edit_text(f"✅ Pʀᴇᴍɪᴜᴍ Pʟᴀɴ `{timestring}` Aᴅᴅᴇᴅ Tᴏ Usᴇʀ `{user_id}`.")

        # ✅ Notify the user
        try:
            user = await client.get_users(user_id)
            await client.send_message(
                chat_id=user_id,
                text=f"Cᴏɴɢʀᴀᴛᴜʟᴀᴛɪᴏɴ 🎉\n\n"
                     f"🎖 **Yᴏᴜʀ Pʀᴇᴍɪᴜᴍ Pʟᴀɴ:** `{timestring}`\n"
                     f"🕐 **Eɴᴅs Oɴ:** `{expiry_ist}`\n\n"
                     "<b>Yᴏᴜʀ Bᴇɴᴇғɪᴛs:</b>\n"
                     f"✔ Aᴅs-Fʀᴇᴇ Exᴘᴇʀɪᴇɴᴄᴇ\n"
                     f"✔ Uɴʟɪᴍɪᴛᴇᴅ Cᴏɴᴛᴇɴᴛ Aᴄᴄᴇss\n"
                     f"✔ Dɪʀᴇᴄᴛ Fɪʟᴇ Dᴏᴡɴʟᴏᴀᴅs\n"
                     f"✔ Sᴀᴠᴇ Tᴏ Gᴀʟʟᴇʀʏ\n",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔍 Vɪᴇᴡ Pʟᴀɴ", callback_data="myplan")]
                ])
            )
        except PeerIdInvalid:
            print("User chat is not available.")

        await query.answer("✅ Premium Plan Updated!")  # Send an acknowledgment to avoid Telegram error
    except Exception as e:
        print(f"Error in callback: {e}")
        await query.answer("⚠️ Something went wrong!", show_alert=True)


from traceback import format_exc

@Bot.on_callback_query(filters.regex(r"^premium$"))
async def handle_premium_section(client: Bot, query: CallbackQuery):

    await query.answer()

    bot_name = (await client.get_me()).first_name  # Dynamically fetch bot name

    # Updated premium buttons with consistent small caps
    premium_buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📜 Sʜᴏᴡ Pʀᴇᴍɪᴜᴍ Uꜱᴇʀꜱ", callback_data="show_premium_users")
        ],
        [
            InlineKeyboardButton("➕ Aᴅᴅ Pʀᴇᴍɪᴜᴍ Uꜱᴇʀ", callback_data="add_prem"),
            InlineKeyboardButton("🗑 Dᴇʟᴇᴛᴇ Pʀᴇᴍɪᴜᴍ Uꜱᴇʀ", callback_data="delete_premium")
        ],
        [
            InlineKeyboardButton("Cʟᴏꜱᴇ ✖", callback_data="close")
        ]
    ])

    caption_text = f"""💎 <b>{bot_name} - Pʀᴇᴍɪᴜᴍ Sᴇᴄᴛɪᴏɴ</b>
━━━━━━━━━━━━━━━━━━━
👑 Wᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ OɴʟʏF@ɴs Aʟʙᴜᴍ Pʀᴇᴍɪᴜᴍ Sᴇᴄᴛɪᴏɴ.
📌 Hᴇʀᴇ ʏᴏᴜ ᴄᴀɴ ᴍᴀɴᴀɢᴇ Pʀᴇᴍɪᴜᴍ Uꜱᴇʀꜱ.
━━━━━━━━━━━━━━━━━━━"""

    try:
        await client.send_message(chat_id=query.message.chat.id, text="💎")
        await query.message.reply_photo(
            photo=PREMIUM_IMG,
            caption=caption_text,
            reply_markup=premium_buttons
        )
    except Exception as e:
        print(f"Error sending premium logic:\n{format_exc()}")  # Logs full traceback

@Client.on_message(filters.command("premium") & filters.user(ADMINS))
async def premium_section(client, message):
    try:
        premium_buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🐦‍🔥 Sʜᴏᴡ Pʀᴇᴍɪᴜᴍ Usᴇʀs", callback_data="show_premium_users")
            ],
            [
                InlineKeyboardButton("➕ Aᴅᴅ Pʀᴇᴍɪᴜᴍ Usᴇʀ", callback_data="add_prem"),
                InlineKeyboardButton("➖ Dᴇʟᴇᴛᴇ Pʀᴇᴍɪᴜᴍ Usᴇʀ", callback_data="delete_premium")
            ],
            [
                InlineKeyboardButton("🤖 Cʟᴏꜱᴇ", callback_data="close")
            ]
        ])

        caption_text = "Wᴇʟᴄᴏᴍᴇ Tᴏ Tʜᴇ Pʀᴇᴍɪᴜᴍ Sᴇᴄᴛɪᴏɴ. Hᴇʀᴇ Yᴏᴜ Cᴀɴ Mᴀɴᴀɢᴇ Pʀᴇᴍɪᴜᴍ Usᴇʀs."
        await message.reply_photo(
            photo=PREMIUM_IMG,
            caption=caption_text,
            reply_markup=premium_buttons
        )
    except Exception as e:
        print(f"Error sending premium logic: {e}")



async def start_check_expired_plans(bot_instance):
    await check_expired_plans(bot_instance)

@Client.on_callback_query(filters.regex(r"^refer_(\d+)$"))
async def refresh_refer_callback(client: Client, query: CallbackQuery):
    user_id = int(query.matches[0].group(1))  # Extract user ID from callback_data

    user = await user_data.find_one({'_id': user_id})

    if not user:
        await query.answer("✖ You are not in the database!", show_alert=True)
        return

    referrals = user.get('referrals', [])
    referral_count = len(referrals) if isinstance(referrals, list) else 0
    referral_points = referral_count * REFERRAL_REWARD  

    # Calculate Bonus from Tiers
    bonus_points = sum(points for ref, points in referral_tiers.items() if referral_count >= ref)
    total_referral_points = referral_points + bonus_points  

    purchased_points = user.get('purchased_points', 0)
    total_points = total_referral_points + purchased_points

    referral_link = f"https://t.me/{client.me.username}?start=refer={user_id}"

    # Progress Bar
    next_tier = min((tier for tier in referral_tiers.keys() if referral_count < tier), default=None)
    progress = progress_bar(referral_count, next_tier if next_tier else referral_count + 5)

    new_caption = f"""
🎉 <b>Hᴇʏ {query.from_user.mention}, Yᴏᴜ Aʀᴇ A Lᴏʏᴀʟ Mᴇᴍʙᴇʀs..!</b>

🔗 <b>Yᴏᴜʀ Gᴏʟᴅᴇɴ Lɪɴᴋ:</b> 
<code>{referral_link}</code>

1 Rᴇғᴇʀ = {REFERRAL_REWARD} Pᴏɪɴᴛ

👥 <b>Fᴏʟʟᴏᴡᴇʀs:</b> <code>{referral_count}</code> | 💰 <b>Rᴇᴡᴀʀᴅs:</b> <code>{total_points}</code>
🎁 <b>VIP Bᴏɴᴜs:</b> <code>{bonus_points}</code>
💎 <b>Pᴜʀᴄʜᴀsᴇᴅ Pᴏɪɴᴛs:</b> <code>{purchased_points}</code>

🏆 <b>Pʀᴏɢʀᴇss:</b> {progress}
{f"🎯 <i>Nᴇxᴛ Rᴏʏᴀʟ Bᴏɴᴜs ᴀᴛ {next_tier} ʀᴇғᴇʀʀᴀʟs (+{referral_tiers[next_tier]} ᴘᴏɪɴᴛs)</i>" if next_tier else "🎯 <i>Aʟʟ Tɪᴇʀs Rᴇᴀᴄʜᴇᴅ!</i>"}
"""

    buttons = [
        [InlineKeyboardButton("🔮 Sʜᴀʀᴇ Mʏ Mᴀɢɪᴄᴀʟ Lɪɴᴋ", url=f"https://t.me/share/url?url={referral_link}")],
        [
            InlineKeyboardButton("🚀 Uᴘɢʀᴀᴅᴇ Rᴇᴡᴀʀᴅs", callback_data="redeem"),
            InlineKeyboardButton("💎 Bᴜʏ Pᴏɪɴᴛs", callback_data="buy_point"),
        ],
        [InlineKeyboardButton("📜 Rᴇғᴇʀʀᴀʟ Tᴜᴛᴏʀɪᴀʟ", callback_data="watch_tutorial"),
        InlineKeyboardButton("🔙 Rᴇᴛᴜʀɴ",callback_data="backtostart")]  # Make button refresh data
    ]

    # ✅ **Check if the caption is different before editing**
    current_caption = query.message.caption if query.message.caption else ""
    
    if new_caption.strip() != current_caption.strip():
        await query.message.edit_caption(
            caption=new_caption,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.HTML
        )
    else:
        await query.answer("✅ Already Up-to-Date!", show_alert=True)



@Bot.on_message(
    (filters.text & filters.regex("🫨 Refer") | filters.command(['refer', f'refer@{Bot().username}']))
    & not_banned & (filters.private | filters.group)
)
async def refer_command(client: Client, message):
    try:
        user_id = message.from_user.id
        user = await user_data.find_one({'_id': user_id})

        if not user:
            await message.reply_text("✖ Yᴏᴜ Aʀᴇ Nᴏᴛ Iɴ Tʜᴇ Dᴀᴛᴀʙᴀsᴇ.\nPʟᴇᴀsᴇ Sᴛᴀʀᴛ Tʜᴇ Bᴏᴛ Fɪʀsᴛ!")
            return

        # ✅ Retrieve User Referral Data
        referrals = user.get('referrals', [])
        referrals = referrals if isinstance(referrals, list) else []

        referral_count = len(referrals)
        referral_points = referral_count * REFERRAL_REWARD  

        # ✅ Calculate Bonus Points from Tiers
        bonus_points = sum(points for ref, points in referral_tiers.items() if referral_count >= ref)
        total_referral_points = referral_points + bonus_points  

        # ✅ Add Purchased Points
        purchased_points = user.get('purchased_points', 0)
        total_points = total_referral_points + purchased_points

        # ✅ Generate Referral Link
        referral_link = f"https://t.me/{client.me.username}?start=refer={user_id}"

        # ✅ Determine Next Bonus Tier
        next_tier = min((tier for tier in referral_tiers.keys() if referral_count < tier), default=None)
        progress = progress_bar(referral_count, next_tier if next_tier else referral_count + 5)

        # ✅ Generate Dynamic Message
        response = f"""
🎉 <b>Hᴇʏ {message.from_user.mention}, Yᴏᴜ Aʀᴇ A Lᴏʏᴀʟ Mᴇᴍʙᴇʀs..!</b>

🔗 <b>Yᴏᴜʀ Gᴏʟᴅᴇɴ Lɪɴᴋ:</b> 
<code>{referral_link}</code>

1 Rᴇғᴇʀ = {REFERRAL_REWARD} Pᴏɪɴᴛ

👥 <b>Fᴏʟʟᴏᴡᴇʀs:</b> <code>{referral_count}</code> | 💰 <b>Rᴇᴡᴀʀᴅs:</b> <code>{total_points}</code>
🎁 <b>VIP Bᴏɴᴜs:</b> <code>{bonus_points}</code>
💎 <b>Pᴜʀᴄʜᴀsᴇᴅ Pᴏɪɴᴛs:</b> <code>{purchased_points}</code>

🏆 <b>Pʀᴏɢʀᴇss:</b> {progress}
{f"🎯 <i>Nᴇxᴛ Rᴏʏᴀʟ Bᴏɴᴜs ᴀᴛ {next_tier} ʀᴇғᴇʀʀᴀʟs (+{referral_tiers[next_tier]} ᴘᴏɪɴᴛs)</i>" if next_tier else "🎯 <i>Aʟʟ Tɪᴇʀs Rᴇᴀᴄʜᴇᴅ!</i>"}
"""

        # ✅ Buttons with Animated Icons 🆕
        buttons = [
            [InlineKeyboardButton("🚀 Sʜᴀʀᴇ Lɪɴᴋ", url=f"https://t.me/share/url?url={referral_link}")],
            [
                InlineKeyboardButton("🎁 Rᴇᴅᴇᴇᴍ", callback_data="redeem"),
                InlineKeyboardButton("💎 Bᴜʏ Pᴏɪɴᴛꜱ", callback_data="buy_point"),
                InlineKeyboardButton("⚡ Tᴜᴛᴏʀɪᴀʟ", callback_data="watch_tutorial")
            ]
        ]

        # ✅ Reply with Stylish Image & Message
        await message.reply_photo(
            random.choice(START_PIC),
            caption=response,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.HTML
        )

    except Exception as e:
        await message.reply_text(f"⚠️ Aɴ Eʀʀᴏʀ Oᴄᴄᴜʀʀᴇᴅ: {e}")


@Bot.on_callback_query(filters.regex(r"^(confirm_spin|spin_wheel|cancel_spin|confirm_mega_spin|mega_spin|free_points)$"))
async def handle_spin_operations(client: Bot, query: CallbackQuery):
    data = query.data
    
    if data == "confirm_spin":
        user_id = query.from_user.id
        user = await user_data.find_one({'_id': user_id})

        if not user:
            await query.answer("✖ You are not in the database. Please start the bot first.", show_alert=True)
            return

        referral_points = user.get('referral_points', 0)
        purchased_points = user.get('purchased_points', 0)
        total_points = referral_points + purchased_points

        if total_points >= SPIN_WHEEL_COST:
            await user_data.update_one({'_id': user_id}, {"$inc": {"purchased_points": -SPIN_WHEEL_COST}})
            reward = await spin_wheel(user_id)

            if reward is not None:
                if reward > 0:
                    reward_text = f"🎉 Congratulations! You won {reward} points! Your points have been updated."
                else:
                    reward_text = "✖ Oops! No reward this time. Try again!"
                
                await query.answer(reward_text, show_alert=True)

                user = await user_data.find_one({'_id': user_id})
                total_points = user.get('purchased_points', 0)
                message = await query.message.reply_text(f"Your current points: {total_points} points.")

                await asyncio.sleep(5)
                await message.delete()

                owner_message = f"""
📢 Spin Alert @ OɴʟʏF@ɴs Aʟʙᴜᴍ :
➤ User: [{query.from_user.first_name}](tg://user?id={user_id})
➤ Available Points: {total_points}
➤ Earned Points: {reward}
➤ Spin Result: {'Won' if reward > 0 else 'No Reward'}
                """
                await client.send_message(DUMB_CHAT, owner_message, parse_mode=ParseMode.MARKDOWN)

                print(f"Spin Details - User: {query.from_user.username}, UserID: {user_id}, Available Points: {total_points}, Earned Points: {reward}")
            else:
                await query.answer("✖ There was an issue with the spin. Please try again later.", show_alert=True)
        else:
            await query.answer(f"✖ You don't have enough points to spin. You need at least {SPIN_WHEEL_COST} points.", show_alert=True)

    elif data == "spin_wheel":
        user_id = query.from_user.id
        user = await user_data.find_one({'_id': user_id})

        if not user:
            await query.answer("✖ You are not in the database. Please start the bot first.", show_alert=True)
            return

        referral_points = user.get('referral_points', 0)
        purchased_points = user.get('purchased_points', 0)
        total_points = referral_points + purchased_points

        buttons = [
            [InlineKeyboardButton("✅ Yes", callback_data="confirm_spin"),
            InlineKeyboardButton("✖ No", callback_data="cancel_spin")],
            [InlineKeyboardButton("⚡Mᴇɢᴀ Sᴘɪɴ", callback_data="mega_spin")],
            [InlineKeyboardButton("🎉Bᴜʏ Pᴏɪɴᴛs", callback_data="buy_point"),
            InlineKeyboardButton("Rᴇᴅᴅᴇᴍ Pᴏɪɴᴛs", callback_data="redeem")]
        ]
        
        await client.send_dice(chat_id=query.message.chat.id, emoji="🎰")
        await query.message.reply_text(
            f"""<b><blockquote>Yᴏᴜ Wɪʟʟ Wᴏɴ Pᴏɪɴᴛs Dᴇᴘᴇɴᴅɪɴɢ Oɴ Yᴏᴜʀ Lᴜᴄᴋ Pᴏɪɴᴛs Cᴀɴ Wᴇ Usᴇᴅ Fᴏʀ Rᴇᴅᴅᴇᴍɪɴɢ Rᴇᴡᴀʀᴅs , Pᴜʀᴄʜᴀsɪɴɢ Pʀᴇᴍɪᴜᴍ Aɴᴅ Mᴀɴʏ Tʜɪɴɢ Cᴏᴍᴍɪɴɢ Sᴏᴏɴ</blockquote>

Eɴᴛʀʏ Pʀɪᴄᴇ : {SPIN_WHEEL_COST} Pᴏɪɴᴛs

🏆 Rᴇᴡᴀʀᴅs :
{SPIN_WHEEL_REWARD1} Pᴏɪɴᴛ
{SPIN_WHEEL_REWARD2} Pᴏɪɴᴛ
{SPIN_WHEEL_REWARD3} Pᴏɪɴᴛ
{SPIN_WHEEL_REWARD4} Pᴏɪɴᴛ
{SPIN_WHEEL_REWARD5} Pᴏɪɴᴛ

⚠️ Aʀᴇ Yᴏᴜ Sᴜʀᴇ Yᴏᴜ Wᴀɴᴛ Tᴏ Sᴘᴇɴᴅ {SPIN_WHEEL_COST} Pᴏɪɴᴛs Tᴏ Sᴘɪɴ Tʜᴇ Wʜᴇᴇʟ?\n\nYᴏᴜʀ Bᴀʟᴀɴᴄᴇ: {total_points} Pᴏɪɴᴛs

Pʀᴇss Tʜᴇ Yᴇs Bᴜᴛᴛᴏɴ Bᴇʟᴏᴡ Tᴏ Eᴀʀɴ A Rᴀɴᴅᴏᴍ Rᴇᴡᴀʀᴅ From Tʜᴇ Lɪsᴛ </b>""",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data == "cancel_spin":
        await query.answer("✖ Spin cancelled.", show_alert=True)
        await query.message.delete()

    elif data == "confirm_mega_spin":
        user_id = query.from_user.id
        user = await user_data.find_one({'_id': user_id})
        user_name = query.from_user.first_name if query.from_user.first_name else "Unknown"

        if not user:
            await query.answer("✖ You are not in the database. Please start the bot first.", show_alert=True)
            return

        referral_points = user.get('referral_points', 0)
        purchased_points = user.get('purchased_points', 0)
        total_points = referral_points + purchased_points
   
        if total_points >= MEGA_SPIN_COST:
            await user_data.update_one({'_id': user_id}, {"$inc": {"purchased_points": -MEGA_SPIN_COST}})
            reward = await mega_spin_wheel(user_id)

            if reward is not None:
                if reward > 0:
                    reward_text = f"🎉 Congratulations! You won {reward} points! Your points have been updated."
                else:
                    reward_text = "✖ Oops! No reward this time. Try again!"
               
                await query.answer(reward_text, show_alert=True)

                user = await user_data.find_one({'_id': user_id})
                total_points = user.get('purchased_points', 0)
                message = await query.message.reply_text(f"Your current points: {total_points} points.")

                await asyncio.sleep(5)
                await message.delete()

                owner_message = f"""
📢 Mega Spin Alert @ OɴʟʏF@ɴs Aʟʙᴜᴍ:
➤ Usᴇʀ : [{query.from_user.first_name}](tg://user?id={user_id})
➤ Available Points: {total_points}
➤ Earned Points: {reward}
➤ Spin Result: {'Won' if reward > 0 else 'No Reward'}
                """
                await client.send_message(DUMB_CHAT, owner_message, parse_mode=ParseMode.MARKDOWN)

                print(f"Mega Spin Details - User: {query.from_user.username}, UserID: {user_id}, Available Points: {total_points}, Earned Points: {reward}")
            else:
                await query.answer("✖ There was an issue with the mega spin. Please try again later.", show_alert=True)
        else:
            await query.answer(f"✖ You don't have enough points to spin. You need at least {MEGA_SPIN_COST} points.", show_alert=True)

    elif data == "mega_spin":
        user_id = query.from_user.id
        user = await user_data.find_one({'_id': user_id})
       
        if not user:
            await query.answer("✖ You are not in the database. Please start the bot first.", show_alert=True)
            return

        referral_points = user.get('referral_points', 0)
        purchased_points = user.get('purchased_points', 0)
        total_points = referral_points + purchased_points

        buttons = [
            [InlineKeyboardButton("✅ Yes", callback_data="confirm_mega_spin"),
            InlineKeyboardButton("✖ No", callback_data="cancel_spin")],
            [InlineKeyboardButton("🎉Bᴜʏ Pᴏɪɴᴛs", callback_data="buy_point"),
            InlineKeyboardButton("Rᴇᴅᴅᴇᴍ Pᴏɪɴᴛs", callback_data="redeem")]
        ]
        
        await client.send_message(chat_id=query.message.chat.id, text="👾")
        await query.message.reply_text(
            f"""<b><blockquote>Yᴏᴜ Wɪʟʟ Wᴏɴ Pᴏɪɴᴛs Dᴇᴘᴇɴᴅɪɴɢ Oɴ Yᴏᴜʀ Lᴜᴄᴋ Pᴏɪɴᴛs Cᴀɴ Wᴇ Usᴇᴅ Fᴏʀ Rᴇᴅᴅᴇᴍɪɴɢ Rᴇᴡᴀʀᴅs ,Pᴜʀᴄʜᴀsɪɴɢ Pʀᴇᴍɪᴜᴍ Aɴᴅ Mᴀɴʏ Tʜɪɴɢ Cᴏᴍᴍɪɴɢ Sᴏᴏɴ</blockquote>

Entry Price: {MEGA_SPIN_COST} Points

🏆 Mega Spin Rewards:
{MEGA_REWARDS[0]} Points
{MEGA_REWARDS[1]} Points
{MEGA_REWARDS[2]} Points
{MEGA_REWARDS[3]} Points
{MEGA_REWARDS[4]} Points

⚠️ Aʀᴇ Yᴏᴜ Sᴜʀᴇ Yᴏᴜ Wᴀɴᴛ Tᴏ Sᴘᴇɴᴅ {MEGA_SPIN_COST} Pᴏɪɴᴛs Tᴏ Mᴇɢᴀ Sᴘɪɴ ᴛʜᴇ Wʜᴇᴇʟ?
Pʀᴇss Tʜᴇ Yᴇs Bᴜᴛᴛᴏɴ Bᴇʟᴏᴡ Tᴏ Eᴀʀɴ A Rᴀɴᴅᴏᴍ Rᴇᴡᴀʀᴅ From Tʜᴇ Lɪsᴛ

Your Balance: {total_points} Pᴏɪɴᴛs.
</b>""",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    elif data == "free_points":
        user_id = query.from_user.id
        user = await user_data.find_one({'_id': user_id})

        if not user:
            await query.answer("✖ You are not in the database. Please start the bot first.", show_alert=True)
            return

        last_claim_date = user.get('last_free_points_date', None)
        today_date = datetime.now()

        if last_claim_date and last_claim_date.date() == today_date.date():
            await query.answer("✖ Aʟʀᴇᴀᴅʏ Cʟᴀɪᴍᴇᴅ. Cᴏᴍᴇ Bᴀᴄᴋ Tᴏᴍᴏʀʀᴏᴡ!", show_alert=True)
            return

        free_points = random.randint(MIN_POINTS, MAX_POINTS)

        await user_data.update_one({'_id': user_id}, {
            "$inc": {"purchased_points": free_points},
            "$set": {"last_free_points_date": today_date}
        })

        await query.answer(f"🎉 Rᴇᴄᴇɪᴠᴇᴅ {free_points} Pᴏɪɴᴛ Tᴏᴅᴀʏ !", show_alert=True)

        owner_id = DUMB_CHAT
        user_name = query.from_user.first_name or "Unknown User"
        user_mention = f"[{user_name}](tg://user?id={user_id})"
        message_text = f"🎁 Dᴀɪʟʏ Fʀᴇᴇ Pᴏɪɴᴛs Cʟᴀɪᴍᴇᴅ\n\n👤 Usᴇʀ : {user_mention}\n💰 Pᴏɪɴᴛs: {free_points}\n📅 Dᴀᴛᴇ: {today_date.strftime('%Y-%m-%d %H:%M:%S')}"
        await client.send_message(owner_id, message_text, parse_mode=ParseMode.MARKDOWN)

# async def main_menu(user_id, is_owner):
#     buttons = [
#         [InlineKeyboardButton("⚡ Aʙᴏᴜᴛ", callback_data="about"),
#         InlineKeyboardButton("⚙️ Fᴇᴀᴛᴜʀᴇs", callback_data="settings")],
#         [
#             InlineKeyboardButton("👄 Pɪᴄ", callback_data="pic"),
#             InlineKeyboardButton("🔥 Vɪᴅᴇᴏs", callback_data="video")
#         ]
#     ]
    
#     if is_owner:
#         buttons.append([
#             InlineKeyboardButton("💎 Mᴀɴᴀɢᴇ Pʀᴇᴍɪᴜᴍ", callback_data="premium"),
#             InlineKeyboardButton("👾 Tɪᴄᴋᴇᴛs", callback_data="allrequest")
#         ])

#     return InlineKeyboardMarkup(buttons)



@Bot.on_callback_query(filters.regex("^settings$"))
async def all_channels_callback(client, query):
    try:
        user_id = query.from_user.id  # Get the user ID
        # Channel information
        channels_text = """🌆 <b>Wᴇʟᴄᴏᴍᴇ, Cʏʙᴇʀ Wᴀʀʀɪᴏʀ...!</b> 🔥
🔹 Bᴜɪʟᴅ ʏᴏᴜʀ ʀᴇᴘᴜᴛᴀᴛɪᴏɴ & ᴜᴘɢʀᴀᴅᴇ! 🚀
"""

        # Create buttons for each channel
        buttons = [
            [InlineKeyboardButton("🚀Nᴇᴏɴ Rᴇғᴇʀ", callback_data=f"refer_{user_id}"),
            InlineKeyboardButton("🎟️ Rᴇᴅᴇᴇᴍ", callback_data="redeem")],
            [InlineKeyboardButton("💸 Bᴜʏ Tᴇᴄʜ Pᴏɪɴᴛ", callback_data="buy_point")],
            [InlineKeyboardButton("⌛ Dᴀɪʟʏ Qᴜᴇsᴛ", callback_data="free_points"),
            InlineKeyboardButton("🎡 Cʏʙᴇʀ Wʜᴇᴇʟ", callback_data="spin_wheel")],
            [InlineKeyboardButton("👩‍💻 Sᴜᴘᴘᴏʀᴛ", callback_data="support"),
            InlineKeyboardButton("🔎 Cʏʙᴇʀ Uᴘɢʀᴀᴅᴇ", callback_data="myplan")],
            [InlineKeyboardButton("♾️ Iɴғɪɴɪᴛᴇ Pᴏᴡᴇʀ", callback_data="generate_token")],
            [InlineKeyboardButton("✈️ Tʀᴀɴsғᴇʀ Pᴏɪɴᴛs", callback_data="transfer")],
            [InlineKeyboardButton("◀️ Rᴇᴛᴜʀɴ", callback_data="backtostart"),
            InlineKeyboardButton("💀 Dᴇᴀᴄᴛɪᴠᴀᴛᴇ", callback_data="close")]
            
        ]

        # Send the message with a nice image
        await query.message.edit_media(
            media=InputMediaPhoto(
            media=random.choice(START_PIC) ,# Replace with your actual image URL
            caption=channels_text,
            ),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        
    except Exception as e:
        print(f"Error in all_channels callback: {e}")
        await query.answer("An error occurred. Please try again later.", show_alert=True)

@Bot.on_callback_query(filters.regex("^backtostart$"))
async def back_to_start(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    is_owner = user_id == OWNER_ID  # Check if user is owner

    # Select a random start image
    start_pic = random.choice(START_PIC)

    raw_caption_text = "<blockquote>⚡ Hᴇʏ, {mention}</blockquote>\n\nI Aᴍ Aɴ <b>Uʟᴛɪᴍᴀᴛᴇ Hᴀᴄᴋᴇʀ</b> Bᴏᴛ."

    # Format message caption
    caption_text = raw_caption_text.format(
        mention=callback_query.from_user.mention
    )
    # Construct reply markup
    buttons = [[InlineKeyboardButton("👁️ Aɴᴏɴʏᴍᴏᴜs", callback_data="about"),
                InlineKeyboardButton("🛠️ Hᴀᴄᴋᴇʀ Tᴏᴏʟs", callback_data="settings")],
                [InlineKeyboardButton("🏛 Dᴀʀᴋ Lᴇɢᴇɴᴅs", callback_data="halloffame")]]

    reply_markup = InlineKeyboardMarkup(buttons)

    # Edit message with new media and text (FASTEST method)
    await callback_query.message.edit_media(
        media=InputMediaPhoto(start_pic, caption=caption_text),
        reply_markup=reply_markup
    )
    
    await callback_query.answer()

@Bot.on_message(filters.command("clear_requests") & filters.user(ADMINS))
async def clear_join_requests(client: Client, message: Message):
    result = await join_request_collection.delete_many({})
    await message.reply_text(f"🗑️ Deleted {result.deleted_count} join request(s) from the database.")

import random
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from bson import ObjectId

@Bot.on_callback_query(filters.regex(r"^(like|dislike)_[a-fA-F0-9]{24}$"))
async def handle_callback_query(client: Client, callback_query: CallbackQuery):
    data = callback_query.data
    user_id = str(callback_query.from_user.id)  # Store user_id as string for MongoDB
    action, file_id = data.split("_", 1)

    # Validate ObjectId
    if not ObjectId.is_valid(file_id):
        return await callback_query.answer("✖ Invalid file ID!", show_alert=True)

    # Fetch file data
    file_data = await link_data.find_one({"_id": ObjectId(file_id)})
    if not file_data:
        return await callback_query.answer("✖ File not found!", show_alert=True)

    user_interactions = file_data.get("user_interactions", {})
    previous_action = user_interactions.get(user_id)

    # Prevent redundant actions
    if previous_action == action:
        return await callback_query.answer("🔍 Rᴇsᴘᴏɴsᴇ Rᴇᴄᴏʀᴅᴇᴅ.", show_alert=True)

    # Prepare database update
    update_query = {"$set": {f"user_interactions.{user_id}": action}, "$inc": {}}

    if previous_action == "like":
        update_query["$inc"]["likes"] = -1
    elif previous_action == "dislike":
        update_query["$inc"]["dislikes"] = -1

    if action == "like":
        update_query["$inc"]["likes"] = update_query["$inc"].get("likes", 0) + 1
    elif action == "dislike":
        update_query["$inc"]["dislikes"] = update_query["$inc"].get("dislikes", 0) + 1

    # Apply update
    await link_data.update_one({"_id": ObjectId(file_id)}, update_query)

    # Fetch updated counts
    updated_file_data = await link_data.find_one({"_id": ObjectId(file_id)})
    likes = updated_file_data.get("likes", 0)
    dislikes = updated_file_data.get("dislikes", 0)

    # Inject random fake likes and dislikes if both are 0
    fake_updates = {}
    if likes == 0:
        likes = random.randint(10, 20)
        fake_updates["likes"] = likes
    if dislikes == 0:
        dislikes = random.randint(2, 5)
        fake_updates["dislikes"] = dislikes

    if fake_updates:
        fake_updates["fake_counts_injected"] = True
        await link_data.update_one(
            {"_id": ObjectId(file_id)},
            {"$set": fake_updates}
        )

    # Update message buttons
    reply_markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"❤️ {likes}", callback_data=f"like_{file_id}"),
            InlineKeyboardButton(f"💔 {dislikes}", callback_data=f"dislike_{file_id}")
        ]
    ])

    try:
        await callback_query.message.edit_reply_markup(reply_markup)
    except Exception as e:
        print(f"Error updating message: {e}")

    await callback_query.answer(f"🔍 Yᴏᴜ {action}ᴅ Tʜɪs Fɪʟᴇ..!", show_alert=False)

# ➤ Support Menu Buttons
def support_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Oᴘᴇɴ Sᴇᴄʀᴇᴛ Tɪᴄᴋᴇᴛ", callback_data="open_ticket")],
        [InlineKeyboardButton("💀 Dᴇᴀᴄᴛɪᴠᴀᴛᴇ", callback_data="backtostart")]
    ])

@Client.on_callback_query(filters.regex("^support$"))
async def support_panel(client, query: CallbackQuery):
    user_id = query.from_user.id
    user = await user_data.find_one({'_id': user_id})

    # Check if user exists and get their plan
    if not user:
        await query.answer("✖ Please start the bot first!", show_alert=True)
        return

    # Get user's current plan
    current_plan = await get_user_plan_group(user_id) or 'Free'  # Default to 'Free' if not found

    estimated_time = PLAN_SUPPORT_TIMES.get(current_plan, "⏳ 24-48 hours")  # Default to Free if not found

    await query.message.edit_text(
        f"👁‍🗨 **Sᴇᴄʀᴇᴛ Oᴘᴇʀᴀᴛɪᴏɴs Cᴏɴᴛʀᴏʟ** 👁‍🗨\n\n"
        f"🔐 Nᴏ Oɴᴇ Cᴀɴ Hᴇᴀʀ Yᴏᴜ Hᴇʀᴇ... Iꜰ Yᴏᴜ Hᴀᴠᴇ A Qᴜᴇʀʏ, Oᴘᴇɴ A Tɪᴄᴋᴇᴛ ᴀɴᴅ Aɴ Aᴅᴍɪɴ Wɪʟʟ Rᴇᴀᴄʜ Oᴜᴛ. "
        f"Rᴇsᴘᴏɴsᴇ Tɪᴍᴇ Dᴇᴘᴇɴᴅs Oɴ Yᴏᴜʀ Cʟᴇᴀʀᴀɴᴄᴇ Lᴇᴠᴇʟ. ⏳\n\n"
        f"📩 Cʟɪᴄᴋ **'Oᴘᴇɴ Sᴇᴄʀᴇᴛ Tɪᴄᴋᴇᴛ'** Tᴏ Eɴɢᴀɢᴇ Aɴ Oᴘᴇʀᴀᴛɪᴠᴇ.\n\n"
        f"📅 **Dᴇᴄᴏᴅᴇᴅ Rᴇᴘʟʏ Wɪɴᴅᴏᴡ:** {estimated_time}\n\n"
        f"💡 Cᴏɴᴛʀᴏʟ Tɪᴇʀ: {current_plan}",
        reply_markup=support_buttons()
    )
# Function to safely edit messages without causing MESSAGE_NOT_MODIFIED error
async def safe_edit_text(message, new_text, reply_markup=None):
    """Edit message only if the new text is different."""
    try:
        if message.text != new_text:
            await message.edit_text(new_text, reply_markup=reply_markup)
    except Exception as e:
        print(f"Error editing message: {e}")

# ➤ Open Ticket Request
# ➤ Open Ticket Request
@Client.on_callback_query(filters.regex("^open_ticket$"))
async def open_ticket(client: Client, query: CallbackQuery):
    user_id = query.from_user.id

    # Check if user already has an open ticket
    existing_ticket = await conversation_collection.find_one({'user_id': user_id, 'status': 'open'})
    
    if existing_ticket:
        await safe_edit_text(query.message, 
            "🚫 You already have a pending request. Please wait for a response before submitting another. 📌",
            reply_markup=support_buttons()
        )
        return

    # Ask the user for their message
    await safe_edit_text(query.message, "📝 Please type your message for the owner.")
    user_message = await client.ask(query.message.chat.id, "✉️ Send your message now:", timeout=60)

    # Generate a unique conversation ID
    conversation_id = f"conv_{user_id}_{int(time.time())}"

    # Fetch user's plan and calculate response time
    user = await user_data.find_one({'_id': user_id})
    current_plan = await get_user_plan_group(user_id) or 'Free'
    estimated_time = PLAN_SUPPORT_TIMES.get(current_plan, "⏳ 48-72 hours")  # Default to Free plan if not found

    # Store conversation in database
    conversation_details = {
        '_id': conversation_id,
        'user_id': user_id,
        'username': query.from_user.username,
        'first_name': query.from_user.first_name,
        'last_name': query.from_user.last_name,
        'messages': [{'sender': 'user', 'text': user_message.text, 'timestamp': time.time()}],
        'status': 'open',
        'last_updated': time.time(),
        'estimated_time': estimated_time  # Store the estimated response time for reference
    }
    await conversation_collection.insert_one(conversation_details)

    # Notify the owner with user's plan and estimated response time
    await client.send_message(
        chat_id=OWNER_ID,
        text=f"📩 **New Support Request** 📩\n\n"
             f"👤 **User:** [{query.from_user.first_name}](tg://user?id={user_id})\n"
             f"🆔 **ID:** `{user_id}`\n"
             f"💬 **Message:**\n{user_message.text}\n\n"
             f"📌 **Conversation ID:** `{conversation_id}`\n"
             f"📅 **Estimated Response Time for User ({current_plan}):** {estimated_time}"
        ,
        reply_markup=InlineKeyboardMarkup([ 
            [InlineKeyboardButton("✅ Close Ticket", callback_data=f"close_ticket_{conversation_id}")],
            [InlineKeyboardButton("💬 Reply", callback_data=f"reply_ticket_{conversation_id}")]
        ])
    )
    
    # Confirm to the user
    await safe_edit_text(query.message, 
        f"✅ Your message has been sent to the owner. You will be notified of a response.\n"
        f"📌 Keep this **Conversation ID:** `{conversation_id}`\n\n"
        f"📅 **Estimated Response Time:** {estimated_time}",
        reply_markup=support_buttons()
    )



# ➤ Close Ticket (Admin Only)
@Client.on_callback_query(filters.regex("^close_ticket_(.+)$"))
async def close_ticket_callback(client: Client, query: CallbackQuery):
    if query.from_user.id != OWNER_ID:
        await query.answer("⚠️ Only the owner can close tickets!", show_alert=True)
        return

    conversation_id = query.matches[0].group(1)
    await conversation_collection.update_one({'_id': conversation_id}, {'$set': {'status': 'closed'}})

    await query.message.edit_text(f"✅ Ticket `{conversation_id}` has been closed.", reply_markup=None)
    await client.send_message(
        chat_id=int(conversation_id.split('_')[1]),
        text="📢 Your support ticket has been **closed** by the admin. If you need further assistance, open a new ticket."
    )

# ➤ Admin Replies to a Ticket
@Client.on_callback_query(filters.regex("^reply_ticket_(.+)$"))
async def reply_ticket_callback(client: Client, query: CallbackQuery):
    if query.from_user.id != OWNER_ID:
        await query.answer("⚠️ Only the owner can reply to tickets!", show_alert=True)
        return

    conversation_id = query.matches[0].group(1)
    
    # Ask for admin's reply
    await query.message.edit_text("📝 Please type your response to the user.")
    admin_reply = await client.ask(query.message.chat.id, "✏️ Type your reply:", timeout=120)

    # Fetch ticket details
    ticket = await conversation_collection.find_one({'_id': conversation_id})
    if not ticket:
        await query.message.edit_text("✖ Ticket not found or already closed.")
        return

    user_id = ticket['user_id']
    user = await user_data.find_one({'_id': user_id})
    
    # Fetch user's plan
    user_plan = await get_user_plan_group(user_id) or 'Free'
    
    # Fetch estimated response time based on the user's plan
    user_estimated_time = PLAN_SUPPORT_TIMES.get(user_plan, "⏳ 48-72 hours")  # Default to 'Free' if not found

    # Store reply in database
    await conversation_collection.update_one(
        {'_id': conversation_id},
        {'$push': {'messages': {'sender': 'admin', 'text': admin_reply.text, 'timestamp': time.time()}}}
    )

    # Send admin's response to the user with their estimated response time
    await client.send_message(
        chat_id=user_id,
        text=f"📬 **Admin Reply to Your Ticket**\n\n"
             f"💬 **Message:**\n{admin_reply.text}\n\n"
             f"📌 Conversation ID: `{conversation_id}`\n"
             f"📅 **Estimated Response Time for Your Plan ({user_plan}):** {user_estimated_time}"
            
    )

    # Automatically close the ticket after replying
    await conversation_collection.update_one(
        {'_id': conversation_id},
        {'$set': {'status': 'closed'}}
    )

    # Notify admin about the closure and the response
    await query.message.edit_text(
        f"✅ Reply sent to the user.\n🚪 The ticket has been closed automatically.\n"
        f"📅 **User's Plan:** {user_plan}\n"
        f"⏳ **Estimated Response Time for User:** {user_estimated_time}"
    )

@Client.on_callback_query(filters.regex("watch_tutorial"))
async def send_tutorial(client: Client, callback_query):
    # If you have the video ID from Telegram, you can use it directly:
    tutorial_video = "BAACAgUAAxkBAAEFZ2ln69N1woHnlUdf4WwaSjRoS2jLBQACfRYAArrDgFZDxK3z2tRl0B4E"
    
    try:
        # Reply with the tutorial video
        await callback_query.message.reply_video(
            tutorial_video,  # File ID
            caption="📹 Here's a quick tutorial on how to refer and earn points!"
        )
        print(f"✅ Sent tutorial video to {callback_query.from_user.id}")
    except Exception as e:
        print(f"✖ Error sending tutorial video: {e}")

@Client.on_callback_query(filters.regex("daily_point"))
async def send_tutorial(client: Client, callback_query):
    # If you have the video ID from Telegram, you can use it directly:
    tutorial_video = "BAACAgUAAxkBAAEFZ2Vn69JtcpfBo0Jk1wVbDMgyN-YTTwACkB4AAsntuVZR4M4nnFrRfB4E"
    
    try:
        # Reply with the tutorial video
        await callback_query.message.reply_video(
            tutorial_video,  # File ID
            caption="📹 Here's a quick tutorial on how to earn daily points!"
        )
        print(f"✅ Sent tutorial video to {callback_query.from_user.id}")
    except Exception as e:
        print(f"✖ Error sending tutorial video: {e}")

@Bot.on_callback_query(filters.regex(r"^(approve|reject|delete)_(\d+)$"))
async def handle_auth_buttons(client: Bot, callback: CallbackQuery):
    action, user_id = callback.data.split("_")
    user_id = int(user_id)

    pending_req = await user_data.find_one({'user_id': user_id, 'status': 'pending'})

    if action == "approve":
        if pending_req:
            await add_admin(user_id)
            await user_data.update_one({'user_id': user_id}, {'$set': {'status': 'approved'}})

            approval_message = (
                "👑 <b>Yᴏᴜ Aʀᴇ Wᴏʀᴛʜʏ!</b> 👑\n\n"
                "🔥 <i>Tʜᴇ Gᴀᴛᴇs Oғ OɴʟʏF@ɴs Aʟʙᴜᴍ ᴀʀᴇ ɴᴏᴡ ᴏᴘᴇɴ ᴛᴏ ʏᴏᴜ!</i> 🔥\n\n"
                "🚀 <b>Wᴇʟᴄᴏᴍᴇ, Mɪɢʜᴛʏ Wᴀʀʀɪᴏʀ!</b> Yᴏᴜʀ ᴊᴏᴜʀɴᴇʏ ʙᴇɢɪɴs ɴᴏᴡ! 🏆"
            )

            await client.send_message(chat_id=user_id, text=approval_message, parse_mode=ParseMode.HTML)
            await callback.message.edit_text(f"✅ <b>Uꜱᴇʀ {user_id} ʜᴀs ʙᴇᴇɴ ᴅᴇᴄʟᴀʀᴇᴅ Wᴏʀᴛʜʏ! 🔥</b>", reply_markup=None)

        else:
            return await callback.answer("⚠️ Nᴏ ᴘᴇɴᴅɪɴɢ ʀᴇǫᴜᴇsᴛ ᴡᴀs ᴛᴏ ʙᴇ ᴀᴘᴘʀᴏᴠᴇᴅ.", show_alert=True)

    elif action == "reject":
        if pending_req:
            await user_data.delete_one({'_id': user_id, 'status': 'pending'})  # Fix applied here

            rejection_message = (
                "💔 <b>Yᴏᴜ Aʀᴇ Nᴏᴛ Wᴏʀᴛʜʏ...</b>\n\n"
                "😔 Tʜᴇ Cᴏᴜɴᴄɪʟ ʜᴀs sᴘᴏᴋᴇɴ. Yᴏᴜ ᴅᴏ ɴᴏᴛ ʜᴀᴠᴇ ᴡʜᴀᴛ ɪᴛ ᴛᴀᴋᴇs... ʏᴇᴛ.\n\n"
                "💪 Bᴜᴛ ᴅᴏ ɴᴏᴛ ʟᴏsᴇ ʜᴏᴘᴇ! Tʀʏ ᴀɢᴀɪɴ, ɢʀᴏᴡ sᴛʀᴏɴɢᴇʀ, ᴀɴᴅ ʏᴏᴜ ᴍᴀʏ ʀᴇᴛᴜʀɴ! 🔥"
            )

            await client.send_message(chat_id=user_id, text=rejection_message, parse_mode=ParseMode.HTML)
            await callback.message.edit_text(f"❌ <b>Uꜱᴇʀ {user_id} ʜᴀs ʙᴇᴇɴ ʀᴇᴊᴇᴄᴛᴇᴅ.</b> 🚫", reply_markup=None)
        else:
            return await callback.answer("⚠️ Nᴏ ᴘᴇɴᴅɪɴɢ ʀᴇǫᴜᴇsᴛ ꜰᴏᴜɴᴅ ᴛᴏ ʀᴇᴊᴇᴄᴛ.", show_alert=True)

    elif action == "delete":
        res = await user_data.delete_one({'user_id': user_id})
        if res.deleted_count:
            await callback.answer("🗑 Aᴅᴍɪɴ Rᴇᴍᴏᴠᴇᴅ!", show_alert=True)
            await callback.message.delete()
        else:
            return await callback.answer("⚠️ Uꜱᴇʀ ɴᴏᴛ ꜰᴏᴜɴᴅ ɪɴ ᴅᴀᴛᴀʙᴀꜱᴇ.", show_alert=True)

@Bot.on_callback_query(filters.regex(r"^transfer$"))
async def initiate_transfer(client: Client, callback_query: CallbackQuery):
    # Ask the sender for the receiver's ID and amount
    sender_id = callback_query.from_user.id
    user_data = database.users
    transfer_logs = database.point_transfers

    # Step 1: Ask for Receiver ID
    ask_id = await callback_query.message.reply(
        "🔁 <b>Sᴇɴᴅ Tʜᴇ Uꜱᴇʀ ID Tᴏ Tʀᴀɴꜱꜰᴇʀ Pᴏɪɴᴛꜱ:</b>\n\n"
        "📌 <i>Tip: Ask the user to use</i> /info <i>to get their ID.</i>",
        parse_mode=ParseMode.HTML
    )
    try:
        id_msg = await client.listen(sender_id, timeout=60)
    except:
        return await ask_id.edit("⏱️ Tɪᴍᴇᴏᴜᴛ. Tʀᴀɴꜱꜰᴇʀ Cᴀɴᴄᴇʟʟᴇᴅ.")

    try:
        receiver_id = int(id_msg.text.strip())
    except:
        return await ask_id.edit("🚫 Iɴᴠᴀʟɪᴅ ID. Cᴀɴᴄᴇʟʟɪɴɢ.")
    if receiver_id == sender_id:
        return await ask_id.edit("🚫 Yᴏᴜ Cᴀɴ'ᴛ Sᴇɴᴅ Pᴏɪɴᴛꜱ Tᴏ Yᴏᴜʀꜱᴇʟꜰ.")

    receiver = await user_data.find_one({'_id': receiver_id})
    if not receiver:
        return await ask_id.edit("❗ Tᴀʀɢᴇᴛ Uꜱᴇʀ Nᴏᴛ Fᴏᴜɴᴅ.")

    # Step 2: Ask for amount
    ask_amt = await ask_id.edit("💸 Hᴏᴡ Mᴀɴʏ Pᴏɪɴᴛꜱ?")
    try:
        amt_msg = await client.listen(sender_id, timeout=60)
    except:
        return await ask_amt.edit("⏱️ Tɪᴍᴇᴏᴜᴛ. Tʀᴀɴꜱꜰᴇʀ Cᴀɴᴄᴇʟʟᴇᴅ.")

    try:
        amount = int(amt_msg.text.strip())
        if amount <= 0:
            return await ask_amt.edit("🚫 Aᴍᴏᴜɴᴛ Mᴜꜱᴛ Bᴇ > 0.")
    except:
        return await ask_amt.edit("🚫 Iɴᴠᴀʟɪᴅ Aᴍᴏᴜɴᴛ.")

    # Step 3: Confirm transfer with inline buttons
    confirm_msg = f"⚠️ Cᴏɴꜰɪʀᴍ Tʀᴀɴꜱꜰᴇʀ?\n\n"
    confirm_msg += f"🎯 Tᴏ: <code>{receiver_id}</code>\n"
    confirm_msg += f"💳 Aᴍᴏᴜɴᴛ: <b>{amount}</b>\n\n"

    inline_buttons = [
        [InlineKeyboardButton("✅ Yᴇs", callback_data=f"confirm_transfer_{receiver_id}_{amount}_yes"),
        InlineKeyboardButton("❌ Nᴏ", callback_data="cancel_transfer")]
    ]
    
    await amt_msg.reply(
        confirm_msg,
        reply_markup=InlineKeyboardMarkup(inline_buttons)
    )


@Bot.on_callback_query(filters.regex(r"^confirm_transfer_"))
async def confirm_transfer(client: Client, callback_query: CallbackQuery):
    data = callback_query.data.split('_')
    receiver_id = int(data[2])
    amount = int(data[3])

    sender_id = callback_query.from_user.id
    user_data = database.users
    transfer_logs = database.point_transfers

    if data[4] == 'yes':
        # Step 4: Validate balance and proceed
        sender = await user_data.find_one({'_id': sender_id})
        total_sender_points = sender.get("referral_points", 0) + sender.get("purchased_points", 0)

        if total_sender_points < amount:
            return await callback_query.answer("🚫 Yᴏᴜ Dᴏɴ'ᴛ Hᴀᴠᴇ Eɴᴏᴜɢʜ Pᴏɪɴᴛꜱ.", show_alert=True)

        deduct_from_purchased = min(amount, sender.get("purchased_points", 0))
        deduct_from_referral = amount - deduct_from_purchased

        await user_data.update_one({'_id': sender_id}, {
            '$inc': {
                'purchased_points': -deduct_from_purchased,
                'referral_points': -deduct_from_referral
            }
        })

        await user_data.update_one({'_id': receiver_id}, {
            '$inc': {
                'purchased_points': amount  # ✅ Points now go to purchased_points
            }
        })

        await transfer_logs.insert_one({
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "amount": amount,
            "timestamp": datetime.utcnow()
        })

        await callback_query.message.edit(
            f"✅ <b>{amount} Pᴏɪɴᴛꜱ</b> Sᴇɴᴛ Tᴏ <code>{receiver_id}</code>!"
        )

        try:
            await client.send_message(
                receiver_id,
                f"🎁 Yᴏᴜ Gᴏᴛ <b>{amount} Pᴏɪɴᴛꜱ</b> Fʀᴏᴍ <code>{sender_id}</code>!"
            )
        except:
            pass
    else:
        await callback_query.message.edit("❌ Tʀᴀɴꜱꜰᴇʀ Cᴀɴᴄᴇʟʟᴇᴅ.")


@Bot.on_callback_query(filters.regex("cancel_transfer"))
async def cancel_transfer(client: Client, callback_query: CallbackQuery):
    await callback_query.message.edit("❌ Tʀᴀɴꜱꜰᴇʀ Cᴀɴᴄᴇʟʟᴇᴅ.")


@Bot.on_callback_query(filters.regex(r"^(not_authorized|allrequest.*|reply_ticket_.+)$"))
async def handle_auth_and_tickets(client: Bot, query: CallbackQuery):
    data = query.data
    
    if data == "not_authorized":
        await query.answer(
            "Yᴏᴜ Aʀᴇ Nᴏᴛ A Pʀᴇᴍɪᴜᴍ Usᴇʀ ❌ Yᴏᴜ Nᴇᴇᴅ Tᴏ Bᴜʏ Pʀᴇᴍɪᴜᴍ",
            show_alert=True
        )
        return

    elif data.startswith("allrequest"):
        if query.from_user.id != OWNER_ID:
            await query.answer("You are not authorized to view this.", show_alert=True)
            return
        
        tokens = data.split("_")
        page = int(tokens[1]) if len(tokens) > 1 and tokens[1].isdigit() else 0

        tickets = await conversation_collection.find({"status": "open"}).sort("last_updated", -1).to_list(length=None)
        total_tickets = len(tickets)

        if total_tickets == 0:
            text = "No pending requests found."
            buttons = [[
                InlineKeyboardButton("Close", callback_data="close"),
                InlineKeyboardButton("Bᴀᴄᴋ", callback_data="back_to_start")
            ]]
        else:
            start_index = page * 5
            end_index = start_index + 5
            displayed_tickets = tickets[start_index:end_index]
            text = f"<b>All Pending Requests (Page {page + 1}):</b>\n\n"

            for ticket in displayed_tickets:
                ticket_id = ticket.get("_id", "N/A")
                first_name = ticket.get("first_name", "N/A")
                last_name = ticket.get("last_name", "")
                username = ticket.get("username", "N/A")
                messages_list = ticket.get("messages", [])
                message_text = (
                    messages_list[0]["text"][:50] + "..."
                    if messages_list and "text" in messages_list[0]
                    else "N/A"
                )
                text += (
                    f"Ticket ID: <code>{ticket_id}</code>\n"
                    f"👤 User: {first_name} {last_name} (@{username})\n"
                    f"💬 Message: {message_text}\n\n"
                )

            buttons = []
            for ticket in displayed_tickets:
                ticket_id = ticket.get('_id', 'N/A')
                buttons.append([
                    InlineKeyboardButton(
                        f"Reply to {ticket_id}", 
                        callback_data=f"reply_ticket_{ticket_id}"
                    ),
                    InlineKeyboardButton(
                        "❌ Delete Ticket", 
                        callback_data=f"delete_ticket_{ticket_id}"
                    )
                ])

            nav_buttons = []
            if start_index > 0:
                nav_buttons.append(InlineKeyboardButton("Previous", callback_data=f"allrequest_{page - 1}"))
            if end_index < total_tickets:
                nav_buttons.append(InlineKeyboardButton("Next", callback_data=f"allrequest_{page + 1}"))
            if nav_buttons:
                buttons.append(nav_buttons)

            buttons.append([InlineKeyboardButton("Cʟᴏsᴇ", callback_data="close")])

        await query.message.reply_photo(
            photo=random.choice(START_PIC),
            caption=text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("reply_ticket_"):
        try:
            if query.from_user.id != OWNER_ID:
                await query.answer("You are not authorized to view this.", show_alert=True)
                return

            ticket_id = data[len("reply_ticket_"):]
            ticket = await conversation_collection.find_one({"_id": ticket_id, "status": "open"})
            
            if not ticket:
                await query.answer("Ticket not found.", show_alert=True)
                return

            prompt_msg = await client.send_message(
                chat_id=query.from_user.id,
                text=f"Enter Your reply for ticket {ticket_id}:"
            )

            reply_msg = await client.ask(
                chat_id=query.from_user.id,
                text="💬 Type your reply now:",
                timeout=60
            )

            await prompt_msg.delete()
            await reply_msg.delete()

            user_id = ticket.get("user_id", "N/A")
            if user_id:
                await client.send_message(
                    chat_id=user_id,
                    text=f"📩 Rᴇᴘʟʏ Fʀᴏᴍ Aᴅᴍɪɴ:\n\nTɪᴄᴋᴇᴛ Iᴅ: {ticket_id} \n\n{reply_msg.text}"
                )

            await conversation_collection.delete_one({"_id": ticket_id})
            success_msg = await query.message.edit_text(
                "Sᴜᴄᴄᴇss\nRᴇᴘʟʏ Sᴇɴᴛ Tᴏ Tɪᴄᴋᴇᴛ. Tɪᴄᴋᴇᴛ Cʟᴏsᴇᴅ...",
                reply_markup=InlineKeyboardMarkup([[ 
                    InlineKeyboardButton("Back", callback_data="allrequest"),
                    InlineKeyboardButton("Close", callback_data="close")
                ]])
            )
            await asyncio.sleep(3)
            await success_msg.delete()

        except Exception as e:
            logger.exception("Error replying to ticket:")
            await query.answer("An error occurred while replying to the ticket.", show_alert=True)

    elif data.startswith("delete_ticket_"):
        try:
            if query.from_user.id != OWNER_ID:
                await query.answer("You are not authorized to delete this ticket.", show_alert=True)
                return

            ticket_id = data[len("delete_ticket_"):]

            # Delete the ticket from the database
            ticket = await conversation_collection.find_one({"_id": ticket_id})
            if ticket:
                await conversation_collection.delete_one({"_id": ticket_id})
                await query.answer(f"Ticket {ticket_id} has been deleted.", show_alert=True)
                await query.message.edit_text(f"Ticket {ticket_id} has been deleted.", reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Back", callback_data="allrequest"), InlineKeyboardButton("Close", callback_data="close")]
                ]))
            else:
                await query.answer("Ticket not found to delete.", show_alert=True)

        except Exception as e:
            logger.exception("Error deleting ticket:")
            await query.answer("An error occurred while deleting the ticket.", show_alert=True)


from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
import asyncio
import time

REPLY_ERROR = """Usᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴀs ᴀ ʀᴇᴘʟʏ ᴛᴏ ᴀɴʏ ᴛᴇʟᴇɢʀᴀᴍ ᴍᴇssᴀɢᴇ ᴡɪᴛʜᴏᴜᴛ ᴀɴʏ sᴘᴀᴄᴇs."""

broadcast_sessions = {}

@Bot.on_message(filters.private & filters.command('broadcast') & filters.user(ADMINS))
async def start_broadcast(client: Bot, message: Message):
    if not message.reply_to_message:
        msg = await message.reply("⚠️ Please reply to a message to start broadcasting.")
        await asyncio.sleep(8)
        return await msg.delete()

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 All Users", callback_data="bc_all"),
         InlineKeyboardButton("🎯 Specific Users", callback_data="bc_specific")],
        [InlineKeyboardButton("💎 Users", callback_data="bc_premium"),
         InlineKeyboardButton("🎯 Users with > 100 Points", callback_data="bc_points")],
        [InlineKeyboardButton("🕒 Delete After Scheduled Time", callback_data="bc_delete_time")],
    ])

    broadcast_sessions[message.from_user.id] = {"msg": message.reply_to_message}
    await message.reply("🔘 Choose your broadcast target:", reply_markup=keyboard)


@Bot.on_callback_query(filters.regex("bc_(all|specific)"))
async def broadcast_type_handler(client: Bot, callback: CallbackQuery):
    await callback.message.delete()
    broadcast_type = callback.data.split("_")[1]
    user_id = callback.from_user.id

    data = broadcast_sessions.get(user_id, {})
    data["type"] = broadcast_type
    broadcast_sessions[user_id] = data

    # Ask if user wants to edit the message
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Yes", callback_data="bc_edit"),
         InlineKeyboardButton("❌ No", callback_data="bc_skipedit")]
    ])
    await callback.message.reply("✍️ Do you want to edit the broadcast message?", reply_markup=keyboard)


@Bot.on_callback_query(filters.regex("bc_edit|bc_skipedit"))
async def edit_message_handler(client: Bot, callback: CallbackQuery):
    user_id = callback.from_user.id
    editing = callback.data == "bc_edit"
    await callback.message.delete()

    if editing:
        await callback.message.reply("📝 Send the new broadcast message:")
        new_msg = await client.listen(callback.message.chat.id)
        broadcast_sessions[user_id]["msg"] = new_msg

    # Ask for inline button addition
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Button", callback_data="bc_addbtn"),
         InlineKeyboardButton("➡️ Skip", callback_data="bc_nobtn")]
    ])
    await callback.message.reply("Would you like to add inline buttons to your broadcast message?", reply_markup=keyboard)


@Bot.on_callback_query(filters.regex("bc_addbtn|bc_nobtn"))
async def add_button_handler(client: Bot, callback: CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.delete()
    
    # Retrieve broadcast session data
    data = broadcast_sessions.get(user_id)
    
    # Ensure 'data' exists and 'type' is set
    if not data or "type" not in data:
        await callback.message.reply("⚠️ No broadcast type selected. Please start the broadcast process again.")
        return

    # If type is 'specific', prompt for user IDs
    if data["type"] == "specific":
        await callback.message.reply("📥 Send user IDs (space or comma separated):")
        uid_msg = await client.listen(callback.message.chat.id)
        ids = [int(uid.strip()) for uid in uid_msg.text.replace(',', ' ').split() if uid.strip().isdigit()]
        data["users"] = ids
    else:
        # Handle other types
        pass

    # Continue processing button addition
    if callback.data == "bc_addbtn":
        await callback.message.reply("📥 Send buttons in this format:\n\n`Button Text - URL` (one per line)", parse_mode=ParseMode.MARKDOWN)
        button_msg = await client.listen(callback.message.chat.id)
        buttons = []

        for line in button_msg.text.strip().split("\n"):
            if "-" in line:
                text, url = map(str.strip, line.split("-", 1))
                buttons.append([InlineKeyboardButton(text, url=url)])

        data["reply_markup"] = InlineKeyboardMarkup(buttons)
    else:
        data["reply_markup"] = None

    # Preview the message
    preview_msg = await data["msg"].copy(
        chat_id=callback.message.chat.id,
        reply_markup=data.get("reply_markup")
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Send Broadcast", callback_data="bc_confirm")],
        [InlineKeyboardButton("❌ Cancel", callback_data="bc_cancel")]
    ])

    await client.send_message(
        chat_id=callback.message.chat.id,
        text="📋 Here's your broadcast preview. Do you want to proceed?",
        reply_markup=keyboard
    )


async def do_broadcast(client, chat_id, data):
    msg = data["msg"]
    user_ids = data["users"]
    markup = data.get("reply_markup")

    total = len(user_ids)
    successful = blocked = deleted = failed = 0
    progress_msg = await client.send_message(chat_id, "<i>🚀 Starting broadcast...</i>")

    for i, uid in enumerate(user_ids):
        try:
            sent_message = await msg.copy(chat_id=uid, reply_markup=markup)
            successful += 1
        except Exception as e:
            failed += 1

        # Update progress bar
        progress = (i + 1) / total
        bar = '█' * int(progress * 20) + '-' * (20 - int(progress * 20))
        await progress_msg.edit_text(
            f"<b>Broadcast Progress:</b>\n{bar} {progress:.1%}\n\n"
            f"✅ Sent: {successful}\n🚫 Blocked: {blocked}\n🗑 Deleted: {deleted}\n⚠️ Failed: {failed}"
        )

    # Check if the user selected a deletion time
    delete_after = data.get("delete_after")
    if delete_after:
        await asyncio.sleep(delete_after * 60)  # Wait for the specified delay time
        await sent_message.delete()  # Delete the broadcast message

    await progress_msg.edit_text(
        f"<b><u>✅ Broadcast Complete</u></b>\n\n"
        f"👥 Total Users: <code>{total}</code>\n"
        f"✅ Successful: <code>{successful}</code>\n"
        f"🚫 Blocked: <code>{blocked}</code>\n"
        f"🗑 Deleted: <code>{deleted}</code>\n"
        f"⚠️ Failed: <code>{failed}</code>"
    )

    broadcast_sessions.pop(chat_id, None)


@Bot.on_callback_query(filters.regex("bc_confirm|bc_cancel"))
async def confirm_broadcast_handler(client: Bot, callback: CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.delete()

    if callback.data == "bc_cancel":
        broadcast_sessions.pop(user_id, None)
        return await callback.message.reply("❌ Broadcast canceled.")

    data = broadcast_sessions.get(user_id)
    if not data:
        return await callback.message.reply("⚠️ No broadcast data found.")

    await do_broadcast(client, callback.message.chat.id, data)

@Bot.on_callback_query(filters.regex(r"bc_(all|specific|premium|points)"))
async def broadcast_type_handler(client: Bot, callback: CallbackQuery):
    await callback.message.delete()
    
    # Get the broadcast type from the callback data
    filter_type = callback.data.split("_")[1]
    user_id = callback.from_user.id

    # Ensure that session data exists for this user
    data = broadcast_sessions.get(user_id, {})
    if not data:
        broadcast_sessions[user_id] = {"msg": None, "type": None}

    # Set the broadcast type in the session data
    data["type"] = filter_type
    broadcast_sessions[user_id] = data

    # Handle the users list based on the selected type
    if filter_type == "points":
        users = await user_data.find({
            "$expr": {
                "$gt": [
                    {"$add": ["$referral_points", "$purchased_points"]},
                    100
                ]
            }
        }).to_list(length=None)
        data["users"] = [u["_id"] for u in users]

    elif filter_type == "premium":
        users = await user_data.find({"premium": True}).to_list(length=None)
        data["users"] = [u["_id"] for u in users]

    elif filter_type == "all":
        users = await user_data.find({}, {"_id": 1}).to_list(length=None)
        data["users"] = [u["_id"] for u in users]

    elif filter_type == "specific":
        await client.send_message(
            callback.message.chat.id,
            "👥 Send user IDs (space or comma separated):"
        )
        uid_msg = await client.listen(callback.message.chat.id)
        ids = [int(uid.strip()) for uid in uid_msg.text.replace(',', ' ').split() if uid.strip().isdigit()]
        data["users"] = ids

    # Ask if user wants to edit the message
    keyboard = InlineKeyboardMarkup([  
        [InlineKeyboardButton("✏️ Yes", callback_data="bc_edit"),
         InlineKeyboardButton("❌ No", callback_data="bc_skipedit")]
    ])
    
    await client.send_message(
        callback.message.chat.id,
        "<b>🛠️ Do you want to edit the broadcast message?</b>",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )


# This function will handle the callback for setting the deletion time.
@Bot.on_callback_query(filters.regex("bc_delete_time"))
async def delete_time_handler(client: Bot, callback: CallbackQuery):
    await callback.message.delete()

    # # Ensure that the broadcast type is set before continuing
    # data = broadcast_sessions.get(callback.from_user.id)
    # if not data or "type" not in data:
    #     await callback.message.reply("⚠️ No broadcast type selected. Please start the broadcast process again.")
    #     return

    # Ask user for the time after which the message should be deleted (in minutes)
    await callback.message.reply(
        "🕒 How many minutes after the broadcast should the message be deleted? (e.g., '5' for 5 minutes)"
    )

    # Capture the user's input for delay time
    time_msg = await client.listen(callback.message.chat.id)
    
    try:
        # Convert the input into an integer for time delay
        delay_minutes = int(time_msg.text.strip())
        if delay_minutes <= 0:
            await callback.message.reply("⚠️ Please provide a positive number for the delay.")
            return
        # Store the delete time in the session data
        broadcast_sessions[callback.from_user.id]["delete_after"] = delay_minutes
    except ValueError:
        await callback.message.reply("⚠️ Invalid input. Please enter a valid number for the delay.")
        return
    
    # Now ask the user if they want to send to all users or a specific user
    await callback.message.reply(
        "👥 Do you want to send the broadcast to all users or a specific user?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🌍 All Users", callback_data="bc_send_all"),
             InlineKeyboardButton("👤 Specific User", callback_data="bc_send_specific")]
        ])
    )

# This will handle the callback if the user chooses to send the broadcast to all users
@Bot.on_callback_query(filters.regex("bc_send_all"))
async def send_to_all_users(client: Bot, callback: CallbackQuery):
    await callback.message.delete()
    
    # You can send the broadcast message to all users here
    # Assuming you have a list of all users in your database
    users = await get_all_users()  # This should return a list of user IDs or user objects
    message_text = "Your broadcast message here"

    # Sending broadcast message to all users
    for user in users:
        try:
            await client.send_message(user.id, message_text)
        except Exception as e:
            print(f"Failed to send message to {user.id}: {e}")

    await callback.message.reply("✔️ Broadcast sent to all users.")

# This will handle the callback if the user chooses to send the broadcast to a specific user
@Bot.on_callback_query(filters.regex("bc_send_specific"))
async def send_to_specific_user(client: Bot, callback: CallbackQuery):
    await callback.message.delete()

    # Ask for the specific user's ID
    await callback.message.reply("📥 Please provide the user ID of the specific user you want to send the message to.")

    # Capture the user's input for the specific user ID
    user_id_msg = await client.listen(callback.message.chat.id)

    try:
        specific_user_id = int(user_id_msg.text.strip())
        # Send the broadcast message to the specific user
        message_text = "Your broadcast message here"
        await client.send_message(specific_user_id, message_text)
        
        await callback.message.reply(f"✔️ Broadcast sent to user {specific_user_id}.")
    except ValueError:
        await callback.message.reply("⚠️ Invalid user ID. Please enter a valid user ID.")

# Helper function to fetch all users (you need to implement this based on your database)
async def get_all_users():
    # Replace this with the actual code to fetch users from your database
    # For example, MongoDB or any other database you are using.
    users = []  # Fetch the list of users (user IDs or user objects)
    return users




DB_CHANNEL_ID = -1002637047900
MAIN_CHANNEL_ID = -1002571223411

import pytz
from datetime import datetime, timedelta
from pyrogram.types import CallbackQuery

scheduled_batches = {}  # msg.chat.id: (f_id, l_id)

@Client.on_message(filters.private & filters.user(ADMINS) & filters.command('send'))
async def batch(client: Client, message: Message):
    while True:
        first_msg = await client.ask(
            message.chat.id,
            "📥 Send the FIRST message from DB channel",
            filters=(filters.forwarded | filters.text),
            timeout=60
        )
        if first_msg.text == "/sbatch":
            return
        f_msg_id = await get_message_id_send(client, first_msg)
        if f_msg_id:
            break
        else:
            await first_msg.reply("❌ Not a valid DB channel message.")

    while True:
        last_msg = await client.ask(
            message.chat.id,
            "📥 Send the LAST message from DB channel",
            filters=(filters.forwarded | filters.text),
            timeout=60
        )
        if last_msg.text == "/sbatch":
            return
        l_msg_id = await get_message_id_send(client, last_msg)
        if l_msg_id:
            break
        else:
            await last_msg.reply("❌ Not a valid DB channel message.")

    # Ask for confirmation: Now or Later
    scheduled_batches[message.chat.id] = (f_msg_id, l_msg_id)

    await message.reply(
        "✅ Ready to send batch.\n\nDo you want to send **now** or **schedule** it?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 Send Now", callback_data="send_now")],
            [InlineKeyboardButton("🕒 Schedule for Later", callback_data="send_later")]
        ])
    )

@Client.on_callback_query(filters.regex("send_now|send_later"))
async def handle_batch_confirm(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    f_msg_id, l_msg_id = scheduled_batches.get(user_id, (None, None))

    if not f_msg_id or not l_msg_id:
        return await callback_query.answer("❌ No batch info found.", show_alert=True)

    if callback_query.data == "send_now":
        await callback_query.message.edit("🚀 Sending batch now...")
        await process_batch(client, user_id, f_msg_id, l_msg_id)
    else:
        await callback_query.message.edit("🕒 Please send the schedule time in format `DD-MM-YYYY HH:MM` (24hr, IST):")
        schedule_msg = await client.listen(user_id, timeout=120)
        try:
            ist = pytz.timezone("Asia/Kolkata")
            scheduled_time = datetime.strptime(schedule_msg.text, "%d-%m-%Y %H:%M")
            scheduled_time = ist.localize(scheduled_time)

            now_ist = datetime.now(ist)
            delay = (scheduled_time - now_ist).total_seconds()

            if delay < 1:
                return await schedule_msg.reply("❌ Time must be in the future.")

            await schedule_msg.reply(f"✅ Scheduled in {int(delay)} seconds at {scheduled_time.strftime('%d-%b %H:%M')} IST.")
            await asyncio.sleep(delay)
            await process_batch(client, user_id, f_msg_id, l_msg_id)

        except Exception as e:
            await schedule_msg.reply(f"❌ Invalid time format or error: {e}")
# from bs4 import BeautifulSoup


import html
import re
import asyncio
from pyrogram.enums import MessageEntityType
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait

async def process_batch(client, user_id, f_msg_id, l_msg_id):
    for msg_id in range(f_msg_id, l_msg_id + 1):
        try:
            msg = await client.get_messages(DB_CHANNEL_ID, msg_id)

            # Skip service messages or empty messages
            if msg.service or not (msg.text or msg.caption):
                continue

            text = msg.text or msg.caption
            entities = msg.entities or msg.caption_entities or []

            # Default fallback URL
            button_url = "https://t.me/NyxTeraBoxXRobot"

            # Try to find the hyperlink labeled "NʏxKɪɴɢX Sᴘᴇᴄɪᴀʟ Lɪɴᴋ 🤖"
            for entity in entities:
                if entity.type == "text_link":
                    visible_text = text[entity.offset:entity.offset + entity.length]
                    if visible_text.strip() == "NʏxKɪɴɢX Sᴘᴇᴄɪᴀʟ Lɪɴᴋ 🤖":
                        button_url = entity.url
                        break

            # If no special link found, fallback to the first t.me link in the text
            if button_url == "https://t.me/NyxTeraBoxXRobot":
                match = re.search(r"(https?://t\.me/[^\s]+)", text)
                if match:
                    button_url = match.group(1)

            # Debugging: Log the final URL being used
            print(f"Processing message {msg_id} with button URL: {button_url}")

            # Try sending the message to the public channel
            try:
                # Ensure the channel ID and URL are correct, and send the message
                await msg.copy(
                    MAIN_CHANNEL_ID,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("Tᴇʀᴀʙᴏx Dᴏᴡɴʟᴏᴀᴅᴇʀ ( Fʀᴇᴇ )", url=button_url)]
                    ])
                )
                print(f"✅ Message {msg_id} sent successfully to public channel.")
            except Exception as e:
                print(f"❌ Error while sending message {msg_id}: {e}")
                continue

            # Adding delay between each message
            await asyncio.sleep(1)

        except Exception as e:
            print(f"❌ Error on message {msg_id}: {e}")
            continue

    # Once done, notify the user
    await client.send_message(user_id, "✅ All messages sent to public channel.")


async def get_message_id_send(client, message):
    # Check if the message is forwarded
    if message.forward_from_chat:
        # Return the message ID of the forwarded message regardless of the source channel
        return message.forward_from_message_id

    # If the message is a direct reply with a sender name
    elif message.forward_sender_name:
        return 0

    # If the message is a URL, try to extract the message ID from the URL
    elif message.text:
        # Regex to extract the channel and message ID from the URL
        pattern = r"https://t.me/(?:c/)?(.*)/(\d+)"
        matches = re.match(pattern, message.text)

        if not matches:
            return 0

        # Extract channel ID and message ID from the matched URL
        channel_id = matches.group(1)
        msg_id = int(matches.group(2))

        # Return the message ID regardless of the channel
        return msg_id

    return 0  # If no valid message ID was found, return 0


@Bot.on_message(filters.command("post") & filters.private)
async def ask_for_post_message(client, message):
    await message.reply_text("📥 Please forward or send the message from your private channel.")

    try:
        user_message: Message = await client.listen(message.chat.id, timeout=60)
    except asyncio.TimeoutError:
        return await message.reply_text("⏰ Timeout. Please try again.")

    if user_message.forward_from_chat and user_message.forward_from_chat.id == DB_CHANNEL_ID:
        # Extract first t.me link from the message text
        text = user_message.text or user_message.caption or ""
        match = re.search(r"(https?://t\.me/[^\s]+)", text)

        button_url = match.group(1) if match else "https://t.me/NyxTeraBoxXRobot"

        while True:
            try:
                await user_message.copy(
                    MAIN_CHANNEL_ID,
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("🔗 Open File Link", url=button_url)]]
                    )
                )
                await message.reply_text("✅ Message posted to the public channel.")
                break
            except FloodWait as e:
                await message.reply_text(f"⚠️ Flood wait of {e.value} seconds. Waiting before retrying...")
                await asyncio.sleep(e.value)
    else:
        await message.reply_text("❌ That message wasn't from the private channel.")



