import asyncio
import os
import random
import sys
import time
import logging
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
from pyrogram.types import ChatJoinRequest  
from pyrogram.enums import ParseMode
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton,ReplyKeyboardMarkup, KeyboardButton
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, PeerIdInvalid

from bot import *
from config import  *
from helper_func import *
from database.database import *
from pymongo.operations import InsertOne  # Add this line to fix the NameError
from pyrogram import Client, filters
from pyrogram.types import Message, ReplyKeyboardMarkup, ReplyKeyboardRemove
from config import  *
from pyrogram.enums import ChatType 
from cachetools import TTLCache
 
IST = pytz.timezone("Asia/Kolkata")

cache = TTLCache(maxsize=1, ttl=6000)


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)




@Bot.on_message(filters.command(['start']) & (filters.private) & subscribed & subscribed2 & not_banned)
async def start_command(client: Client, message: Message):
    start_btn = [
        [InlineKeyboardButton("🤖 Aʙᴏᴜᴛ Mᴇ", callback_data="about"),
        InlineKeyboardButton("🛠️ Hᴀᴄᴋᴇʀ Tᴏᴏʟs", callback_data="settings")],
        [InlineKeyboardButton("🏛 Dᴀʀᴋ Lᴇɢᴇɴᴅs", callback_data="halloffame")]
    ]
    if message.from_user.id == OWNER_ID:
        start_btn.append([InlineKeyboardButton("💎 Mᴀɴᴀɢᴇ Pʀᴇᴍɪᴜᴍ", callback_data="premium"),
        InlineKeyboardButton("👾 Tɪᴄᴋᴇᴛs", callback_data="allrequest")])
    reply_markup = InlineKeyboardMarkup(start_btn)
    global user_data
    global premium_cache
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
    effect_id = int(random.choice(SUCCESS_EFFECT_IDS))# Random effect
    await message.delete()
    id = message.from_user.id
    user_id = message.from_user.id
    base64_string = None

    # ✅ Check if the user is already in the database
    is_new_user = not await present_user(id)

    if is_new_user:
        try:
            await add_user(id)  # ✅ Add new user to the database
        except Exception as e:
            print(f"Error adding user: {e}")
            return
    else:
        logger.debug(f"User {id} is already in the database, skipping referral check.")

    waiting_timer_status = await get_waiting_timer()

    referrer_id = None  # Ensure referrer_id is always defined

    # ✅ Extract the start parameter (claim or referral)
    try:
        base64_string = message.text.split(" ", 1)[1]  # Extract the parameter
    except IndexError:
        base64_string = None  # No extra parameter provided

    # 🔹 **Handle 'claim_' links (Points Claiming)**
    if base64_string and base64_string.startswith("claim_"):
        claim_id = base64_string.split("_", 1)[1]  # Extract claim ID

        try:
            # Convert claim_id to ObjectId for MongoDB query
            claim_data = await envelop_data.find_one({"_id": ObjectId(claim_id)})
        except Exception as e:
            print(f"Error retrieving claim data: {e}")
            await message.reply_text("<b>❌ Lɪɴᴋ Is Iɴᴠᴀʟɪᴅ Pʟᴇᴀsᴇ Cʜᴇᴄᴋ...</b>")
            return

        if not claim_data:
            await message.reply_text("<b>❌ Lɪɴᴋ Is Iɴᴠᴀʟɪᴅ Pʟᴇᴀsᴇ Cʜᴇᴄᴋ</b>")
            return

        if claim_data.get("claimed_users") and str(id) in claim_data["claimed_users"]:
            await message.reply_sticker("CAACAgUAAxkBAAEBMQ5n7Od3c5ifljnKWE_hXkkqzXbHYwAC5gcAAjL26VVmPJzCM-BjdzYE")  
            await message.reply_text(
                "<b>👀 Dᴇᴛᴇᴄᴛᴇᴅ: Aʟʀᴇᴀᴅʏ Cʟᴀɪᴍᴇᴅ! 🚫</b>\n\n"
                "⚡ Nᴏ Rᴇʜᴀsʜɪɴɢ – Gᴇᴛ Bᴀᴄᴋ ᴛᴏ ᴛʜᴇ Gʀɪɴᴅ! 🔥\n",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💸 Eᴀʀɴ Mᴏʀᴇ", callback_data=f"refer_{user_id}")]
                ])
            )
            return

        # Check if the envelope has expired
        expiry_time = claim_data.get("expiry_time", None)
        if expiry_time and datetime.utcnow() > expiry_time:
            await message.reply_text("⏳ Oᴏᴘs... Tɪᴍᴇ Wᴀsɴ'ᴛ Oɴ Yᴏᴜʀ Sɪᴅᴇ! ⚠️\n\n"
            "🔗 Lɪɴᴋ Eᴠᴀᴘᴏʀᴀᴛᴇᴅ Iɴᴛᴏ Tʜᴇ Dɪɢɪᴛᴀʟ Vᴏɪᴅ... 💀",
            )
            return

        # Check if there are remaining points
        if claim_data["remaining_points"] <= 0:
            await message.reply_text("🔗 Lɪɴᴋ Eᴠᴀᴘᴏʀᴀᴛᴇᴅ Iɴᴛᴏ Tʜᴇ Dɪɢɪᴛᴀʟ Vᴏɪᴅ... 💀")
            return

        # ✅ If everything is fine, give the points to the user
        points_to_receive = claim_data["fixed_claim"]
        if points_to_receive > claim_data["remaining_points"]:
            points_to_receive = claim_data["remaining_points"]

        # Update the user's points balance
        await user_data.update_one(
            {"_id": id},
            {"$inc": {"purchased_points": points_to_receive}}
        )

        # Mark the claim as used
        await envelop_data.update_one(
            {"_id": ObjectId(claim_id)},
            {"$inc": {"remaining_points": -points_to_receive}, "$set": {f"claimed_users.{id}": points_to_receive}}
        )

        try:
            notification_text = (
                f"📢 Usᴇʀ Cʟᴀɪᴍᴇᴅ Fʀᴏᴍ Aɴ Eɴᴠᴇʟᴏᴘᴇ\n"
                f"👤 Usᴇʀ : [{message.from_user.first_name}](tg://user?id={id}) (`{id}`)\n"
                f"📩 Eɴᴠᴇʟᴏᴘ : {claim_data['name']}\n"
                f"🎁 Cʟᴀɪᴍᴇᴅ Aᴍᴏᴜɴᴛ : {points_to_receive} points\n"
                f"💰 Rᴇᴍᴀɪɴɪɴɢ Pᴏɪɴᴛs : {claim_data['remaining_points'] - points_to_receive}\n"
                f"⏳ Exᴘɪʀʏ Tɪᴍᴇ : {claim_data['expiry_time'].strftime('%Y-%m-%d %H:%M:%S UTC')}"
            )
            await client.send_message(DUMB_CHAT, notification_text, parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            print(f"❌ Failed to notify owner about claim: {e}")

        await message.reply_text(f"<b>👁‍🗨 Tʜᴇ Oʀᴅᴇʀ Hᴀs Rᴇᴄᴏɢɴɪᴢᴇᴅ Yᴏᴜ. {points_to_receive} Cʏʙᴇʀ Cʀᴇᴅɪᴛs Hᴀᴠᴇ Bᴇᴇɴ Tʀᴀɴsғᴇʀʀᴇᴅ. 🔺")
        return  # Stop further processing

    # 🔹 **Handle 'refer=' links (Referrals)**
    if base64_string and 'refer=' in base64_string:
        try:
            # Extract referrer ID
            referrer_id = int(base64_string.split("refer=")[1])

            # Prevent self-referral
            if referrer_id == id:
                await message.reply_text("❌ You can't refer yourself!")
                return

            # ✅ Only allow referral if the user is **new**
            if is_new_user:
                # Check if the user has already been referred
                existing_user = await user_data.find_one({'_id': id})
                if existing_user and 'referrer' in existing_user:
                    await message.reply_text("❌ You have already been referred!")
                    return

                await store_referrer(referrer_id, id,client, OWNER_ID)
                await increment_referral_count(client, referrer_id, id)

                await message.reply_text("🎉 You were referred successfully!")

                # Notify the referrer
                await client.send_message(referrer_id, f"🎉 You have successfully referred {message.from_user.first_name}!")

            else:
                await message.reply_text("❌ You are already registered. Referrals only work for new users.")

        except ValueError:
            await message.reply_text("❌ Invalid referral ID.")
        except IndexError:
            await message.reply_text("❌ Referral link is incorrect.")
        return

    # ✅ Fix: Ensure referrer_id exists before checking
    if referrer_id:
        print(f"User {id} was referred by {referrer_id}")

    if base64_string and base64_string.startswith("daily_"):
        token = base64_string[6:]  # Extract the token part
        token_data = await token_collection.find_one({"token": token, "claimed": False})
        if token_data:
            await token_collection.update_one({"token": token}, {"$set": {"claimed": True}})
            await user_data.update_one({"_id": user_id}, {"$inc": {"purchased_points": 10}})
            await message.reply_text(
                "🏆 <b>Qᴜᴇꜱᴛ Cᴏᴍᴘʟᴇᴛᴇ!</b>\n\n"
                "🎮 Yᴏᴜ ᴄʟᴀɪᴍᴇᴅ ʏᴏᴜʀ <b>Dᴀɪʟʏ Rᴇᴡᴀʀᴅ</b>!\n"
                "💰 <b>+10</b> Lᴏᴏᴛ Pᴏɪɴᴛꜱ ᴀᴅᴅᴇᴅ ᴛᴏ ʏᴏᴜʀ ɪɴᴠᴇɴᴛᴏʀʏ.\n\n"
            )
            user_info = f"🎮 Pʟᴀʏᴇʀ: {message.from_user.first_name} (@{message.from_user.username})\n🆔 ID: {user_id}"
            alert_text = f"🏆 <b>Qᴜᴇsᴛ Cᴏᴍᴘʟᴇᴛᴇ!</b> 🏆\n\n{user_info}\n🏆 XP Gᴀɪɴᴇᴅ : <b>+10 Lᴏᴏᴛ Pᴏɪɴᴛꜱ 🎯</b>"

            await client.send_message(DUMB_CHAT, alert_text, parse_mode=ParseMode.HTML)
        else:
            await message.reply_text("⚠️ Invalid or already claimed daily reward link.")
        return  

    if base64_string and base64_string.startswith("file_"):
        encoded_key = base64_string.split("_", 1)[1]  # ✅ Extract the encoded key
        try:
            decoded_key = await decode_points(encoded_key)
            if not decoded_key:
                raise ValueError("Decoded key is None or empty")    

            msg_id, db_channel_id, required_points = map(int, decoded_key)
            access_key = encoded_key

            await inc_count(access_key)
            
        except Exception as e:
            print(f"Error decoding file link: {e}")
            await message.reply_text("<b>❌ Invalid File Link. Please Check.</b>")
            return

            # ✅ Fetch file message from the DB Channel (not from file_collection)
        try:
            channel_message = await client.get_messages(db_channel_id, msg_id)
            if not channel_message:
                raise ValueError("Message not found in DB Channel")
        except Exception as e:
            logger.error(f"❌ File Not Found for msg_id: {msg_id}")
            await message.reply_text("<b>❌ File Not Found in DB Channel.</b>")
            return

        user_info = await user_data.find_one({"_id": message.from_user.id})
        
        if not user_info:
            logger.error(f" User Not Found: {user_id}")
            await message.reply_text("<b>❌ User data not found.</b>")
            return  

        referral_points = user_info.get("referral_points", 0)
        purchased_points = user_info.get("purchased_points", 0)
        total_points = referral_points + purchased_points
        file_data = await link_data.find_one({"access_key": access_key})
        file_ids = file_data.get("file_ids", []) if file_data else []
        file_name = file_data.get('file_name') if file_data else (channel_message.document.file_name if channel_message.document else 'No File')
        purchased_files = user_info.get("purchased_files", [])
        # is_premium = user_info.get("premium", False)
        days_left = await get_premium_days_left(id)
        referral_link = f"https://t.me/{client.me.username}?start=refer={user_id}"

        if await can_bypass_points(user_info):  # ✅ Use user_info instead of user
            premium_msg = await message.reply_text("<b>🎉 Pʀᴇᴍɪᴜᴍ Uꜱᴇʀ Dᴇᴛᴇᴄᴛᴇᴅ! Yᴏᴜ Cᴀɴ Aᴄᴄᴇꜱꜱ Tʜɪꜱ Fɪʟᴇ Fᴏʀ Fʀᴇᴇ.</b>")
            retrieved_msg = await channel_message.copy(chat_id=message.from_user.id, disable_notification=True)
            sent_messages = [retrieved_msg]
            await asyncio.sleep(PAID_TIME)
            try:
                await client.delete_messages(chat_id=message.from_user.id, message_ids=premium_msg.id)
            except Exception as e:
                logger.error(f"❌ Error deleting premium message: {e}")
            for sent_msg in sent_messages:
                try:
                    if sent_msg:
                        await client.delete_messages(chat_id=message.from_user.id, message_ids=sent_msg.id)
                except Exception as e:
                    logger.error(f"❌ Error deleting message {sent_msg.id}: {e}")
            return

        if msg_id in purchased_files:
            unlocked_msg = await message.reply_text("<b>⚡ Yᴏᴜ Hᴀᴠᴇ Aʟʀᴇᴀᴅʏ Uɴʟᴏᴄᴋᴇᴅ Tʜɪs Fɪʟᴇ Nᴏ Nᴇᴇᴅ Tᴏ Pᴀʏ Aɢᴀɪɴ...</b>")
            retrieved_msg = await channel_message.copy(chat_id=message.from_user.id, disable_notification=True)
            reply_msg  = await message.reply_text(
                f"<b>🎉 Fɪʟᴇ Rᴇᴛʀɪᴇᴠᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ !</b>\n\n"
                f"<b>Nᴏ Pᴏɪɴᴛs Dᴇᴅᴜᴄᴛᴇᴅ</b>\n\n"
                f"<blockquote><b>Tʜɪs Fɪʟᴇ Wɪʟʟ Bᴇ Dᴇʟᴇᴛᴇᴅ Iɴ {PAID_TIME} Sᴇᴄᴏɴᴅs Pʟᴇᴀsᴇ Sᴀᴠᴇ / Fᴏʀᴡᴀʀᴅ Tʜɪs Fɪʟᴇ Tᴏ Yᴏᴜʀ Sᴀᴠᴇᴅ Mᴇssᴀɢᴇs..</b></blockquote>"
            )
            await asyncio.sleep(PAID_TIME)
            await unlocked_msg.delete()
            await retrieved_msg.delete()
            await reply_msg.edit_text(
                f"<b>🗑️ Fɪʟᴇ Dᴇʟᴇᴛᴇᴅ!</b>\n"
                f"💸 Dᴇᴅᴜᴄᴛᴇᴅ: <b>0 Pᴏɪɴᴛs</b>\n"
                f"💼 Bᴀʟᴀɴᴄᴇ: <b>{total_points} Pᴏɪɴᴛs</b>\n\n"
                f"⚠️ <i>Fɪʟᴇ ʀᴇᴍᴏᴠᴇᴅ ғʀᴏᴍ sʏsᴛᴇᴍ. Mᴀᴋᴇ sᴜʀᴇ ɪᴛ's sᴀᴠᴇᴅ.</i>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("♻️ Uɴʟᴏᴄᴋ Aɢᴀɪɴ", url=f"https://t.me/{client.username}?start={message.command[1]}")]
                    ])
                )
            return
        if total_points < required_points:
            buttons = [
                [
                    InlineKeyboardButton("Tʀʏ Aɢᴀɪɴ ♻️", url=f"https://t.me/{client.username}?start={message.command[1]}"),
                ],
                [InlineKeyboardButton("⚡Bᴜʏ Pᴏɪɴᴛs", callback_data="buy_point"),
                InlineKeyboardButton("🐦‍🔥 Iɴᴠɪᴛᴇ Sǫᴜᴀᴅ",url=f"https://t.me/share/url?url={referral_link}")],
                [InlineKeyboardButton("🎰 Fʀᴇᴇ Pᴏɪɴᴛs", callback_data="free_points"),
                InlineKeyboardButton("🕸️ Sᴘɪɴ Wʜᴇᴇʟ", callback_data="spin_wheel")],
                [InlineKeyboardButton("👻 Fʀᴇᴇ Pᴏɪɴᴛs Lɪғᴀғᴀ Eᴠᴇʀʏᴅᴀʏ", url="https://t.me/+Ta5P3a3k9mk2N2E1"),
                InlineKeyboardButton("♾️ Iɴғɪɴɪᴛᴇ Pᴏᴡᴇʀ", callback_data="generate_token")]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await message.reply_text(
                f"<b>🚫 Aᴄᴄᴇss Dᴇɴɪᴇᴅ!</b>\n\n"
                f"<b>💾 Tʜɪs Fɪʟᴇ Rᴇǫᴜɪʀᴇs:</b> <u>{required_points} Pᴏɪɴᴛs</u>\n"
                f"<b>💰 Yᴏᴜʀ Bᴀʟᴀɴᴄᴇ:</b> <u>{total_points} Pᴏɪɴᴛs</u>\n\n"
                f"<i>🧿 Tᴏ Uɴʟᴏᴄᴋ Tʜɪs Fɪʟᴇ, Yᴏᴜ Nᴇᴇᴅ Mᴏʀᴇ Pᴏɪɴᴛs.</i>\n"
                f"<i>🎯 Dᴏɴ’ᴛ Wᴏʀʀʏ, Yᴏᴜ Cᴀɴ Bᴜʏ Pᴏɪɴᴛs ᴏʀ Eᴀʀɴ Tʜᴇᴍ Tʜʀᴏᴜɢʜ Rᴇғᴇʀʀᴀʟs.</i>\n\n"
                f"<blockquote>🌀 <b>Fɪʟᴇs Yᴏᴜ Uɴʟᴏᴄᴋ Cᴀɴ Bᴇ Fᴏʀᴡᴀʀᴅᴇᴅ Iɴsᴛᴀɴᴛʟʏ.</b>\n"
                f"🛠 <b>Fᴀᴄɪɴɢ Issᴜᴇs?</b> Cᴏɴᴛᴀᴄᴛ: @{OWNER_TAG}</blockquote>",
                reply_markup=reply_markup
            )
            return
            

        # ✅ Deduct points properly
        if referral_points >= required_points:
            await user_data.update_one({"_id": message.from_user.id}, {"$inc": {"referral_points": -required_points}})
        else:
            remaining = required_points - referral_points
            await user_data.update_one(
                {"_id": message.from_user.id},
                {"$set": {"referral_points": 0}, "$inc": {"purchased_points": -remaining}}
            )

        await user_data.update_one({"_id": message.from_user.id}, {"$push": {"purchased_files": msg_id}})
        snt_msg = await channel_message.copy(chat_id=message.from_user.id, disable_notification=True)
        remaining_points = user_info.get("referral_points", 0) + user_info.get("purchased_points", 0) - required_points
        reply_msg  = await message.reply_text(f"<b>🎉 Fɪʟᴇ Uɴʟᴏᴄᴋᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ !</b>\n\n<b>Pᴏɪɴᴛs Dᴇᴅᴜᴄᴛᴇᴅ :</b> {required_points} Pᴏɪɴᴛs\n<b>Rᴇᴍᴀɪɴɪɴɢ Bᴀʟᴀɴᴄᴇ :</b> {remaining_points} Pᴏɪɴᴛs\n\n<b><blockquote>Tʜɪs Fɪʟᴇ Wɪʟʟ Bᴇ Dᴇʟᴇᴛᴇᴅ Iɴ {PAID_TIME} Sᴇᴄᴏɴᴅs Pʟᴇᴀsᴇ Sᴀᴠᴇ / Fᴏʀᴡᴀʀᴅ Tʜɪs Fɪʟᴇ Tᴏ Yᴏᴜʀ Sᴀᴠᴇᴅ Mᴇssᴀɢᴇs</b></blockquote>"
        )
        await inc_count(access_key)
        owner_alert = (f"Pᴀɪᴅ Fɪʟᴇs Aᴄᴄᴇssᴇᴅ Bʏ Usᴇʀ : [{message.from_user.first_name}](tg://user?id={message.from_user.id}) "
                   f"({message.from_user.id})\n"
                   f"👻 Rᴇᴍᴀɪɴɪɴɢ Bᴀʟᴀɴᴄᴇ : {remaining_points}\n"
                   f"👾 File: {file_name}\n"
                   f"🔗 Lɪɴᴋ: [Access Link](https://t.me/{client.username}?start={message.command[1]})")
        await client.send_message(DUMB_CHAT, owner_alert, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        await asyncio.sleep(PAID_TIME)
        try:
            await snt_msg.delete()
            await reply_msg.edit_text(
                f"<b>🗑️ Fɪʟᴇ Dᴇʟᴇᴛᴇᴅ</b>\n"
                f"<i>— {required_points} ᴘᴏɪɴᴛs ᴜsᴇᴅ</i>\n"
                f"<i>— {remaining_points} ʀᴇᴍᴀɪɴɪɴɢ</i>\n\n"
                f"<b>⚠️ Aᴄᴄᴇss Exᴘɪʀᴇᴅ.</b>\n"
                f"<i>Mᴀᴋᴇ sᴜʀᴇ ʏᴏᴜ sᴀᴠᴇᴅ ɪᴛ ɴᴇxᴛ ᴛɪᴍᴇ.</i>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("♻️ Rᴇᴜɴʟᴏᴄᴋ", url=f"https://t.me/{client.username}?start={message.command[1]}")]
                    ])
                )
        except Exception as e:
            print(f"Error deleting file: {e}")
        return

    if base64_string and base64_string.startswith("batch_"):
        encoded_key = base64_string.split("_", 1)[1]
        try:
            decoded_key = await decode_batch_points(encoded_key)
            if not decoded_key:
                raise ValueError("Decoded key is None or empty")

            start_id, end_id, db_channel_id, required_points = decoded_key
            required_points = int(required_points)
            file_ids = list(range(int(start_id), int(end_id) + 1))  # Generate file IDs from start_id to end_id

            await inc_count(encoded_key)

            user_info = await user_data.find_one({"_id": message.from_user.id})
            referral_points = user_info.get("referral_points", 0)
            purchased_points = user_info.get("purchased_points", 0)
            total_points = referral_points + purchased_points
            purchased_files = user_info.get("purchased_files", [])
            # is_premium = user_info.get("premium", False)
            days_left = await get_premium_days_left(id)
            referral_link = f"https://t.me/share/url?url=https://t.me/{client.username}?start=ref_{message.from_user.id}"

            batch_info = await database.batch_data.find_one({"access_key": encoded_key})
            if not batch_info:
                raise ValueError("Batch info not found in the database")
            file_name = batch_info.get("file_name", "Unknown File")
            

            if await can_bypass_points(user_info):
                plan = await get_user_plan_group(message.from_user.id)
                premium_msg = await message.reply_text(
                    f"<b>👑 {plan} Mᴇᴍʙᴇʀ Dᴇᴛᴇᴄᴛᴇᴅ</b>\n"
                    f"<i>🎉 Fɪʟᴇ Uɴʟᴏᴄᴋᴇᴅ Fᴏʀ Fʀᴇᴇ – Nᴏ Pᴏɪɴᴛs Dᴇᴅᴜᴄᴛᴇᴅ.</i>"
                )
                sent_messages = []
                for msg_id in file_ids:
                    try:
                        msg_id = re.sub(r'\D', '', str(msg_id))  # Convert msg_id to string
                        if msg_id:
                            msg_id = int(msg_id)  # Convert to integer
                            channel_message = await client.get_messages(CHANNEL_ID, msg_id)
                            if not channel_message or (not channel_message.text and not channel_message.photo and not channel_message.video and not channel_message.document):
                                # logger.warning(f"⚠️ Message {msg_id} not found in the channel.")
                                continue  
                            sent_message = await channel_message.copy(
                                chat_id=message.from_user.id,
                                disable_notification=True
                            )
                            sent_messages.append(sent_message)
                    except Exception as e:
                        logger.error(f"❌ Error retrieving file for msg_id {msg_id}: {e}")

                await asyncio.sleep(PAID_TIME)
                try:
                    await client.delete_messages(chat_id=message.from_user.id, message_ids=premium_msg.id)
                except Exception as e:
                    logger.error(f"❌ Error deleting premium message: {e}")
                for sent_msg in sent_messages:
                    try:
                        if sent_msg:
                            await client.delete_messages(chat_id=message.from_user.id, message_ids=sent_msg.id)
                    except Exception as e:
                        logger.error(f"❌ Error deleting message {sent_msg.id}: {e}")
                return

            # Check if all files are already purchased
            already_purchased = all(file_id in purchased_files for file_id in file_ids)
            if already_purchased:
                unlocked_msg = await message.reply_text("<b>⚡ Yᴏᴜ Hᴀᴠᴇ Aʟʀᴇᴀᴅʏ Uɴʟᴏᴄᴋᴇᴅ Tʜɪs Fɪʟᴇ Nᴏ Nᴇᴇᴅ Tᴏ Pᴀʏ Aɢᴀɪɴ...</b>")
                sent_messages = []
                for file_id in file_ids:
                    logger.debug(f"Attempting to retrieve channel message for file_id: {file_id}")
                    try:
                        clean_file_id = re.sub(r'\D', '', str(file_id))  # Convert file_id to string
                        await client.get_chat(CHANNEL_ID)  # Check if the channel exists
                        channel_message = await client.get_messages(CHANNEL_ID, int(clean_file_id))
                        if channel_message:
                            sent_message = await channel_message.copy(chat_id=message.from_user.id, disable_notification=True)
                            sent_messages.append(sent_message)
                        # return
                    except ValueError as ve:
                        logger.error(f"❌ Error converting file_id to int: {ve}")
                        await message.reply_text(f"<b>❌ Error retrieving file with ID: {file_id}</b>")
                    except Exception as e:
                        logger.error(f"❌ Error retrieving channel message for file_id {file_id}: {e}")
                
                if sent_messages:
                    reply_success_msg = await message.reply_text(
                        f"<b>🎉 Aʟʟ Fɪʟᴇs Rᴇᴛʀɪᴇᴠᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ !</b>\n\n"
                        f"<b>Nᴏ Pᴏɪɴᴛs Wᴇʀᴇ Dᴇᴅᴜᴄᴛᴇᴅ</b>\n\n"
                        f"<blockquote><b>Tʜᴇsᴇ Fɪʟᴇs Wɪʟʟ Bᴇ Dᴇʟᴇᴛᴇᴅ Iɴ {PAID_TIME} Sᴇᴄᴏɴᴅs. Pʟᴇᴀsᴇ Sᴀᴠᴇ / Fᴏʀᴡᴀʀᴅ Tʜᴇᴍ Tᴏ Yᴏᴜʀ Sᴀᴠᴇᴅ Mᴇssᴀɢᴇs.</b></blockquote>"
                    )
                # print(f"Waiting for {PAID_TIME} seconds before deleting messages.")        
                await asyncio.sleep(PAID_TIME)
                for sent_msg in sent_messages:
                    try:
                        if sent_msg:
                            await client.delete_messages(chat_id=message.from_user.id, message_ids=sent_msg.id)
                        if unlocked_msg:
                            await unlocked_msg.delete()
                        if reply_success_msg and reply_success_msg.text != (
                            f"<b>🗑️ Fɪʟᴇ Dᴇʟᴇᴛᴇᴅ!</b>\n"
                            f"💸 Dᴇᴅᴜᴄᴛᴇᴅ: <b>0 Pᴏɪɴᴛs</b>\n"
                            f"💼 Bᴀʟᴀɴᴄᴇ: <b>{total_points} Pᴏɪɴᴛs</b>\n\n"
                            f"⚠️ <i>Fɪʟᴇ ʀᴇᴍᴏᴠᴇᴅ ғʀᴏᴍ sʏsᴛᴇᴍ. Mᴀᴋᴇ sᴜʀᴇ ɪᴛ's sᴀᴠᴇᴅ.</i>",
                        ):
                            await reply_success_msg.edit_text(
                                f"<b>🗑️ Fɪʟᴇ Dᴇʟᴇᴛᴇᴅ!</b>\n"
                                f"💸 Dᴇᴅᴜᴄᴛᴇᴅ: <b>0 Pᴏɪɴᴛs</b>\n"
                                f"💼 Bᴀʟᴀɴᴄᴇ: <b>{total_points} Pᴏɪɴᴛs</b>\n\n"
                                f"⚠️ <i>Fɪʟᴇ ʀᴇᴍᴏᴠᴇᴅ ғʀᴏᴍ sʏsᴛᴇᴍ. Mᴀᴋᴇ sᴜʀᴇ ɪᴛ's sᴀᴠᴇᴅ.</i>",
                                reply_markup=InlineKeyboardMarkup([
                                    [InlineKeyboardButton("♻️ Uɴʟᴏᴄᴋ Aɢᴀɪɴ", url=f"https://t.me/{client.username}?start={message.command[1]}")]
                                ])
                            )
                    except Exception :
                        pass        
                return
            new_files = [file_id for file_id in file_ids if file_id not in purchased_files]
            if new_files:
                points_needed = int(required_points) if new_files else 0  # Ensure points_needed is an integer

                logger.debug(f"Total points: {total_points}, Points needed: {points_needed}")
            

            if total_points < points_needed:
                buttons = [
                    [
                        InlineKeyboardButton("Tʀʏ Aɢᴀɪɴ ♻️", url=f"https://t.me/{client.username}?start={message.command[1]}"),
                    ],
                    [
                        InlineKeyboardButton("⚡Bᴜʏ Pᴏɪɴᴛs", callback_data="buy_point"),
                        InlineKeyboardButton("🐦‍🔥 Rᴇғᴇʀ", url=referral_link)],
                    [
                        InlineKeyboardButton("🎰 Fʀᴇᴇ Pᴏɪɴᴛs", callback_data="free_points"),
                        InlineKeyboardButton("🕸️ Sᴘɪɴ Wʜᴇᴇʟ", callback_data="spin_wheel")
                    ],
                    [
                        InlineKeyboardButton("👻 Fʀᴇᴇ Pᴏɪɴᴛs Lɪғᴀғᴀ Eᴠᴇʀʏᴅᴀʏ", url="https://t.me/+Ta5P3a3k9mk2N2E1"),
                        InlineKeyboardButton("♾️ Iɴғɪɴɪᴛᴇ Pᴏᴡᴇʀ", callback_data="generate_token")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(buttons)
                await message.reply_text(
                    f"<b>🚫 Aᴄᴄᴇss Dᴇɴɪᴇᴅ!</b>\n\n"
                    f"<b>💾 Tʜɪs Fɪʟᴇ Rᴇǫᴜɪʀᴇs:</b> <u>{required_points} Pᴏɪɴᴛs</u>\n"
                    f"<b>💰 Yᴏᴜʀ Bᴀʟᴀɴᴄᴇ:</b> <u>{total_points} Pᴏɪɴᴛs</u>\n\n"
                    f"<i>🧿 Tᴏ Uɴʟᴏᴄᴋ Tʜɪs Fɪʟᴇ, Yᴏᴜ Nᴇᴇᴅ Mᴏʀᴇ Pᴏɪɴᴛs.</i>\n"
                    f"<i>🎯 Dᴏɴ’ᴛ Wᴏʀʀʏ, Yᴏᴜ Cᴀɴ Bᴜʏ Pᴏɪɴᴛs ᴏʀ Eᴀʀɴ Tʜᴇᴍ Tʜʀᴏᴜɢʜ Rᴇғᴇʀʀᴀʟs.</i>\n\n"
                    f"<blockquote>🌀 <b>Fɪʟᴇs Yᴏᴜ Uɴʟᴏᴄᴋ Cᴀɴ Bᴇ Fᴏʀᴡᴀʀᴅᴇᴅ Iɴsᴛᴀɴᴛʟʏ.</b>\n"
                    f"🛠 <b>Fᴀᴄɪɴɢ Issᴜᴇs?</b> Cᴏɴᴛᴀᴄᴛ: @{OWNER_TAG}</blockquote>",
                    reply_markup=reply_markup
                )
                return

            if referral_points >= points_needed:
                await user_data.update_one({"_id": message.from_user.id}, {"$inc": {"referral_points": -points_needed}})
                logger.debug(f"Deducted {points_needed} points from referral points for user {message.from_user.id}.")
            else:
                remaining_points = required_points - referral_points
                await user_data.update_one(
                    {"_id": message.from_user.id},
                    {"$set": {"referral_points": 0}, "$inc": {"purchased_points": -remaining_points}}
                )

            sent_messages = []
            for msg_id in file_ids:
                try:
                    msg_id = re.sub(r'\D', '', str(msg_id))  # Convert msg_id to string
                    if msg_id:
                        msg_id = int(msg_id)  # Convert to integer
                    channel_message = await client.get_messages(CHANNEL_ID, msg_id)
                    if channel_message:
                        sent_message = await channel_message.copy(
                            chat_id=message.from_user.id,
                            disable_notification=True
                        )
                        sent_messages.append(sent_message)
                except Exception as e:
                    logger.error(f"❌ Error retrieving file for msg_id {msg_id}: {e}")

            update_result = await user_data.update_one(
                {"_id": message.from_user.id},
                {"$addToSet": {"purchased_files": {"$each": file_ids}}}
            )
            logger.debug(f"Update result for purchased files: {update_result.modified_count} documents modified.")

            remaining_points = (referral_points + purchased_points) - points_needed
            reply_msg = await message.reply_text(
                f"<b>✅ Fɪʟᴇ Uɴʟᴏᴄᴋᴇᴅ!</b>\n\n"
                f"🔻 <b>Pᴏɪɴᴛs Dᴇᴅᴜᴄᴛᴇᴅ:</b> {required_points}\n"
                f"💎 <b>Rᴇᴍᴀɪɴɪɴɢ:</b> {remaining_points} Pᴏɪɴᴛs\n\n"
                f"<b><blockquote>⚠️ Tʜɪs Fɪʟᴇ Wɪʟʟ Bᴇ Dᴇʟᴇᴛᴇᴅ Iɴ {PAID_TIME} Sᴇᴄᴏɴᴅs Pʟᴇᴀsᴇ Sᴀᴠᴇ / Fᴏʀᴡᴀʀᴅ Tʜɪs Fɪʟᴇ Tᴏ Yᴏᴜʀ Sᴀᴠᴇᴅ Mᴇssᴀɢᴇs</b></blockquote>"
            )
            await inc_count(encoded_key)

            owner_alert = (
                f"Pᴀɪᴅ Fɪʟᴇs Aᴄᴄᴇssᴇᴅ Bʏ Usᴇʀ : [{message.from_user.first_name}](tg://user?id={message.from_user.id}) "
                f"({message.from_user.id})\n"
                f"👻 Rᴇᴍᴀɪɴɪɴɢ Bᴀʟᴀɴᴄᴇ : {remaining_points}\n"
                f"⚡ Accessed Files: {file_ids}\n"
                f"🙅 File Name: {file_name}\n"
            )

            access_link = f"https://t.me/{client.username}?start={message.command[1]}"

            reply_markup = InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔗 Oᴘᴇɴ Fɪʟᴇ", url=access_link)]]
            )
            await client.send_message(
                    chat_id=DUMB_CHAT,
                    text=owner_alert,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN,
                )

            await asyncio.sleep(PAID_TIME)
            for sent_msg in sent_messages:
                try:
                    if sent_msg:
                        await client.delete_messages(chat_id=message.from_user.id, message_ids=sent_msg.id)     
                except Exception as e:
                    logger.error(f"❌ Error deleting message {sent_msg.id}: {e}")

            if reply_msg and reply_msg.text != (
                f"<b>🗑️ Fɪʟᴇ Dᴇʟᴇᴛᴇᴅ</b>\n"
                f"<i>— {required_points} ᴘᴏɪɴᴛs ᴜsᴇᴅ</i>\n"
                f"<i>— {remaining_points} ʀᴇᴍᴀɪɴɪɴɢ</i>\n\n"
                f"<b>⚠️ Aᴄᴄᴇss Exᴘɪʀᴇᴅ.</b>\n"
                f"<i>Mᴀᴋᴇ sᴜʀᴇ ʏᴏᴜ sᴀᴠᴇᴅ ɪᴛ ɴᴇxᴛ ᴛɪᴍᴇ.</i>",
            ):
                await reply_msg.edit_text(
                    f"<b>🗑️ Fɪʟᴇ Dᴇʟᴇᴛᴇᴅ</b>\n"
                    f"<i>— {required_points} ᴘᴏɪɴᴛs ᴜsᴇᴅ</i>\n"
                    f"<i>— {remaining_points} ʀᴇᴍᴀɪɴɪɴɢ</i>\n\n"
                    f"<b>⚠️ Aᴄᴄᴇss Exᴘɪʀᴇᴅ.</b>\n"
                    f"<i>Mᴀᴋᴇ sᴜʀᴇ ʏᴏᴜ sᴀᴠᴇᴅ ɪᴛ ɴᴇxᴛ ᴛɪᴍᴇ.</i>",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("♻️ Rᴇᴜɴʟᴏᴄᴋ", url=f"https://t.me/{client.username}?start={message.command[1]}")]
                        ]),
                )
            return
    
        except Exception as e:
            logger.error(f"❌ Error processing batch link: {e}")
            await message.reply_text("<b>❌ Invalid Batch Access Link. Please Check.</b>")
        return

    verify_status = await get_verify_status(id)
    if USE_SHORTLINK and (not U_S_E_P):
        for i in range(1):
            if id in ADMINS:
                continue
            if verify_status['is_verified'] and VERIFY_EXPIRE < (time.time() - verify_status['verified_time']):
                await update_verify_status(id, is_verified=False)
            if "verify_" in message.text:
                _, token = message.text.split("_", 1)
                if verify_status['verify_token'] != token:
                    # Send alert to OWNER_ID for invalid token
                    invalid_alert_message = (
                        f"😂 Iɴᴠᴀʟɪᴅ Tᴏᴋᴇɴ Aᴛᴛᴇᴍᴘᴛ\n\n"
                        f"👤 Usᴇʀ ID: [{message.from_user.first_name}](tg://user?id={id})\n"
                        f"☠️Aᴛᴛᴇᴍᴘᴛᴇᴅ Tᴏᴋᴇɴ : {token}\n"
                        f"♻️Vᴀʟɪᴅ Tᴏᴋᴇɴ : {verify_status['verify_token']}\n"
                        f"👻Tɪᴍᴇ : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    inline_button = InlineKeyboardButton(
                        "🔗 Vᴇʀɪғʏ Lɪɴᴋ", url=f"https://t.me/{client.username}?start=verify_{verify_status['verify_token']}"
                    )
                    inline_keyboard = InlineKeyboardMarkup([[inline_button]])
                    await client.send_message(DUMB_CHAT, invalid_alert_message,reply_markup=inline_keyboard, parse_mode=ParseMode.MARKDOWN)
                
                    return await message.reply_photo(
                        
                        photo=INVALID_TOKEN,  # Replace with your invalid token image URL
                        caption=(
                            "💀 <b>Iɴᴠᴀʟɪᴅ Tᴏᴋᴇɴ Dᴇᴛᴇᴄᴛᴇᴅ..!</b>\n\n"
                            "🚫 <b>Aᴄᴄᴇss Dᴇɴɪᴇᴅ: Yᴏᴜʀ Tᴏᴋᴇɴ Hᴀs Bᴇᴇɴ Cᴏʀʀᴜᴘᴛᴇᴅ Oʀ Exᴘɪʀᴇᴅ! ⏳</b>\n\n"
                            "🔄 <b>Gᴇɴᴇʀᴀᴛᴇ A Nᴇᴡ Oɴᴇ Uꜱɪɴɢ</b> 👉 <code>/start</code>\n\n"
                            "🛡️ <i>Sᴇᴄᴜʀɪᴛʏ Pʀᴏᴛᴏᴄᴏʟ 42-A Iɴɪᴛɪᴀᴛᴇᴅ...</i>\n"
                            "💡 <i>Fᴀᴄɪɴɢ Iꜱꜱᴜᴇs? Cᴏɴɴᴇᴄᴛ ᴛᴏ Tʜᴇ Nᴇᴛᴡᴏʀᴋ (Sᴜᴘᴘᴏʀᴛ)!</i> 💬"
                        ),
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🔁 Rᴇʙᴏᴏᴛ Pʀᴏᴄᴇs", url=f'https://t.me/{client.username}?start=start'),
                            InlineKeyboardButton("🕶️ Dᴀʀᴋ Sᴜᴘᴘᴏʀᴛ", callback_data="support")]
                        ])
                    )
                await update_verify_status(id, is_verified=True, verified_time=time.time())
                if verify_status["link"] == "":
                    reply_markup = None

                verified_time = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                expiry_time = datetime.fromtimestamp(time.time() + VERIFY_EXPIRE).strftime('%Y-%m-%d %H:%M:%S')
                verified_alert_message = (
                    f"👀Tᴏᴋᴇɴ Vᴇʀɪғɪᴇᴅ\n\n"
                    f"👤 Usᴇʀ ID: [{message.from_user.first_name}](tg://user?id={id})\n"
                    f"👻Vᴇʀɪғɪᴇᴅ Tɪᴍᴇ : {verified_time}\n"
                    f"👾Exᴘɪʀʏ Tɪᴍᴇ : {expiry_time}"
                )
                await client.send_message(DUMB_CHAT, verified_alert_message, parse_mode=ParseMode.MARKDOWN)
                await message.reply_photo(
                    photo=TOKEN_VERIFIED,
                    caption = (
                        "<b>🛸 Aᴄᴄᴇss Gʀᴀɴᴛᴇᴅ: Nᴇxᴜs Pʀᴏᴛᴏᴄᴏʟ Aᴄᴛɪᴠᴀᴛᴇᴅ</b>\n\n"
                        "✅ <b>Tᴏᴋᴇɴ Aᴜᴛʜᴇɴᴛɪᴄᴀᴛᴇᴅ!</b>\n"
                        "🕶️ <i>Yᴏᴜ ᴀʀᴇ ɴᴏᴡ ɪɴsɪᴅᴇ ᴛʜᴇ ᴍᴀᴛʀɪx...</i>\n\n"
                        "⏳ <b>Vᴀʟɪᴅɪᴛʏ Pᴇʀɪᴏᴅ:</b> 24H ⏰\n"
                        "🔮 <b>Dᴀᴛᴀ Tʀᴀɪʟ: Eɴᴄʀʏᴘᴛᴇᴅ</b>\n"
                        "⚡ <i>Aᴄᴄᴇss Tᴏ ᴛʜᴇ Uʟᴛɪᴍᴀᴛᴇ Hᴜʙ Gʀᴀɴᴛᴇᴅ...</i>\n"
                        "🛠️ <b>⚠️ Aɴʏ Uɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ Mᴏᴠᴇs Wɪʟʟ Tʀɪɢɢᴇʀ A Dɪɢɪᴛᴀʟ Fᴀɪʟsᴀғᴇ...</b>"
                    ),
                    reply_markup=reply_markup,
                    quote=True
                )

    # Continue with the rest of the code as before
    if len(message.text) > 7:
        for i in range(1):
            if USE_SHORTLINK and (not U_S_E_P):
                if USE_SHORTLINK: 
                    if id not in ADMINS:
                        try:
                            if not verify_status['is_verified']:
                                continue
                        except:
                            continue
            try:
                base64_string = message.text.split(" ", 1)[1]
            except:
                return
            if base64_string.startswith("refer="):
                referrer_id = base64_string.split("=")[1]
                # Handle the referral ID here
                await store_referrer(referrer_id, id)
                await message.reply_text("Rᴇғᴇʀ Sᴜᴄᴄᴇssғᴜʟʟʏ Sᴛᴏʀᴇᴅ...")
                return
            else:
                _string = await decode(base64_string)
                if _string is None:
                    await message.reply_text("Error decoding base64 string. Please try again.")
                    return
                if _string is not None:
                    argument = _string.split("-")
            if (len(argument) == 5 )or (len(argument) == 4):
                if not await present_hash(base64_string):
                    try:
                        await gen_new_count(base64_string)
                    except:
                        pass
                await inc_count(base64_string)
                if len(argument) == 5:
                    try:
                        start = int(int(argument[3]) / abs(client.db_channel.id))
                        end = int(int(argument[4]) / abs(client.db_channel.id))
                    except:
                        return
                    if start <= end:
                        ids = range(start, end+1)
                    else:
                        ids = []
                        i = start
                        while True:
                            ids.append(i)
                            i -= 1
                            if i < end:
                                break
                elif len(argument) == 4:
                    try:
                        ids = [int(int(argument[3]) / abs(client.db_channel.id))]
                    except:
                        return
                temp_msg = await message.reply("<b>🔍 Sᴄᴀɴɴɪɴɢ Fɪʟᴇ Sɪɢɴᴀᴛᴜʀᴇs...</b>")
                await asyncio.sleep(0.3)
                await temp_msg.edit("<b>🧠 Aᴄᴛɪᴠᴀᴛɪɴɢ Aɪ Mᴏᴅᴜʟᴇs...</b>")
                await asyncio.sleep(0.3)
                await temp_msg.edit("<b>⚡ Eɴᴛᴇʀɪɴɢ Gʜᴏsᴛ Mᴏᴅᴇ...</b>") 
                await asyncio.sleep(0.3)
                await temp_msg.edit("<b>🍻 Aʟᴍᴏsᴛ Dᴏɴᴇ...</b>")
                try:
                    messages = await get_messages(client, ids)
                except:
                    await message.reply_text("Cʜᴜᴅ Gʏᴇ Gᴜʀᴜ..! 🥲")
                    return
                await temp_msg.delete()

                hash_value = message.command[1]
                file_data = await link_data.find_one({'hash': hash_value})
                user_info = await get_user_info(message.from_user.id)
                file_name = file_data.get('file_name', 'Unknown File') if file_data else 'Unknown File'
                snt_msgs = []

                premium_status = user_info.get("premium", False)
                is_admin = message.from_user.id in ADMINS  # Check if user is an admin
                if waiting_timer_status and not premium_status and not is_admin:
                    user_id = message.from_user.id
                    user_data = await link_data.find_one({'user_id': user_id}) or {}
                    accessed_links = user_data.get('accessed_links', [])
                    last_reset = user_data.get('last_reset', 0)

                    current_time = int(time.time())
                    if current_time - last_reset >= 86400:
                        accessed_links = []
                        last_reset = current_time

                    accessed_links.append(hash_value)
                    await link_data.update_one(
                        {'user_id': user_id},
                        {'$set': {'accessed_links': accessed_links, 'last_reset': last_reset}},
                        upsert=True
                    )

                    if waiting_timer_status:
                        unique_links_accessed = len(accessed_links)
                        total_time = min(60 + ((unique_links_accessed - 1) * 30), 300)

                        delay_msg = await message.reply(
                            f"<b>🚫 Aᴄᴄᴇꜱꜱ Dᴇɴɪᴇᴅ — Cᴏᴏʟᴅᴏᴡɴ Aᴄᴛɪᴠᴇ</b>\n\n"
                            f"<b>🕒 Wᴀɪᴛɪɴɢ Pᴇʀɪᴏᴅ: {total_time // 60} Mɪɴᴜᴛᴇ(ꜱ)</b>\n\n"
                            f"🎮 <i>Gᴀᴍᴇ Cʜᴀɴɢᴇʀs Dᴏɴ’ᴛ Wᴀɪᴛ.</i>\n"
                            f"⚡ <b>Uɴʟᴏᴄᴋ Gᴏᴅ Mᴏᴅᴇ: Gᴏ Pʀᴇᴍɪᴜᴍ ⏩</b>",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("⚡ Gᴏᴅ Mᴏᴅᴇ", callback_data="buy_prem"),
                            InlineKeyboardButton("🎁 Fʀᴇᴇ", callback_data="free_points")],
                        ])
                    )

                    # Countdown timer
                    for remaining in range(total_time, 0, -10):
                        try:
                            await delay_msg.edit(
                                f"<b>🕓 Cᴏᴏʟᴅᴏᴡɴ Iɴ Pʀᴏɢʀᴇss...</b>\n"
                                f"<b>⏳ {remaining // 60}ᴍ {remaining % 60}s Rᴇᴍᴀɪɴɪɴɢ...</b>\n\n"
                                f"🎮 <i>Gᴀᴍᴇ Cʜᴀɴɢᴇʀs Dᴏɴ’ᴛ Wᴀɪᴛ.</i>\n"
                                f"⚡ <b>Uɴʟᴏᴄᴋ Gᴏᴅ Mᴏᴅᴇ: Gᴏ Pʀᴇᴍɪᴜᴍ</b>",
                                reply_markup=InlineKeyboardMarkup([
                                    [InlineKeyboardButton("⚡ Gᴏᴅ Mᴏᴅᴇ", callback_data="buy_prem"),
                                    InlineKeyboardButton("🕹️ Fʀᴇᴇ ", callback_data="free_points")]
                                ])
                                )
                        except:
                            pass
                        await asyncio.sleep(10)

                        try:
                            await delay_msg.edit("<b>✅ Aᴄᴄᴇꜱꜱ Gʀᴀɴᴛᴇᴅ — Fɪʟᴇs Aʀᴇ Nᴏᴡ Uɴʟᴏᴄᴋᴇᴅ 🔓</b>")
                            await asyncio.sleep(1)
                            await delay_msg.delete()
                        except:
                            pass

                batch_size = 15  # Process messages in batches for faster sending
                for i in range(0, len(messages), batch_size):
                    batch = messages[i:i + batch_size]
                    tasks = []
                    for msg in batch:
                        try:
                            if msg.service:
                                continue
                            if msg.text:
                                tasks.append(message.reply_text(msg.text))
                                continue

                            caption = msg.caption.html if msg.caption else ""
                            if msg.document or msg.video or msg.audio or msg.animation:
                                file_details = await get_file_details(msg)
                                premium_message = "" if premium_status else "🚫 <b>Aᴄᴄᴇss Dᴇɴɪᴇᴅ</b>: Pᴏᴡᴇʀ-ᴜᴘ RᴇQᴜɪʀᴇᴅ 🔒\n"
                                caption = CUSTOM_CAPTION.format(
                                    title=file_name,
                                    premium_message=premium_message,
                                    previouscaption=msg.caption.html if msg.caption else ""
                                )
                            reply_markup = get_caption_buttons()
                            protect_content = await should_protect_content(user_info)
                            tasks.append(msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup, protect_content=protect_content))
                        except Exception as e:
                            print(f"Error sending message: {e}")
                            pass

                    results = []
                    for task in tasks:
                        try:
                            result = await task
                            results.append(result)
                            await asyncio.sleep(0.5)
                        except Exception as e:
                            print(f"FloodWait detected: waiting for {e.x} seconds")
                            await asyncio.sleep(e.x)
                            try:
                                if isinstance(task, Message):
                                    result = await task.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup, protect_content=protect_content)
                                    results.append(result)
                            except Exception as retry_error:
                                print(f"Error during retry: {retry_error}")
                        except Exception as e:
                            print(f"Error sending message: {e}")
                            pass
                    
                    snt_msgs.extend([res for res in results if isinstance(res, Message)])

                    await asyncio.sleep(2)

                await inc_count(base64_string)
                owner_alert = (
                    f"📢 Usᴇʀ Aᴄᴄᴇssᴇᴅ Fɪʟᴇ:\n"
                    f"👤 Usᴇʀ : [{message.from_user.first_name}](tg://user?id={message.from_user.id}) ({message.from_user.id})\n"
                    f"👾 Fɪʟᴇ Nᴀᴍᴇ: {file_name}\n"
                )
                access_link = f"https://t.me/{client.username}?start={message.command[1]}"
                reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔗 Oᴘᴇɴ Fɪʟᴇ", url=access_link)]])
                await client.send_message(chat_id=DUMB_CHAT, text=owner_alert, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

                if snt_msgs:
                    user_plan = await get_user_plan_group(id)
                    if await can_keep_files_permanently(user_info):
                        await message.reply(
                            f"<b>🎮 Aᴄᴄᴇꜱꜱ Uɴʟᴏᴄᴋᴇᴅ: {user_plan} Mᴏᴅᴇ</b>\n"
                            "📂 Fɪʟᴇ Sᴛᴀᴛᴜs: Pᴇʀᴍᴀɴᴇɴᴛ\n"
                            "🧬 Mᴏᴅᴜʟᴇ: Gᴏᴅ-Tɪᴇʀ Sᴛᴏʀᴀɢᴇ\n"
                            "<i>Yᴏᴜ'ʀᴇ ᴏɴ ᴀ ʟᴇᴠᴇʟ ᴀʙᴏᴠᴇ ᴛʜᴇ ʀᴜʟᴇꜱ.</i>",
                        reply_markup=InlineKeyboardMarkup([
                                [InlineKeyboardButton("⚔️ Aᴄᴋɴᴏᴡʟᴇᴅɢᴇ", callback_data=f"like_{file_data['_id']}"),
                                InlineKeyboardButton("💣 Fʟᴀɢ Fᴏʀ Wᴀʀ", callback_data=f"dislike_{file_data['_id']}")]
                            ])
                        )
                        return
                    if SECONDS > 0:
                        notification_msg = await message.reply(
                            "<b>⚡ Fɪʟᴇ Rɪsᴋ Aʟᴇʀᴛ...!</b>\n"
                            "💣 Aᴜᴛᴏ-Wɪᴘᴇ Dᴇᴛᴇᴄᴛᴇᴅ. Aᴄᴛ Fᴀsᴛ.\n\n"
                            "<b>🌩️ Lɪᴋᴇ Oʀ Dɪsʟɪᴋᴇ...?</b>",
                            reply_markup=InlineKeyboardMarkup([
                                [InlineKeyboardButton("❤️ Lɪᴋᴇ", callback_data=f"like_{file_data['_id']}"),
                                InlineKeyboardButton("💔 Dɪsʟɪᴋᴇ", callback_data=f"dislike_{file_data['_id']}")]
                            ])
                        )
                        await asyncio.sleep(SECONDS)
                        for snt_msg in snt_msgs:
                            try:
                                await snt_msg.delete()
                            except:
                                pass
                premium_status = await is_premium(id)
                buttons = [
                    [InlineKeyboardButton("🎮 Rᴇᴍᴀᴛᴄʜ 🔁", url=f"https://t.me/{client.username}?start={message.command[1]}")]
                ] 
                if not premium_status:
                    buttons[0].append(InlineKeyboardButton("💸 Uᴘɢʀᴀᴅᴇ", callback_data="buy_prem"))
                reply_markup = InlineKeyboardMarkup(buttons)

                await notification_msg.edit(
                    "<b>🗑️ Fɪʟᴇ Wɪᴘᴇᴅ</b>\n"
                    "🕶️ Tʀᴀᴄᴇ: Zᴇʀᴏ\n"
                    "⚡ Gʜᴏsᴛ Mᴏᴅᴇ: Aᴄᴛɪᴠᴇ",
                    reply_markup=InlineKeyboardMarkup(buttons),
                    disable_web_page_preview=True
                )
                return

            if (U_S_E_P):
                if verify_status['is_verified'] and VERIFY_EXPIRE < (time.time() - verify_status['verified_time']):
                    await update_verify_status(id, is_verified=False)

            if (not U_S_E_P) or (id in ADMINS) or (verify_status['is_verified']):
                if len(argument) == 3:
                    try:
                        start = int(int(argument[1]) / abs(client.db_channel.id))
                        end = int(int(argument[2]) / abs(client.db_channel.id))
                    except:
                        return
                    if start <= end:
                        ids = range(start, end+1)
                    else:
                        ids = []
                        i = start
                        while True:
                            ids.append(i)
                            i -= 1
                            if i < end:
                                break
                elif len(argument) == 2:
                    try:
                        ids = [int(int(argument[1]) / abs(client.db_channel.id))]
                    except:
                        return
                temp_msg = await message.reply("<b>🔍 Sᴄᴀɴɴɪɴɢ Fɪʟᴇ Sɪɢɴᴀᴛᴜʀᴇs...</b>")
                await asyncio.sleep(0.3)
                await temp_msg.edit("<b>🧠 Aᴄᴛɪᴠᴀᴛɪɴɢ Aɪ Mᴏᴅᴜʟᴇs....</b>")
                await asyncio.sleep(0.3)
                await temp_msg.edit("<b>⚡ Eɴᴛᴇʀɪɴɢ Gʜᴏsᴛ Mᴏᴅᴇ...</b>") 
                await asyncio.sleep(0.3)
                await temp_msg.edit("<b>🍻 Aʟᴍᴏsᴛ Dᴏɴᴇ...</b>")
                try:
                    messages = await get_messages(client, ids)
                except:
                    await message.reply_text("Cʜᴜᴅ Gʏᴇ Gᴜʀᴜ..! 🥲")
                    return
                await temp_msg.delete()
                hash_value = message.command[1]  # Extract hash from /start command
                file_data = await link_data.find_one({'hash': hash_value})
                user_info = await get_user_info(message.from_user.id)
                file_name = file_data.get('file_name', 'Unknown File') if file_data else 'Unknown File'  # Default to 'Unknown File' if not found
                snt_msgs = []
                premium_status = user_info.get("premium", False)

                # Optimize accessed_links and last_reset initialization
                accessed_links = locals().get('accessed_links', [])
                accessed_links.append(hash_value)
                last_reset = locals().get('last_reset', int(time.time()))
                await link_data.update_one(
                    {'user_id': user_id},
                    {'$set': {'accessed_links': accessed_links, 'last_reset': last_reset}},
                    upsert=True
                )

                is_admin = message.from_user.id in ADMINS  # Check if user is an admin
                if waiting_timer_status and not premium_status and not is_admin:
                    unique_links_accessed = len(accessed_links)
                    total_time = min(60 + ((unique_links_accessed - 1) * 30), 300)  # Max 10 min limit

                    delay_msg = await message.reply(
                        f"<b>⏳ Aᴄᴄᴇꜱꜱ Dᴇɴɪᴇᴅ — Cᴏᴏʟᴅᴏᴡɴ Iɴ Pʀᴏɢʀᴇss...</b>\n"
                        f"<b>🕒 Wᴀɪᴛɪɴɢ Tɪᴍᴇ : {total_time // 60} Mɪɴᴜᴛᴇ(ꜱ)</b>\n\n"
                        f"🎮 <i>Gᴀᴍᴇ Cʜᴀɴɢᴇʀs Dᴏɴ’ᴛ Wᴀɪᴛ.</i>\n"
                        f"⚡ <b>Uɴʟᴏᴄᴋ Gᴏᴅ Mᴏᴅᴇ: Gᴏ Pʀᴇᴍɪᴜᴍ</b>",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("☠️ Gᴏᴅ Mᴏᴅᴇ (Pʀᴇᴍɪᴜᴍ)", callback_data="buy_prem"),
                            InlineKeyboardButton("🧪 Fʀᴇᴇ", callback_data="free_points")],
                        ])
                    )

                    # Countdown timer
                    for remaining in range(total_time, 0, -10):
                        try:
                            await delay_msg.edit(
                                f"🎭 Aᴄᴄᴇꜱꜱ Dᴇɴɪᴇᴅ — Cᴏᴏʟᴅᴏᴡɴ Iɴ Pʀᴏɢʀᴇss...</b>\n"
                                f"<b>⏳ {remaining // 60}ᴍ {remaining % 60}s Rᴇᴍᴀɪɴɪɴɢ...</b>\n\n"
                                f"🎮 <i>Gᴀᴍᴇ Cʜᴀɴɢᴇʀs Dᴏɴ’ᴛ Wᴀɪᴛ.</i>\n"
                                f"⚡ <b>Uɴʟᴏᴄᴋ Gᴏᴅ Mᴏᴅᴇ: Gᴏ Pʀᴇᴍɪᴜᴍ</b>",
                                reply_markup=InlineKeyboardMarkup([
                                    [InlineKeyboardButton("☠️ Gᴏᴅ Mᴏᴅᴇ", callback_data="buy_prem"),
                                    InlineKeyboardButton("🕹️ Fʀᴇᴇ", callback_data="free_points")]
                                ])
                            )
                        except:
                            pass
                        await asyncio.sleep(10)

                    try:
                        await delay_msg.edit("<b>✅ Mɪssɪᴏɴ Cᴏᴍᴘʟᴇᴛᴇ — Yᴏᴜʀ Fɪʟᴇs Aʀᴇ Uɴʟᴏᴄᴋᴇᴅ!</b>")
                        await asyncio.sleep(1)
                        await delay_msg.delete()
                    except:
                        pass   
                # anya = []
                batch_size = 20  # Process messages in batches for faster sending
                for i in range(0, len(messages), batch_size):
                    batch = messages[i:i + batch_size]
                    tasks = []
                    for msg in batch:
                        try:
                            if msg.service:
                                continue
                            if msg.text:
                                tasks.append(message.reply_text(msg.text))
                                continue

                            caption = msg.caption.html if msg.caption else ""
                            if msg.document or msg.video or msg.audio or msg.animation:
                                file_details = await get_file_details(msg)
                                premium_message = "" if premium_status else "🚫 <b>Aᴄᴄᴇss Dᴇɴɪᴇᴅ</b>: Pᴏᴡᴇʀ-ᴜᴘ RᴇQᴜɪʀᴇᴅ 🔒\n"
                                caption = CUSTOM_CAPTION.format(
                                    title=file_name,
                                    premium_message=premium_message,
                                    previouscaption=msg.caption.html if msg.caption else ""
                                )
                            reply_markup = get_caption_buttons()
                            protect_content = await should_protect_content(user_info)
                            tasks.append(msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup, protect_content=protect_content))
                        except Exception as e:
                            print(f"Error sending message: {e}")
                            pass

                    results = []
                    for task in tasks:
                        try:
                            result = await task
                            results.append(result)
                            # await asyncio.sleep(0.5)
                        except Exception as e:
                            print(f"FloodWait detected: waiting for {e.x} seconds")
                            await asyncio.sleep(e.x)
                            try:
                                if isinstance(task, Message):
                                    result = await task.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup, protect_content=protect_content)
                                    results.append(result)
                            except Exception as retry_error:
                                print(f"Error during retry: {retry_error}")
                        except Exception as e:
                            print(f"Error sending message: {e}")
                            pass
                    
                    snt_msgs.extend([res for res in results if isinstance(res, Message)])

                    await asyncio.sleep(2)

                await inc_count(base64_string)
                hash_value = message.command[1]
                file_data = await link_data.find_one({'hash': hash_value})
                file_name = file_data.get('file_name', 'Unknown File') if file_data else 'Unknown File'
                owner_alert = (
                    f"🎯 <b>Fɪʟᴇ Aᴄᴄᴇꜱꜱ Aʟᴇʀᴛ</b>\n"
                    f"👤 <b>Uꜱᴇʀ:</b> <a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a> <code>({message.from_user.id})</code>\n"
                    f"📁 <b>Fɪʟᴇ Nᴀᴍᴇ:</b> <code>{file_name}</code>\n"
                    f"⏱️ <i>RᴇQᴜᴇꜱᴛ Tʀᴀᴄᴋᴇᴅ</i>"
                )
                access_link = f"https://t.me/{client.username}?start={message.command[1]}"

                reply_markup = InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔗 Oᴘᴇɴ Fɪʟᴇ", url=access_link)]]
                )
                await client.send_message(
                    chat_id=DUMB_CHAT,
                    text=owner_alert,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML,
                )
            try:
                if snt_msgs:
                    user_plan = await get_user_plan_group(id)
                    if await can_keep_files_permanently(user_info):
                        await message.reply(
                            f"<b>🎮 Aᴄᴄᴇꜱꜱ Uɴʟᴏᴄᴋᴇᴅ: {user_plan} Mᴏᴅᴇ</b>\n"
                            "📂 Fɪʟᴇ Sᴛᴀᴛᴜs: Pᴇʀᴍᴀɴᴇɴᴛ\n"
                            "🧬 Mᴏᴅᴜʟᴇ: Gᴏᴅ-Tɪᴇʀ Sᴛᴏʀᴀɢᴇ\n"
                            "<i>Yᴏᴜ'ʀᴇ ᴏɴ ᴀ ʟᴇᴠᴇʟ ᴀʙᴏᴠᴇ ᴛʜᴇ ʀᴜʟᴇꜱ.</i>",
                        reply_markup=InlineKeyboardMarkup([
                                [InlineKeyboardButton("⚔️ Aᴄᴋɴᴏᴡʟᴇᴅɢᴇ", callback_data=f"like_{file_data['_id']}"),
                                InlineKeyboardButton("💣 Fʟᴀɢ Fᴏʀ Wᴀʀ", callback_data=f"dislike_{file_data['_id']}")]
                            ])
                        )
                        return
                    if SECONDS > 0:
                        notification_msg = await message.reply(
                            "<b>⚡️ Fɪʟᴇ Rɪsᴋ Aʟᴇʀᴛ...!</b>\n"
                            "💣 Aᴜᴛᴏ-Wɪᴘᴇ Dᴇᴛᴇᴄᴛᴇᴅ. Aᴄᴛ Fᴀsᴛ.\n\n"
                             "<b>🌩️ Lɪᴋᴇ Oʀ Dɪsʟɪᴋᴇ...?</b>",
                            reply_markup=InlineKeyboardMarkup([
                                [InlineKeyboardButton("❤️ Lɪᴋᴇ", callback_data=f"like_{file_data['_id']}"),
                                InlineKeyboardButton("💔 Dɪsʟɪᴋᴇ", callback_data=f"dislike_{file_data['_id']}")]
                            ])
                        )
                        await asyncio.sleep(SECONDS)

                        for snt_msg in snt_msgs: 
                            try:
                                await snt_msg.delete()
                            except:
                                pass
                premium_status = await is_premium(id)
                buttons = [
                    [InlineKeyboardButton("🎮 Rᴇᴍᴀᴛᴄʜ 🔁", url=f"https://t.me/{client.username}?start={message.command[1]}")]
                ] 
                if not premium_status:
                    buttons[0].append(InlineKeyboardButton("💸 Uᴘɢʀᴀᴅᴇ", callback_data="buy_prem"))
                reply_markup = InlineKeyboardMarkup(buttons)

                await notification_msg.edit(
                    "<b>🗑️ Fɪʟᴇ Wɪᴘᴇᴅ</b>\n"
                    "🕶️ Tʀᴀᴄᴇ: Zᴇʀᴏ\n"
                    "⚡ Gʜᴏsᴛ Mᴏᴅᴇ: Aᴄᴛɪᴠᴇ",
                    reply_markup=InlineKeyboardMarkup(buttons),
                    disable_web_page_preview=True
                )
                return
            except:
                    newbase64_string = await encode(f"sav-ory-{_string}")
                    if not await present_hash(newbase64_string):
                        try:
                            await gen_new_count(newbase64_string)
                        except:
                            pass
                    clicks = await get_clicks(newbase64_string)
                    newLink = f"https://t.me/{client.username}?start={newbase64_string}"
                    link = await get_shortlink(SHORTLINK_API_URLS, SHORTLINK_API_KEYS, newLink)
                    if USE_PAYMENT:
                        btn = [
                        [InlineKeyboardButton("⚡ Cʟɪᴄᴋ Tᴏ Oᴘᴇɴ ⚡", url=link)],
                        [InlineKeyboardButton("❤️‍🔥 Bᴇᴄᴏᴍᴇ Pʀᴇᴍɪᴜᴍ", callback_data="buy_prem")]
                        ]
                    else:
                        btn = [
                        [InlineKeyboardButton("⚡ Cʟɪᴄᴋ Tᴏ Oᴘᴇɴ ⚡", url=link)],
                        [InlineKeyboardButton('Hᴏᴡ Tᴏ Oᴘᴇɴ Lɪɴᴋ 🛠', url=TUT_VID)]
                        ]
                    await message.reply(
                        f"<b>🔺 Aᴄᴄᴇss Rᴇsᴛʀɪᴄᴛᴇᴅ: Fɪʟᴇ Eɴᴄʀʏᴘᴛᴇᴅ 🔻</b>\n\n"
                        "<blockquote>💡 Dᴇᴄᴏᴅᴇ ᴛʜᴇ Cʏʙᴇʀ Tʀᴜᴛʜ. Tᴀᴘ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ᴛᴏ ᴜɴʟᴏᴄᴋ..</blockquote>\n\n"
                        "<b>⏳ Tɪᴍᴇ ɪs Rᴜɴɴɪɴɢ Oᴜᴛ… Aᴄᴛɪᴠᴀᴛᴇ Pʀᴇᴍɪᴜᴍ Aᴄᴄᴇss ɴᴏᴡ!</b>",
                        reply_markup=InlineKeyboardMarkup(btn),
                        protect_content=False,
                        quote=True
                    )
                    return
    
    for i in range(1):
        if USE_SHORTLINK and (not U_S_E_P):
            if USE_SHORTLINK : 
                if id not in ADMINS:
                    try:
                        if not verify_status['is_verified']:
                            continue
                    except:
                        continue
        start_pic = random.choice(START_PIC)
        mention = message.from_user.mention  # Get the user's mention
        start_msg = get_start_msg(mention)  # Generate the start message dynamically

        await message.reply_photo(
            photo=start_pic,
            caption=start_msg,
            reply_markup=reply_markup,
            # message_effect_id=effect_id,
            quote=True
        )
        return
    if USE_SHORTLINK and (not U_S_E_P): 
        if id in ADMINS:
            return
        verify_status = await get_verify_status(id)
        if not verify_status['is_verified']:
            token = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            await update_verify_status(id, verify_token=token, link="")

            long_url = f'https://telegram.dog/{client.username}?start=verify_{token}'
            link = await get_shortlink(SHORTLINK_API_URLS, SHORTLINK_API_KEYS, long_url)

            btn = [
                [InlineKeyboardButton("💀 Dᴇᴄʀʏᴘᴛ & Rᴇᴄʟᴀɪᴍ Kᴇʏ", url=link)],
                [InlineKeyboardButton('🛠 Dᴇᴄᴏᴅᴇ Mᴀɴᴜᴀʟ', url=TUT_VID),
                 InlineKeyboardButton("Bᴜʏ Pʀᴇᴍɪᴜᴍ", callback_data="buy_prem")],
                [InlineKeyboardButton("🎡 Cʏʙᴇʀ Sᴘɪɴ", callback_data="spin_wheel"),
                 InlineKeyboardButton("⚡ Hᴀᴄᴋ ᴛʜᴇ Mᴀᴛʀɪx", callback_data="free_points")]
            ] if USE_PAYMENT else [
                [InlineKeyboardButton("💀 Dᴇᴄʀʏᴘᴛ & Rᴇᴄʟᴀɪᴍ Kᴇʏ", url=link)],
                [InlineKeyboardButton('👁‍🗨 Dᴀʀᴋ Nᴇᴛ Gᴀᴛᴇ', url=TUT_VID)]
            ]

            await message.reply_photo(
                photo=EXPIRED_TOKEN,
                caption="<b>⚠️ Aᴄᴄᴇss Dᴇɴɪᴇᴅ: Tᴏᴋᴇɴ Exᴘɪʀᴇᴅ</b>\n\n"
                        "🕰️ <b>Tɪᴍᴇᴏᴜᴛ:</b> 24H\n"
                        "🕶️ <b>Aᴄᴛɪᴏɴ RᴇQᴜɪʀᴇᴅ:</b> Rᴇɴᴇᴡ Yᴏᴜʀ Tᴏᴋᴇɴ.\n\n"
                        "<blockquote expandable>🔍 <b>Wʜᴀᴛ Iꜱ Tʜᴇ Tᴏᴋᴇɴ?</b>\n"
                        "🔺 Tʜɪs Is A Dɪɢɪᴛᴀʟ Aᴜᴛʜᴏʀɪᴢᴀᴛɪᴏɴ Kᴇʏ. Gᴀɪɴ 24H Aᴄᴄᴇss Bʏ Sʜᴀʀɪɴɢ A Sɪɴɢʟᴇ Aᴅ.\n\n"
                        "🛡️ <b>Yᴏᴜʀ Mɪssɪᴏɴ:</b> Cʟɪᴄᴋ 'Cʟɪᴄᴋ Hᴇʀᴇ', Fᴏʟʟᴏᴡ Tʜᴇ Pʀᴏᴄᴇᴅᴜʀᴇ, Gᴀɪɴ Exᴄʟᴜsɪᴠᴇ Aᴄᴄᴇss.\n\n"
                        "🕵️‍♂️ <b>Nᴇᴇᴅ A Hᴀᴄᴋ?</b> /help</blockquote>",
                reply_markup=InlineKeyboardMarkup(btn),
                quote=True
            )
            return
    return

#=====================================================================================#

WAIT_MSG = """<b>Sᴇɴᴅɪɴɢ ......</b>"""

REPLY_ERROR = """Usᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴀs ᴀ ʀᴇᴘʟʏ ᴛᴏ ᴀɴʏ ᴛᴇʟᴇɢʀᴀᴍ ᴍᴇssᴀɢᴇ ᴡɪᴛʜᴏᴜᴛ ᴀɴʏ sᴘᴀᴄᴇs."""

#=====================================================================================#
@Client.on_message(filters.command("fileid") & filters.private)
async def ask_for_file_id(client: Client, message: Message):
    """Asks the user to send any media file and returns its file ID."""
    ask_msg = await message.reply_text("📩 Send any file (video, photo, document, audio, etc.) to get its File ID.")

    try:
        # Wait for any media message from the user
        response: Message = await client.listen(
            chat_id=message.chat.id,
            filters=filters.media,  # Accepts video, photo, document, etc.
            timeout=60  # Wait for 60 seconds
        )

        # Identify the file type and get its file_id
        file_id = None
        if response.photo:
            file_id = response.photo.file_id
            file_type = "🖼 Photo"
        elif response.video:
            file_id = response.video.file_id
            file_type = "🎥 Video"
        elif response.document:
            file_id = response.document.file_id
            file_type = "📄 Document"
        elif response.audio:
            file_id = response.audio.file_id
            file_type = "🎵 Audio"
        elif response.voice:
            file_id = response.voice.file_id
            file_type = "🎤 Voice Message"
        elif response.animation:
            file_id = response.animation.file_id
            file_type = "🎞 Animation (GIF)"
        elif response.sticker:
            file_id = response.sticker.file_id
            file_type = "🔖 Sticker"

        if file_id:
            await response.reply_text(f"{file_type} File ID:\n`{file_id}`")
        else:
            await ask_msg.edit_text("❌ Unsupported file type. Please try again.")

    except TimeoutError:
        await ask_msg.edit_text("⏳ You took too long! Please send the command again to get the File ID.")

@Bot.on_message((filters.command(['top', f'top@{Bot().username}']) & not_banned & (filters.private | filters.group)))
async def leaderboard(client: Client, message: Message):
    try:
        # Fetch top 10 users sorted by total points
        top_users = await user_data.find(
            {"$or": [{"referrals": {"$exists": True}}, {"purchased_points": {"$exists": True}}]}
        ).to_list(length=100)

        if not top_users:
            await message.reply_text("❌ No users found!", parse_mode=ParseMode.HTML)
            return

        # Sort by total points (referral + purchased)
        top_users = sorted(
            top_users,
            key=lambda user: user.get("referral_points", 0) + user.get("purchased_points", 0),
            reverse=True
        )[:10]  # Top 10 only

        # Medal Icons 🏆
        medals = ["🥇", "🥈", "🥉"] + ["🎖"] * 7  # First 3 get special medals

        leaderboard_text = (
            "<b>🏆 Lᴇᴀᴅᴇʀʙᴏᴀʀᴅ : Lᴇɢᴇɴᴅ𝘀 𝗢𝗳 Tʜᴇ Nᴇᴛ</b>\n"
            "🔺 <i>Tʜᴇ Tᴏᴘ 10 Eʟɪᴛᴇ Oᴘᴇʀᴀᴛɪᴠᴇs Dᴏᴍɪɴᴀᴛɪɴɢ Tʜᴇ Sʏsᴛᴇᴍ...</i> 🔥\n\n"
        )

        for i, user in enumerate(top_users, start=1):
            user_id = user["_id"]

            # Get referrals count
            referrals = user.get("referrals", 0)
            referral_count = len(referrals) if isinstance(referrals, list) else int(referrals)

            referral_points = user.get("referral_points", 0)
            purchased_points = user.get("purchased_points", 0)
            total_points = referral_points + purchased_points  # Total points

            # Fetch username or fallback to first_name
            first_name = user.get("first_name", "Phantom_404 🕶")
            try:
                user_info = await client.get_users(user_id)
                first_name = user_info.first_name or first_name
                username = f"@{user_info.username}" if user_info.username else first_name
            except Exception:
                username = first_name  # Fallback

            # Stylish Entry
            leaderboard_text += (
                f"{medals[i-1]} <b>{username}</b>  |  💸 <b>{total_points} Pᴏɪɴᴛs</b>\n"
                f"👁‍🗨 <b>Iɴғʟᴜᴇɴᴄᴇ:</b> <code>{referral_count}</code>\n\n"
                # "━━━━━━━━━━━━━━━\n"
            )

        # Call-to-Action Footer
        leaderboard_text += (
            "⚡ <b>Dᴏ Yᴏᴜ Dᴀʀᴇ Tᴏ Rᴜʟᴇ Tʜᴇ Bᴏᴀʀᴅ?</b>\n"
            "🕶️ Gᴀɪɴ Pᴏᴡᴇʀ Bʏ Rᴇғᴇʀʀɪɴɢ Aʟʟɪᴇs...\n"
            "👁‍🗨 Tʜᴇ Sʏsᴛᴇᴍ Wᴀᴛᴄʜᴇs. Bᴜᴛ Sᴏ Dᴏ Wᴇ.\n"
        )

        # Quick referral button
        referral_link = f"https://t.me/{client.username}?start=refer={message.from_user.id}"
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("👁‍🗨 Iɴᴠɪᴛᴇ Aɴ Aʟʟʏ", switch_inline_query=f"\n\n🔺 Eɴᴛᴇʀ Tʜᴇ Nᴇᴛᴡᴏʀᴋ ᴏғ {client.username} & ᴜɴʟᴏᴄᴋ ʀᴇᴡᴀʀᴅs..! 🎁\n\n🔗 Dᴀᴛᴀ Lɪɴᴋ:\n{referral_link}")],
            [InlineKeyboardButton("💠 Uᴘɢʀᴀᴅᴇ Yᴏᴜʀ Pᴏᴡᴇʀ", callback_data="buy_point")]
        ])

        await message.reply_text(leaderboard_text, parse_mode=ParseMode.HTML, reply_markup=buttons)

    except Exception as e:
        print(f"❌ Error in leaderboard command: {traceback.format_exc()}")
        await message.reply_text("⚠️ Aɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ ᴡʜɪʟᴇ ғᴇᴛᴄʜɪɴɢ ᴛʜᴇ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ.", parse_mode=ParseMode.HTML)

@Bot.on_message((filters.command(['convert', f'convert@{Bot().username}']) & not_banned & (filters.private | filters.group)))
async def gen_link_encoded(client: Bot, message: Message):
    try:
        await message.react(emoji=random.choice(REACTIONS), big=True)
    except:
        pass

    try:
        user_input = await client.ask(
            chat_id=message.from_user.id,
            text=(
                "🎮 <b>Iɴɪᴛɪᴀᴛɪɴɢ Lɪɴᴋ Eɴᴄʀʏᴘᴛɪᴏɴ</b>...\n\n"
                "🔐 Sᴇɴᴅ ʏᴏᴜʀ ᴄᴏᴅᴇ ᴏʀ ʟɪɴᴋ ᴛᴏ ᴄᴏɴᴠᴇʀᴛ:\n"
                "<code>abc123</code> or <code>https://t.me/bot?start=abc123</code>\n\n"
                "🛑 /cancel ᴛᴏ ᴇxɪᴛ."
            ),
            timeout=60,
            parse_mode=ParseMode.HTML
        )
    except asyncio.TimeoutError:
        return await message.reply("⌛ Tɪᴍᴇᴏᴜᴛ! Tʀʏ ᴀɢᴀɪɴ ᴡʜᴇɴ ʀᴇᴀᴅʏ.", parse_mode=ParseMode.HTML)
    except Exception as e:
        return await message.reply(f"⚠️ Eʀʀᴏʀ: <code>{e}</code>", parse_mode=ParseMode.HTML)

    if user_input.text.strip().lower() == "/cancel":
        return await user_input.reply("❌ Rᴜɴ ᴀʙᴏʀᴛᴇᴅ.", parse_mode=ParseMode.HTML)

    match = re.search(r'start=([^&]+)', user_input.text)
    hash_code = match.group(1) if match else user_input.text.strip()

    if not hash_code or " " in hash_code:
        return await user_input.reply("🚫 Iɴᴠᴀʟɪᴅ ᴄᴏᴅᴇ. Nᴏ sᴘᴀᴄᴇs, ɴᴏ ʙᴜɢs.", parse_mode=ParseMode.HTML)

    link = f"https://t.me/{client.username}?start={hash_code}"
    short_display = f"<code>{link[:35]}...</code>" if len(link) > 40 else f"<code>{link}</code>"

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Dᴇᴘʟᴏʏ Lɪɴᴋ", url=link)],
        [InlineKeyboardButton("🧬 Sʜᴀʀᴇ", switch_inline_query=f"✨ Cʜᴇᴄᴋ ᴛʜɪs ᴏᴜᴛ → {link}")]
    ])

    # 1. Send sticker
    step_msg = await user_input.reply_text("🔒 Iɴɪᴛɪᴀᴛɪɴɢ Eɴᴄʀʏᴘᴛɪᴏɴ...")
    await asyncio.sleep(0.5)
    try:
        await step_msg.edit("💥 Bᴀɴɢ Oɴ! Lɪɴᴋ Gᴇɴᴇʀᴀᴛᴇᴅ...")
    except:
        pass

    sticker_msg = await user_input.reply_sticker("CAACAgIAAxkBAAEBMrdn82oeQLUBqkmhoi2tprlBd5ESGAACHxEAApQgCUrPlMAXIC3dCTYE")

    # 2. Wait 2 seconds to simulate "processing"
    await asyncio.sleep(1.5)  # Simulate "processing"
    try:
        await sticker_msg.delete()
    except:
        pass

    # 3. Then drop the message with a hacker-cool reveal style
    await user_input.reply_text(
        text=(
            "✅ <b>Lɪɴᴋ Rᴇᴀᴅʏ</b> 💾\n\n"
            f"🔗 <b>Gᴇɴᴇʀᴀᴛᴇᴅ:</b> {short_display}\n"
            "🧠 <i>Dᴀᴛᴀ Sᴇᴇᴅᴇᴅ Iɴ ᴛʜᴇ Mᴀᴛʀɪx</i> 🧬\n\n"
            "🎯 <b>Uᴘʟᴏᴀᴅ Tʜᴇ Cᴏᴅᴇ Tᴏ ʏᴏᴜʀ ɴᴇᴛᴡᴏʀᴋ</b> 🌐"
        ),
        parse_mode=ParseMode.HTML,
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )



@Bot.on_message(filters.command('users') & filters.private & filters.user(ADMINS))
async def get_users(client: Bot, message: Message):
    try:
        await message.react(emoji=random.choice(REACTIONS), big=True)
    except:
        pass
    msg = await client.send_message(chat_id=message.chat.id, text=WAIT_MSG)

    users = await full_userbase()
    total_users = len(users)

    # Prepare user details
    user_details = []
    for user_id in users:
        try:
            user = await client.get_users(user_id)
            user_details.append({
                'id': user_id,
                'first_name': user.first_name,
                'username': user.username or "N/A"  # Handle cases where username might be None
            })
        except (UserIsBlocked, InputUserDeactivated, PeerIdInvalid):
            continue  # Skip users that cannot be retrieved
        except Exception as e:
            print(f"Error retrieving user {user_id}: {e}")
            continue

    # Pagination logic
    page_size = 50
    total_pages = (total_users + page_size - 1) // page_size  # Calculate total pages
    current_page = 1

    while current_page <= total_pages:
        start_index = (current_page - 1) * page_size
        end_index = min(start_index + page_size, total_users)
        
        # Prepare the message for the current page
        page_users = user_details[start_index:end_index]
        user_list = "\n".join([f"ID: <code>{user['id']}</code>, Name: {user['first_name']}, Username: @{user['username']}" for user in page_users])

        await msg.edit(
            f"Total users: {total_users} 👥\n\n"
            f"User Details (Page {current_page}/{total_pages}):\n{user_list if user_list else 'No users found.'}"
        )

        # Ask if the admin wants to see the next page
        if current_page < total_pages:
            await message.reply("Reply with 'next' to see the next page or 'done' to finish.")
            response = await client.listen(message.chat.id)

            if response.text.lower() == 'next':
                current_page += 1
            else:
                break
        else:
            break

    await msg.edit("Finished displaying user details.")

# @Bot.on_message(filters.private & filters.command('broadcast') & filters.user(ADMINS))
# async def send_text(client: Bot, message: Message):
#     if message.reply_to_message:
#         # Prompt user to choose broadcast type
#         await message.reply(
#             "Choose broadcast type:\n"
#             "0 - Broadcast to ALL users\n"
#             "1 - Broadcast to SPECIFIC users\n\n"
#             "Send the number (0 or 1)"
#         )
        
#         # Wait for user's choice
#         broadcast_type_msg = await client.listen(message.chat.id)
        
#         try:
#             broadcast_type = int(broadcast_type_msg.text)
            
#             # Validate input
#             if broadcast_type not in [0, 1]:
#                 await message.reply("Invalid input. Please send 0 or 1.")
#                 return
            
#             # Get broadcast message
#             broadcast_msg = message.reply_to_message
            
#             # Ask if the admin wants to edit the broadcast message
#             await message.reply("Would you like to edit the broadcast message? (yes/no)")
#             edit_response = await client.listen(message.chat.id)
#             if edit_response.text.lower() == 'yes':
#                 await message.reply("Please send the new broadcast message.")
#                 new_broadcast_msg = await client.listen(message.chat.id)
#                 broadcast_msg = new_broadcast_msg  # Update the broadcast message
            
#             # Determine user list
#             if broadcast_type == 0:
#                 query = await full_userbase()
#             else:
#                 # Prompt for specific user IDs
#                 await message.reply("Send user IDs separated by spaces or commas")
#                 user_ids_msg = await client.listen(message.chat.id)
                
#                 # Parse user IDs
#                 user_ids_str = user_ids_msg.text.replace(',', ' ')
#                 query = [int(uid.strip()) for uid in user_ids_str.split() if uid.strip().isdigit()]
            
#             # Perform broadcast
#             total = len(query)
#             successful = 0
#             blocked = 0
#             deleted = 0
#             unsuccessful = 0
            
#             pls_wait = await message.reply("<i>ʙʀᴏᴀᴅᴄᴀꜱᴛ ᴘʀᴏᴄᴇꜱꜜɪɴɢ....</i>")
            
#             for index, chat_id in enumerate(query):
#                 try:
#                     # Send message
#                     await broadcast_msg.copy(chat_id=chat_id)
#                     successful += 1
#                 except FloodWait as e:
#                     # Correctly use e.value instead of e.time
#                     await asyncio.sleep(e.value)  # Correct way to access the wait time
#                     try:
#                         await broadcast_msg.copy(chat_id=chat_id)
#                         successful += 1
#                     except Exception as inner_e:
#                         print(f"Failed to send message to {chat_id}: {inner_e}")  # Log the specific error
#                         unsuccessful += 1
#                 except UserIsBlocked:
#                     await del_user(chat_id)
#                     blocked += 1
#                 except InputUserDeactivated:
#                     await del_user(chat_id)
#                     deleted += 1
#                 except Exception as e:
#                     print(f"Unexpected error for {chat_id}: {e}")  # Log unexpected errors
#                     unsuccessful += 1
                
#                 # Update loading bar
#                 progress = (index + 1) / total
#                 bar_length = 20  # Length of the loading bar
#                 filled_length = int(bar_length * progress)
#                 bar = '█' * filled_length + '-' * (bar_length - filled_length)
#                 await pls_wait.edit(f"<b>Broadcast Progress:</b>\n{bar} {progress:.1%}")

#             # Generate status message
#             status = f"""<b><u>ʙʀᴏᴀᴅᴄᴀꜱᴛ ᴄᴏᴍᴘʟᴇᴛᴇᴅ</u>

# Total Users: <code>{total}</code>
# Successful: <code>{successful}</code>
# Blocked Users: <code>{blocked}</code>
# Deleted Accounts: <code>{deleted}</code>
# Unsuccessful: <code>{unsuccessful}</code></b>"""
            
#             await pls_wait.edit(status)
        
#         except ValueError:
#             await message.reply("Invalid input. Please send a number.")
    
#     else:
#         msg = await message.reply(REPLY_ERROR)
#         await asyncio.sleep(8)
#         await msg.delete()
    
#     return

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@Bot.on_message((filters.command(['auth', f'auth@{Bot().username}']) & not_banned & (filters.private | filters.group)))
async def auth_command(client: Bot, message: Message):
    try:
        await message.react(emoji=random.choice(REACTIONS), big=True)
    except:
        pass

    # Delete any rejected requests before proceeding
    await user_data.delete_many({'user_id': message.from_user.id, 'status': {'$in': ['pending', 'rejected']}})

    pending_request = await user_data.find_one({'user_id': message.from_user.id, 'status': 'pending'})
    if pending_request:
        return await message.reply_text(
            "You already have a pending authentication request. Please wait for it to be processed before sending another one.",
            quote=True
        )

    existing_user = await present_user(message.from_user.id)
    if existing_user:
        update_data = {'status': 'pending', 'timestamp': time.time()}
        await user_data.update_one({'user_id': message.from_user.id}, {'$set': update_data})
    else:
        auth_details = {
            '_id': message.from_user.id,
            'user_id': message.from_user.id,
            'username': message.from_user.username,
            'first_name': message.from_user.first_name,
            'last_name': message.from_user.last_name,
            'message': "",
            'timestamp': time.time(),
            'status': 'pending'
        }
        await user_data.insert_one(auth_details)

    # Asking the user for their reason
    user_message = await client.ask(
        text=(
            "🔹 <b>Wʜʏ Dᴏ Yᴏᴜ Wᴀɴᴛ Tᴏ Bᴇ Aɴ Aᴅᴍɪɴ?</b> 🔹\n\n"
            "👑 <i>Sʜᴏᴡ ᴜs ᴡʜʏ ʏᴏᴜ ᴅᴇsᴇʀᴠᴇ ᴛʜᴇ ᴄʀᴏᴡɴ!</i>\n\n"
            "📝 <b>Sᴜʙᴍɪᴛ ʏᴏᴜʀ ʀᴇᴀsᴏɴ ɪɴ 200 ᴄʜᴀʀs ᴏʀ ʟᴇss.</b>\n"
            "⚠️ <i>Oɴʟʏ sᴇʀɪᴏᴜs ʀᴇǫᴜᴇsᴛs ᴡɪʟʟ ʙᴇ ʀᴇᴠɪᴇᴡᴇᴅ.</i>"
        ),
        chat_id=message.from_user.id,
        timeout=60
    )

    if len(user_message.text) > 200:
        return await message.reply_text("Message too long. Please keep it under 200 characters. ✂️", quote=True)

    auth_details = {
        'user_id': message.from_user.id,
        'username': message.from_user.username,
        'first_name': message.from_user.first_name,
        'last_name': message.from_user.last_name,
        'message': user_message.text,
        'timestamp': time.time(),
        'status': 'pending'
    }
    await user_data.insert_one(auth_details)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Approve", callback_data=f"approve_{message.from_user.id}")],
        [InlineKeyboardButton("❌ Reject", callback_data=f"reject_{message.from_user.id}")]
    ])

    owner_msg = (
        f"🔐 <b>New Authentication Request</b> 🔐\n\n"
        f"👤 <b>User Details:</b>\n"
        f"ID: <code>{message.from_user.id}</code>\n"
        f"Username: @{message.from_user.username or 'N/A'}\n"
        f"Name: {message.from_user.first_name} {message.from_user.last_name or ''}\n\n"
        f"📝 <b>Message:</b> {user_message.text}\n\n"
        f"⏳ <b>Timestamp:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    )

    await client.send_message(
        chat_id=OWNER_ID,
        text=owner_msg,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )

    await message.reply_text("Your authentication request has been sent. You will be notified once it is processed. 📬")



@Bot.on_message(filters.command('allauth') & filters.private & filters.user(OWNER_ID))
async def all_auth_command(client: Bot, message: Message):
    pending_cursor = user_data.find({'status': 'pending'})
    pending_requests = [req async for req in pending_cursor]

    approved_cursor = user_data.find({'status': 'approved'})
    approved_requests = [req async for req in approved_cursor]

    if not pending_requests and not approved_requests:
        return await message.reply_text("🚫 <b>Nᴏ ᴘᴇɴᴅɪɴɢ ᴏʀ ᴀᴘᴘʀᴏᴠᴇᴅ ʀᴇǫᴜᴇsᴛs.</b>", parse_mode=ParseMode.HTML)

    text = "⚖️ <b>Wᴏʀᴛʜʏ ᴏʀ Nᴏᴛ?</b> ⚖️\n\n"
    keyboard_buttons = []

    text += "🕵️ <b>Pᴇɴᴅɪɴɢ Rᴇǫᴜᴇsᴛs:</b>\n"
    if pending_requests:
        for req in pending_requests:
            user_id = req.get("user_id", "N/A")
            first_name = req.get("first_name", "N/A")
            username = req.get("username", "N/A")
            auth_text = req.get("message", "N/A")[:50] + "..."
            text += f"🔹 <code>{user_id}</code> - @{username} ({first_name})\n📝 Message: {auth_text}\n\n"
            keyboard_buttons.append([
                InlineKeyboardButton(f"✅ Wᴏʀᴛʜʏ", callback_data=f"approve_{user_id}"),
                InlineKeyboardButton(f"❌ Nᴏᴛ Wᴏʀᴛʜʏ", callback_data=f"reject_{user_id}")
            ])
    else:
        text += "💨 Nᴏ ᴘᴇɴᴅɪɴɢ ʀᴇǫᴜᴇsᴛs.\n\n"

    text += "🏆 <b>Aᴘᴘʀᴏᴠᴇᴅ Aᴅᴍɪɴs:</b>\n"
    if approved_requests:
        for req in approved_requests:
            user_id = req.get("user_id", "N/A")
            first_name = req.get("first_name", "N/A")
            username = req.get("username", "N/A")
            text += f"🔹 <code>{user_id}</code> - @{username} ({first_name})\n\n"
            keyboard_buttons.append([
                InlineKeyboardButton(f"🗑 Rᴇᴍᴏᴠᴇ {user_id}", callback_data=f"delete_{user_id}")
            ])
    else:
        text += "❌ Nᴏ ᴀᴘᴘʀᴏᴠᴇᴅ ᴀᴅᴍɪɴs.\n\n"

    await message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard_buttons))



@Bot.on_message((filters.command(['help', f'help@{Bot().username}']) & not_banned & (filters.private | filters.group)))
async def help_command(client: Bot, message: Message):
    try:
        await message.react(emoji=random.choice(REACTIONS), big=True)
    except:
        pass

    help_pic = random.choice(START_PIC) if START_PIC else None
    fun_fact = random.choice(FUN_FACTS)
    uptime = get_uptime()

    help_text = f"""
<b>👁‍🗨 Wᴇʟᴄᴏᴍᴇ Tᴏ Tʜᴇ Mᴀᴛʀɪx, {message.from_user.mention} 👽</b>

🕸 <b><u>Hᴀᴄᴋᴇʀ Tᴏᴏʟs & Cᴏᴍᴍᴀɴᴅs:</u></b>
<blockquote>🔥 <b>/start</b> - Iɴɪᴛɪᴀᴛᴇ Pʀᴏᴛᴏᴄᴏʟ 🚀  
📡 <b>/ping</b> - Nᴇᴛᴡᴏʀᴋ Aɴᴀʟʏsɪs ⚡  
💰 <b>/points</b> - Cʀʏᴘᴛᴏ Bᴀʟᴀɴᴄᴇ 💎  
🎭 <b>/refer</b> - Rᴇᴄʀᴜɪᴛ Oᴘᴇʀᴀᴛɪᴠᴇs 💰  
🖥 <b>/convert</b> - Dᴀᴛᴀ Rᴇ-ᴄᴏɴꜰɪɢ 💻  
</blockquote>

🔑 <b><u>Pʀᴏᴛᴏᴄᴏʟ Aᴄᴄᴇss:</u></b>
<blockquote>✅ Uɴʟɪᴍɪᴛᴇᴅ Sᴇʀᴠᴇʀ Aᴄᴄᴇss  
🔰 Exᴄʟᴜsɪᴠᴇ Cʀʏᴘᴛᴏ Rᴇᴡᴀʀᴅs  
💀 Eɴᴛᴇʀ Tʜᴇ Dᴀʀᴋ Wᴇʙ...  
</blockquote>

⚠️ <b>Uᴘᴛɪᴍᴇ:</b> {str(uptime).split('.')[0]}  
🔮 <b>Dᴇᴇᴘ Wᴇʙ Iɴꜱɪɢʜᴛ:</b> <i>{fun_fact}</i>  

🕶 <b>Nᴇᴇᴅ Aɴ Aɢᴇɴᴛ?</b> Cᴏɴᴛᴀᴄᴛ @NyxKingX  
"""

    # 🔘 Inline keyboard with premium & fun buttons
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👑 Oᴡɴᴇʀ", url=f"tg://user?id={OWNER_ID}"),
            InlineKeyboardButton("👾 Dᴇᴠᴇʟᴏᴘᴇʀ", url="https://t.me/NyxKingX")
        ],
        [
            InlineKeyboardButton("🎰 Sᴘɪɴ & Wɪɴ", callback_data="spin_wheel"),
            InlineKeyboardButton("💎 Uᴘɢʀᴀᴅᴇ Pʀᴇᴍɪᴜᴍ", callback_data="buy_prem")
        ]
    ])

    sent_help = await message.reply_photo(
        photo=help_pic,
        caption=help_text,
        parse_mode=ParseMode.HTML,
        reply_markup=buttons
    )

    # 🗑 Auto-delete after 30s
    await asyncio.sleep(30)
    await sent_help.delete()
    await message.delete()


@Bot.on_message(filters.command('add_admin') & filters.private & filters.user(OWNER_ID))
async def command_add_admin(client: Bot, message: Message):
    while True:
        try:
            admin_id = await client.ask(text="Enter admin id 🔢\n /cancel to cancel : ",chat_id = message.from_user.id, timeout=60)
        except Exception as e:
            print(e)
            return
        if admin_id.text == "/cancel":
            await admin_id.reply("Cancelled 😉!")
            return
        try:
            await Bot.get_users(user_ids=admin_id.text, self=client)
            break
        except:
            await admin_id.reply("❌ Error 😖\n\nThe admin id is incorrect.", quote = True)
            continue
    if not await present_admin(admin_id.text):
        try:
            await add_admin(admin_id.text)
            await message.reply(f"Added admin <code>{admin_id.text}</code> 😼")
            try:
                await client.send_message(
                    chat_id=admin_id.text,
                    text=f"You are verified, ask the owner to add them to db channels. 😁"
                )
            except:
                await message.reply("Failed to send invite. Please ensure that they have started the bot. 🥲")
        except:
            await message.reply("Failed to add admin. 😔\nSome error occurred.")
    else:
        await message.reply("admin already exist. 💀")
    return


@Bot.on_message(filters.command('del_admin') & filters.private  & filters.user(OWNER_ID))
async def delete_admin_command(client: Bot, message: Message):
    while True:
        try:
            admin_id = await client.ask(text="Enter admin id 🔢\n /cancel to cancel : ",chat_id = message.from_user.id, timeout=60)
        except:
            return
        if admin_id.text == "/cancel":
            await admin_id.reply("Cancelled 😉!")
            return
        try:
            await Bot.get_users(user_ids=admin_id.text, self=client)
            break
        except:
            await admin_id.reply("❌ Error\n\nThe admin id is incorrect.", quote = True)
            continue
    if await present_admin(admin_id.text):
        try:
            await del_admin(admin_id.text)
            await message.reply(f"Admin <code>{admin_id.text}</code> removed successfully 😀")
        except Exception as e:
            print(e)
            await message.reply("Failed to remove admin. 😔\nSome error occurred.")
    else:
        await message.reply("admin doesn't exist. 💀")
    return

@Bot.on_message(filters.command('admins') & filters.private)
async def admin_list_command(client: Bot, message: Message):
    admin_list = await full_adminbase()  # Fetch admin list

    if not admin_list:
        return await message.reply("⚠️ Nᴏ ᴀᴅᴍɪɴs ᴀᴅᴅᴇᴅ ʏᴇᴛ!")

    formatted_list = "\n".join(str(admin) for admin in admin_list)  # Ensure proper formatting
    await message.reply(f"📃 <b>Fᴜʟʟ Aᴅᴍɪɴs Lɪsᴛ:</b>\n<code>{formatted_list}</code>", parse_mode=ParseMode.HTML)


@Bot.on_message(filters.command(['ping', f'ping@{Bot().username}']) & (filters.private | filters.group))
async def check_ping_command(client: Client, message: Message):
    start = time.time()
    ping_msg = await message.reply("🎮 Lᴏᴀᴅɪɴɢ Sʏsᴛᴇᴍ Sᴛᴀᴛs...")

    latency = (time.time() - start) * 1000
    mem = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=0.1)

    speed_status = (
        "⚡ Gᴏᴅ Mᴏᴅᴇ" if latency < 100 else
        "🚀 Gᴏᴏᴅ Sᴘᴇᴇᴅ" if latency < 300 else
        "🐢 Lᴀɢ Dᴇᴛᴇᴄᴛᴇᴅ"
    )

    await ping_msg.edit(
        f"🎯 <b>Gᴀᴍᴇʀ Pɪɴɢ Cʜᴇᴄᴋ</b> 🎮\n\n"
        f"📡 <b>Latency:</b> <code>{latency:.2f} ms</code> [{speed_status}]\n"
        f"🧠 <b>Memory:</b> <code>{mem.percent}%</code> "
        f"({mem.used / (1024**2):.1f} MB / {mem.total / (1024**2):.1f} MB)\n"
        f"🛠️ <b>CPU:</b> <code>{cpu}%</code> "
        f"({psutil.cpu_count(logical=True)} cores)\n"
        f"⏱️ <b>Uptime:</b> <code>{get_uptime()}</code>"
    )

    # await asyncio.sleep(5)
    # try:
    #     await message.delete()
    #     await ping_msg.delete()
    # except:
    #     pass


@Client.on_message(filters.private & filters.command('restart') & filters.user(ADMINS))
async def restart(client, message):
    # Log the restart attempt
    logging.info(f"Restart initiated by user {message.from_user.id}")

    try:
        # Send initial restart message
        restart_msg = await message.reply_text(
            text="♻️ <b>Iɴɪᴛɪᴀᴛɪɴɢ Rᴇsᴛᴀʀᴛ Pʀᴏᴄᴇss...</b>\n\n"
                 "• Saving current state\n"
                 "• Preparing to restart",
            quote=True
        )
        # Countdown with progressive messages
        restart_stages = [
            "🔧 Aᴜʀ Bʜᴀɪ Bʜᴀᴅɪʏᴀ...",
            "💻 Rᴇsᴛᴀʀᴛ Kᴀʀ Rᴀʜᴀ Hᴀɪ...",
            "🚀 Cʜᴀʟ Kᴀʀ Lᴇ...",
            "✅ Jᴀɪ Bᴀʙᴀ ᴋɪ..."
        ]

        for stage in restart_stages:
            await restart_msg.edit(stage)
            await asyncio.sleep(1)

        # Final restart message
        await restart_msg.edit(
            "<b>🌟 Sᴇʀᴠᴇʀ Rᴇsᴛᴀʀᴛ Sᴇǫᴜᴇɴᴄᴇ Cᴏᴍᴘʟᴇᴛᴇᴅ</b>\n"
            "Bᴏᴛ Wɪʟʟ Bᴇ Bᴀᴄᴋ Oɴʟɪɴᴇ Mᴏᴍᴇɴᴛᴀʀɪʟʏ. 🤖"
        )

        # Attempt to restart
        try:
            # Graceful shutdown of any ongoing processes can be added here
            os.execl(sys.executable, sys.executable, *sys.argv)
        except Exception as exec_error:
            # Log detailed error information
            logging.error(f"Restart execution failed: {exec_error}", exc_info=True)
            
            # Send error message to user
            await restart_msg.edit(
                f"❌ <b>Restart Failed</b>\n"
                f"Error: <code>{str(exec_error)}</code>\n\n"
                "Please check system logs for more details."
            )

    except Exception as overall_error:
        # Catch-all error handling
        logging.critical(f"Critical error during restart: {overall_error}", exc_info=True)
        
        await message.reply_text(
            f"🚨 <b>Cʀɪᴛɪᴄᴀʟ Rᴇsᴛᴀʀᴛ Eʀʀᴏʀ</b>\n"
            f"An unexpected error occurred: <code>{str(overall_error)}</code>",
            quote=True
        )

    return



@Bot.on_message(filters.command('stats') & filters.private & filters.user(ADMINS))
async def stats_command(client: Bot, message: Message):
    uptime = get_readable_time(time.time() - client.start_time)
    total_users = len(await full_userbase())
    premium_users = len(await get_premium_users())
    bot_version = __version__
    memory_usage = psutil.virtual_memory().percent
    cpu_usage = psutil.cpu_percent(interval=1)
    messages_processed = client.processed_messages  # Assuming you have a way to track this

    stats_text = BOT_STATS_TEXT.format(
        uptime=uptime,
        total_users=total_users,
        premium_users=premium_users,
        bot_version=bot_version,
        memory_usage=f"{memory_usage}%",
        cpu_usage=f"{cpu_usage}%",
        messages_processed=messages_processed
    )

    await message.reply_text(
        stats_text, 
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )
@Bot.on_message(filters.command("ban") & filters.private & filters.user(ADMINS))
async def ban_command(client: Bot, message: Message):
    try:
        # Ask the admin for the target user id.
        prompt_msg = await client.send_message(
            chat_id=message.from_user.id,
            text="Please enter the user id you wish to ban:"
        )
        reply_msg = await client.listen(message.from_user.id, timeout=60)
        await prompt_msg.delete()
        
        try:
            target_user_id = int(reply_msg.text.strip())
        except ValueError:
            err_msg = await message.reply_text("Invalid user id provided.", quote=True)
            await asyncio.sleep(3)
            await err_msg.delete()
            return
        
        # Mark the user as banned in the user_data collection.
        await user_data.update_one({'_id': target_user_id}, {'$set': {'banned': True}})
        
        # Optionally remove admin privileges if the banned user is in ADMINS.
        if target_user_id in ADMINS:
            await del_admin(target_user_id)
        
        try:
            await client.send_message(
                chat_id=target_user_id,
                text=f"🚫 You have been banned from using this bot. Contact @{OWNER_TAG} for more details.",
                disable_notification=False  # This ensures they get notified
            )
        except Exception as e:
            client.LOGGER(__name__).warning(f"Failed to notify banned user {target_user_id}: {e}")
        
        success_msg = await message.reply_text(f"User {target_user_id} has been banned from using the bot.", quote=True)
        await asyncio.sleep(3)
        await success_msg.delete()
        await reply_msg.delete()
        
    except asyncio.TimeoutError:
        timeout_msg = await message.reply_text("Operation timed out. Please try again.", quote=True)
        await asyncio.sleep(3)
        await timeout_msg.delete()
    except Exception as e:
        client.LOGGER(__name__).error(f"Error in ban command: {e}")
        err_msg = await message.reply_text("An error occurred while trying to ban the user.", quote=True)
        await asyncio.sleep(3)
        await err_msg.delete()        

@Bot.on_message(filters.command("unban") & filters.private & filters.user(ADMINS))
async def unban_command(client: Bot, message: Message):
    try:
        # Get all banned users from the database
        cursor = user_data.find({'banned': True})
        banned_users = await cursor.to_list(length=None)  # Convert cursor to a list

        if not banned_users:
            await message.reply_text("No banned users found.")
            return

        # Display list of banned users
        banned_list = "\n".join([f"User ID: {user['_id']}" for user in banned_users])
        await message.reply_text(
            f"<b>Here are the banned users:</b>\n\n{banned_list}\n\n"
            "Please send the User ID of the user you want to unban or send /cancel to exit.",
            parse_mode=ParseMode.HTML
        )

        try:
            # Wait for admin's response
            reply_msg = await client.listen(message.from_user.id, timeout=60)

            if not reply_msg:
                await message.reply_text("No response received. Operation timed out.")
                return

            if reply_msg.text.strip().lower() == "/cancel":
                await message.reply_text("Operation cancelled. 😁")
                return

            # Validate and parse the user ID
            try:
                target_user_id = int(reply_msg.text.strip())
            except ValueError:
                await message.reply_text("Invalid user ID format. Please send a valid User ID.")
                return

            # Remove banned flag by setting it to False
            result = await user_data.update_one({'_id': target_user_id}, {'$set': {'banned': False}})
            
            if result.modified_count > 0:
                await message.reply_text(f"User ID {target_user_id} has been successfully unbanned.")
            else:
                await message.reply_text("Failed to unban the user. User ID not found or already unbanned.")

        except asyncio.TimeoutError:
            await message.reply_text("Operation timed out. Please try again.")

    except Exception as e:
        client.LOGGER(__name__).error(f"Error in unban command: {e}")  # Remove `await`
        await message.reply_text("An error occurred while trying to unban the user.")

@Bot.on_message(filters.text & filters.regex("⚡ Points") | filters.command(['points', f'points@{Bot().username}']) & (filters.private | filters.group))
async def check_points(client: Client, message: Message):
    user_id = message.from_user.id

    try:
        await message.react(emoji=random.choice(REACTIONS), big=True)
    except:
        pass

    user_data = database.users  # ✅ Ensure this is a MongoDB collection
    # print(f"user_data type: {type(user_data)}")


    # Fetch user data from the database
    user = await user_data.find_one({'_id': user_id})
    if not user:
        await message.reply("🚫 You are not registered in the system. Please start earning points first!")
        return

    # Get the user's points data
    referral_points = user.get('referral_points', 0)
    purchased_points = user.get('purchased_points', 0)
    total_points = referral_points + purchased_points  # Calculate total points
    referral_link = f"https://t.me/{client.me.username}?start=refer={user_id}"
    await client.send_message(chat_id=message.chat.id, text="👻")

    # Points details message
    points_message = (f"""<b>
🕸️ Wᴇʟᴄᴏᴍᴇ Tᴏ Tʜᴇ Nᴇᴛᴡᴏʀᴋ

👁️ Yᴏᴜʀ Pᴏɪɴᴛs Dᴀᴛᴀ Hᴀs Bᴇᴇɴ Rᴇᴛʀɪᴇᴠᴇᴅ...

🔺 Rᴇғᴇʀʀᴀʟ Pᴏɪɴᴛs: <code>{referral_points}</code>
💰 Pᴜʀᴄʜᴀsᴇᴅ Pᴏɪɴᴛs: <code>{purchased_points}</code>
⚡ Tᴏᴛᴀʟ Pᴏɪɴᴛs: <code>{total_points}</code>

👨‍💻 Hᴏᴡ Tᴏ Hᴀᴄᴋ Mᴏʀᴇ Pᴏɪɴᴛs?  
1. /refer 🤖 - Rᴇᴄʀᴜɪᴛ Mᴏʀᴇ Aɢᴇɴᴛs  
2. Sᴘɪɴ Tʜᴇ Wʜᴇᴇʟ ⚡ - Tʀʏ Yᴏᴜʀ Lᴜᴄᴋ  
3. Bᴜʏ Pᴏɪɴᴛs 👾 - Cᴏɴᴛʀᴏʟ ᴛʜᴇ Sʏsᴛᴇᴍ  

🔻 Cʟɪᴄᴋ Tʜᴇ Bᴜᴛᴛᴏɴ Bᴇʟᴏᴡ Tᴏ Sᴘɪɴ Aɴᴅ Wɪɴ 🎰</b>
""")

    # Inline keyboard with "Spin Now" button
    keyboard = InlineKeyboardMarkup([ 
        [InlineKeyboardButton("💕 Rᴇғᴇʀ Aɴᴅ Eᴀʀɴ", url=f"https://t.me/share/url?url={referral_link}")],
        [InlineKeyboardButton("🎰 Sᴘɪɴ Nᴏᴡ", callback_data="spin_wheel")],
        [InlineKeyboardButton("💸 Tʀᴀɴsғᴇʀ Pᴏɪɴᴛs", callback_data="transfer")],
        [InlineKeyboardButton("💵 Bᴜʏ Pᴏɪɴᴛs", callback_data="buy_point"),
        InlineKeyboardButton("🐦‍🔥 Rᴇᴅᴅᴇᴍ",callback_data="redeem")]
    ])

    # Send message with inline button
    
    await message.reply(points_message, reply_markup=keyboard)


@Bot.on_message(filters.command("start", prefixes="/") & filters.group)
async def group_command(client: Client, message: Message):
    user_id = message.from_user.id
    bot_info = await client.get_me()
    bot_username = bot_info.username.lower() if bot_info.username else ""

    command_parts = message.text.strip().lower().split()
    is_bot_mentioned = command_parts[0] == f"/start@{bot_username}"
    if not is_bot_mentioned:
        return

    # Gamer-themed animated intro
    splash = await message.reply_text("⚔️ Iɴɪᴛɪᴀᴛɪɴɢ...")
    await asyncio.sleep(0.6)
    await splash.edit("🎮 Gᴀᴍᴇ Lᴏᴀᴅɪɴɢ...")
    await asyncio.sleep(0.6)
    await splash.edit("👑 OɴʟʏF@ɴs Aʟʙᴜᴍ Eɴᴛᴇʀᴇᴅ")
    await asyncio.sleep(0.5)
    await splash.edit("💀 Bʏ <b>NʏxKɪɴɢX</b> – Tʜᴇ Gʜᴏsᴛ Rᴜʟᴇs Hᴇʀᴇ")
    await asyncio.sleep(1)
    await splash.delete()

    # Cool gamer-style buttons
    buttons = [
        [
            InlineKeyboardButton("💸 Rᴇғᴇʀ & Eᴀʀɴ", callback_data=f"refer_{user_id}"),
            InlineKeyboardButton("📜 Aʙᴏᴜᴛ Bᴏᴛ", callback_data="about"),
            InlineKeyboardButton("🎟️ Rᴇᴅᴇᴇᴍ Cᴏᴅᴇ", callback_data="redeem")
        ],
        [
            InlineKeyboardButton("⚡ Bᴜʏ Pᴏɪɴᴛs", callback_data="buy_point"),
            InlineKeyboardButton("🎁 Fʀᴇᴇ Pᴏɪɴᴛs", callback_data="free_points"),
            InlineKeyboardButton("🎡 Sᴘɪɴ ᴛᴏ Wɪɴ", callback_data="spin_wheel")
        ],
        [
            InlineKeyboardButton("📊 Mʏ Pʟᴀɴ", callback_data="myplan"),
            InlineKeyboardButton("🆘 Nᴇᴇᴅ Hᴇʟᴘ?", callback_data="support")
        ],
        [
            InlineKeyboardButton("♾️ Uɴʟɪᴍɪᴛᴇᴅ Mᴏᴅᴇ", callback_data="generate_token")
        ],
        [
            InlineKeyboardButton("🖼️ Pɪᴄᴛᴜʀᴇs", callback_data="pic"),
            InlineKeyboardButton("📹 Vɪᴅᴇᴏs", callback_data="video")
        ]
    ]

    await message.reply_text(
        "<b>🎮 Wᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ Gᴀᴍᴇ Zᴏɴᴇ!</b>\n"
        "⚔️ Cᴏᴍᴍᴀɴᴅ Cᴇɴᴛᴇʀ Bʏ <b>NʏxKɪɴɢX</b> 👑\n\n"
        "Sᴇʟᴇᴄᴛ ʏᴏᴜʀ ᴘᴀᴛʜ, ᴄʜᴀᴍᴘɪᴏɴ. ⬇️",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# from datetime import datetime

from pyrogram.errors import UserNotParticipant
from pyrogram import enums

# Handle all chat join requests
@Bot.on_chat_join_request()
async def join_reqs(client, message: ChatJoinRequest):
    """Handle join requests for channels that require approval"""
    settings = await get_settings()
    REQUEST_SUB_CHANNELS = settings.get("REQUEST_SUB_CHANNELS", [])
    
    # Only process requests for our channels
    if message.chat.id not in REQUEST_SUB_CHANNELS:
        return
    
    user_id = message.from_user.id
    channel_id = message.chat.id
    
    # Store the join request in the database
    await store_join_request(user_id, channel_id)
    print(f"📝 Stored join request from user {user_id} for channel {channel_id}")

# Main bot handler to check user join status and allow them to proceed
@Bot.on_message(filters.command('start') & filters.private)
async def not_joined(client, message):
    settings = await get_settings()
    FORCE_SUB_CHANNELS = settings.get("FORCE_SUB_CHANNELS", [])
    REQUEST_SUB_CHANNELS = settings.get("REQUEST_SUB_CHANNELS", [])

    user_id = message.from_user.id

    # Skip checks for admins
    if user_id in ADMINS:
        return
    
    # Initialize variables to track which channels the user needs to join
    force_channels_to_join = []
    request_channels_to_join = []
    
    # Check force sub channels
    for channel in FORCE_SUB_CHANNELS:
        try:
            member = await client.get_chat_member(channel, user_id)
            if member.status not in [enums.ChatMemberStatus.OWNER, enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.MEMBER]:
                force_channels_to_join.append(channel)
        except UserNotParticipant:
            force_channels_to_join.append(channel)
        except Exception as e:
            print(f"Error checking force sub: {e}")
            force_channels_to_join.append(channel)
            
    # Check request channels
    for channel in REQUEST_SUB_CHANNELS:
        try:
            # Skip if user already has a pending request
            if await has_pending_request(user_id, channel):
                continue
                
            # Check if user is a member
            member = await client.get_chat_member(channel, user_id)
            if member.status not in [enums.ChatMemberStatus.OWNER, enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.MEMBER]:
                request_channels_to_join.append(channel)
        except UserNotParticipant:
            request_channels_to_join.append(channel)
        except Exception as e:
            print(f"Error checking request sub: {e}")
            request_channels_to_join.append(channel)
    
    # If user has joined all channels, proceed
    if not force_channels_to_join and not request_channels_to_join:
        return
        
    # User needs to join channels - prepare buttons
    force_text = (
        f"⚠️ Hᴇʏ, {message.from_user.mention} 🚀\n\n"
        "Yᴏᴜ ʜᴀᴠᴇɴ'ᴛ ᴊᴏɪɴᴇᴅ ᴄʜᴀɴɴᴇʟs ʏᴇᴛ. Pʟᴇᴀsᴇ ᴊᴏɪɴ ᴛʜᴇ ᴄʜᴀɴɴᴇʟs ʙᴇʟᴏᴡ, ᴛʜᴇɴ ᴛʀʏ ᴀɢᴀɪɴ.. !\n\n"
        "❗️Fᴀᴄɪɴɢ ᴘʀᴏʙʟᴇᴍs, ᴜsᴇ: /help"
    )

    buttons = []
    temp_buttons = []

    # Add FORCE-JOIN CHANNELS buttons
    for channel in force_channels_to_join:
        try:
            chat = await client.get_chat(channel)
            invite_link = await client.export_chat_invite_link(channel)
            btn = InlineKeyboardButton(f"👾 {chat.title}", url=invite_link)
            temp_buttons.append(btn)
            if len(temp_buttons) == 2:
                buttons.append(temp_buttons)
                temp_buttons = []
        except Exception as e:
            print(f"Error creating force join button for {channel}: {e}")
            continue

    # Add REQUEST-JOIN CHANNELS buttons
    for channel in request_channels_to_join:
        try:
            chat = await client.get_chat(channel)
            invite_link = await client.create_chat_invite_link(channel, creates_join_request=True)
            btn = InlineKeyboardButton(f"⚡ {chat.title} (Request)", url=invite_link.invite_link)
            temp_buttons.append(btn)
            if len(temp_buttons) == 2:
                buttons.append(temp_buttons)
                temp_buttons = []
        except Exception as e:
            print(f"Error creating request join button for {channel}: {e}")
            continue

    # Add leftovers
    if temp_buttons:
        buttons.append(temp_buttons)

    # Add Try Again button
    buttons.append([
        InlineKeyboardButton("♻️ ᴛʀʏ ᴀɢᴀɪɴ ♻️", url=f"https://t.me/{client.username}?start="),
        InlineKeyboardButton("❓ Aɴʏ Hᴇʟᴘ", url=SUPPORT_GROUP)
    ])

    # Send the message with buttons
    if buttons:
        try:
            await message.reply_photo(
                photo=FORCE_PIC,
                caption=force_text,
                reply_markup=InlineKeyboardMarkup(buttons),
                quote=True
            )
            print(f"✅ Sent force subscription message to user {user_id}")
        except Exception as e:
            print(f"❌ Error sending force subscription message: {e}")
            # Fallback to text message
            try:
                await message.reply(
                    force_text,
                    reply_markup=InlineKeyboardMarkup(buttons),
                    quote=True
                )
            except Exception as e:
                print(f"❌ Error sending fallback message: {e}")

    # Delete the original message
async def delete_all_conversations():
    """Delete all user support ticket requests from the conversations collection."""
    result = await conversation_collection.delete_many({})
    print(f"🗑️ Deleted {result.deleted_count} conversation(s).")

@Bot.on_message(filters.command("deleteall") & filters.private & filters.user(ADMINS))
async def delete_all_conversations_command(client: Bot, message: Message):
    await delete_all_conversations()
    await message.reply("🗑️ All conversations deleted successfully.")

@Bot.on_message(filters.command('resetall') & filters.private & filters.user(ADMINS))
async def reset_all_users(client: Bot, message: Message):
    result = await user_data.update_many(
        {},  # all users
        {'$set': {'free_trial_claimed': False}}
    )

    await message.reply_text(
        f"✅ Sᴜᴄᴄᴇssғᴜʟʟʏ ʀᴇsᴇᴛ {result.modified_count} ᴜsᴇʀs' ғʀᴇᴇ ᴛʀɪᴀʟ ᴄʟᴀɪᴍ.",
        quote=True
    )
    print(f"[ADMIN] Free trial reset for {result.modified_count} users by {message.from_user.id}")

@Bot.on_message(filters.command("transfer") & filters.private)
async def transfer_points(client: Client, message: Message):
    sender_id = message.from_user.id
    user_data = database.users
    transfer_logs = database.point_transfers

    # Step 1: Ask for Receiver ID
    ask_id = await message.reply(
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

    # Step 3: Confirm transfer
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


from pytz import timezone, utc

@Bot.on_message(filters.command("transferlogs") & filters.user(ADMINS))
async def view_transfer_logs(client: Client, message: Message):
    logs_collection = database.point_transfers
    users = database.users
    india_tz = timezone("Asia/Kolkata")

    logs = logs_collection.find().sort("timestamp", -1).limit(10)
    text = "<b>📜 Last 10 Point Transfers:</b>\n\n"

    async for log in logs:
        sender_id = log["sender_id"]
        receiver_id = log["receiver_id"]
        amount = log["amount"]

        # Fix timezone issue
        utc_time = utc.localize(log["timestamp"])
        local_time = utc_time.astimezone(india_tz)
        time_str = local_time.strftime("%d %b %Y • %I:%M %p")

        sender_user = await users.find_one({"_id": sender_id})
        receiver_user = await users.find_one({"_id": receiver_id})

        sender_name = sender_user.get("username") or sender_user.get("first_name", "Unknown")
        receiver_name = receiver_user.get("username") or receiver_user.get("first_name", "Unknown")

        text += (
            f"👑 <b>{amount} pts</b>\n"
            f"• From: <code>{sender_id}</code> ({sender_name})\n"
            f"• To: <code>{receiver_id}</code> ({receiver_name})\n"
            f"• 🕓 {time_str}\n\n"
        )

    await message.reply(text)


@Bot.on_message(filters.command("info") & filters.private)
async def user_info(client: Client, message: Message):
    user_id = message.from_user.id
    users = database.users

    user = await users.find_one({"_id": user_id})
    if not user:
        return await message.reply("🚫 Yᴏᴜʀ Dᴀᴛᴀ Wᴀꜱ Nᴏᴛ Fᴏᴜɴᴅ.")
    
    await message.reply_sticker("CAACAgIAAxkBAAEBMrdn82oeQLUBqkmhoi2tprlBd5ESGAACHxEAApQgCUrPlMAXIC3dCTYE")

    username = message.from_user.username or "None"
    first_name = message.from_user.first_name or "Unknown"
    last_name = message.from_user.last_name or ""
    full_name = f"{first_name} {last_name}".strip()

    referral_points = user.get("referral_points", 0)
    purchased_points = user.get("purchased_points", 0)
    total_points = referral_points + purchased_points
    referrals = user.get("referrals", [])

    premium = user.get("premium", False)
    premium_status = user.get("premium_status", "None")
    expiry = user.get("premium_expiry")
    expiry_str = "❌ Nᴏᴛ Aᴄᴛɪᴠᴇ"

    if premium and isinstance(expiry, (int, float)):
        # Check if expiry is a timestamp (either int or float)
        from datetime import datetime
        from pytz import timezone, utc

        # Convert expiry timestamp to a datetime object
        expiry_dt = datetime.utcfromtimestamp(expiry)
        india = timezone("Asia/Kolkata")
        expiry_dt = utc.localize(expiry_dt).astimezone(india)
        expiry_str = expiry_dt.strftime("%d %b %Y • %I:%M %p")

    elif premium and isinstance(expiry, datetime):
        # If expiry is already a datetime object
        from pytz import timezone, utc
        india = timezone("Asia/Kolkata")
        expiry_dt = expiry.astimezone(india)
        expiry_str = expiry_dt.strftime("%d %b %Y • %I:%M %p")
    
    # Fetching first names of referrals
    referral_list = "\n".join([f"➜ <a href='tg://user?id={ref}'>{ref_user.first_name} ({ref})</a>\n"
                            if ref_user.first_name else f"➜ Pʜᴀɴᴛᴏᴍ 404 {ref}\n" 
                           for ref in referrals for ref_user in [await client.get_users(ref)]]) if referrals else "Nᴏ Rᴇғᴇʀʀᴀʟ Yᴇᴛ Sᴛᴀʀᴛ Rᴇғᴇʀʀɪɴɢ...\n"

    # If no referrals, show "No Referrals Yet"
    referral_list = referral_list or "No Referrals Yet"

    text = (
        f"<b>👤 Uꜱᴇʀ Iɴғᴏ:</b>\n\n"
        f"🆔 <code>{user_id}</code>\n"
        f"🙍‍♂️ Nᴀᴍᴇ: {full_name}\n"
        f"🔗 Uꜱᴇʀɴᴀᴍᴇ: @{username}\n\n"
        f"💎 Tᴏᴛᴀʟ Pᴏɪɴᴛꜱ: <b>{total_points}</b>\n"
        f"├─ 🪙 Rᴇғᴇʀʀᴀʟ: {referral_points}\n"
        f"└─ 💰 Pᴜʀᴄʜᴀꜱᴇᴅ: {purchased_points}\n"
        f"👥 Rᴇғᴇʀʀᴀʟs:\n{referral_list}\n"
        f"🌟 Pʀᴇᴍɪᴜᴍ: {'✅ Aᴄᴛɪᴠᴇ' if premium else '❌ Nᴏ'}\n"
        f"📦 Pʟᴀɴ: {premium_status}\n"
        f"📅 Exᴘɪʀʏ: {expiry_str}\n\n"
        # f"🎯 Yᴏᴜ'ʀᴇ {total_points} Pᴏɪɴᴛs Aᴡᴀʏ Fʀᴏᴍ ᴇxᴄʟᴜsɪᴠᴇ Rᴇᴡᴀʀᴅs!"
    )

    await message.reply(text, parse_mode=ParseMode.HTML)

from pymongo import DESCENDING

@Client.on_message(filters.command("leaderboard") & filters.private)
async def top_referrals_leaderboard(client, message: Message):
    top_users = await database.users.find().sort("referrals", DESCENDING).limit(10).to_list(length=10)
    
    if not top_users:
        await message.reply("🥲 Nᴏ Rᴇғᴇʀʀᴀʟs Yᴇᴛ.")
        return

    # Define the medals
    medals = ["🥇", "🥈", "🥉"] + ["🎖"] * 7  # First 3 get special medals

    # Start the leaderboard text
    leaderboard_text = (
        "<b>🏆 Lᴇᴀᴅᴇʀʙᴏᴀʀᴅ : Lᴇɢᴇɴᴅ𝘀 𝗢𝗳 Tʜᴇ Nᴇᴛ</b>\n"
        "🔺 <i>Tʜᴇ Tᴏᴘ 10 Eʟɪᴛᴇ Oᴘᴇʀᴀᴛɪᴠᴇs Dᴏᴍɪɴᴀᴛɪɴɢ Tʜᴇ Sʏsᴛᴇᴍ...</i> 🔥\n\n"
        f"<b>💀 ᴇᴀᴄʜ ʀᴇғᴇʀʀᴀʟ ɢɪᴠᴇs {REFERRAL_REWARD} Pᴏɪɴᴛs ᴛᴏ Tʜᴇ Sᴇᴇᴋᴇʀ</b>\n"
        "🚀 <i>Wʜᴏ wɪʟʟ ᴄʟɪᴍʙ ᴛᴏ ᴛʜᴇ Tᴏᴘ? ✨</i>\n\n"
    )

    # Create an inline keyboard for the "Refer" button
    inline_buttons = []

    # Loop through the top users and assign medals
    for idx, user in enumerate(top_users, start=1):
        name = user.get("first_name", "Pʜᴀɴᴛᴏᴍ 404 💦")  # User's first name (or "Unknown")
        user_id = user.get("_id", "Pʜᴀɴᴛᴏᴍ 404")  # User's unique ID (user ID)
        
        # Check if referrals is a list. If not, treat it as 0
        referrals = user.get("referrals", [])
        if isinstance(referrals, list):
            referrals_count = len(referrals)  # Count the number of referrals in the list
        else:
            referrals_count = 0  # If it's not a list, treat as 0 referrals
        
        # Calculate referral points (25 points for each referral)
        referral_points = referrals_count * REFERRAL_REWARD

        # Assign medals to the top 3 users
        medal = medals[idx - 1]  # Get medal based on index (1st, 2nd, 3rd, etc.)

        # Create the "Refer" button with a dynamic referral link
        referral_link = f"https://t.me/{client.username}?start={user_id}"

        # Update the leaderboard text to include referral points
        leaderboard_text += f"<b>{medal} {name}</b> — {referrals_count} Rᴇғᴇʀs\n<b>     ├─ {referral_points} Eᴀʀɴᴇᴅ Pᴏɪɴᴛs</b>\n\n"

    # Add the inline keyboard to the message reply
    await message.reply(
        leaderboard_text,
        reply_markup=InlineKeyboardMarkup([ 
            [InlineKeyboardButton("👁‍🗨 Rᴇғᴇʀ Aɴ Aʟʟʏ", switch_inline_query=f"\n\n🔺 Eɴᴛᴇʀ Tʜᴇ Nᴇᴛᴡᴏʀᴋ ᴏғ {client.username} & ᴜɴʟᴏᴄᴋ ʀᴇᴡᴀʀᴅs..! 🎁\n\n🔗 Dᴀᴛᴀ Lɪɴᴋ:\n{referral_link}")],
        ])
    )
