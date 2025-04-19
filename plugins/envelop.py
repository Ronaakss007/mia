import asyncio
import os
import random
import sys
import time
import logging
from datetime import datetime, timedelta
import re
import string
from pyrogram.types import InputMediaVideo
import traceback
from pymongo import ASCENDING
import base64
from bson import ObjectId
import psutil
from pyrogram import Client, filters, __version__   
from pyrogram.enums import ParseMode
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery,ReplyKeyboardMarkup, KeyboardButton
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, PeerIdInvalid

from bot import Bot
from config import  *
from helper_func import *
from database.database import *
from pyrogram import Client, filters
from pyrogram.types import Message, ReplyKeyboardMarkup, ReplyKeyboardRemove
from config import  *
from pyrogram.enums import ChatType 

@Client.on_message(filters.command("envelop") & filters.user(ADMINS))
async def start_envelop(client: Client, message: Message):

    user_id = message.from_user.id
    effect_id = int(random.choice(SUCCESS_EFFECT_IDS))# Random effect
    current_time_ist = datetime.now(IST).strftime("%d-%m-%y %I:%M %p")

    async def ask(prompt: str) -> Message:
        return await client.listen(message.chat.id, timeout=60)

    try:
        await message.reply("📩 Enter the envelope name:")
        envelope_name = (await ask("Envelope Name")).text.strip()
        
        await message.reply("💰 Enter the total amount of points in this envelope:")
        total_points = int((await ask("Total Points")).text.strip())
        if total_points <= 0:
            raise ValueError("Total points must be greater than 0.")

        await message.reply("🎁 Enter the fixed claim amount per user:")
        claim_amount = int((await ask("Claim Amount")).text.strip())
        if claim_amount <= 0 or claim_amount > total_points:
            raise ValueError("Invalid claim amount.")
        
        await message.reply(f"⏳ Current Time: {current_time_ist}\nEnter expiry date & time (DD-MM-YY HH:MM IST, 24h format):")
        expiry_time_ist = datetime.strptime((await ask("Expiry Date & Time")).text.strip(), "%d-%m-%y %H:%M")
        expiry_time_ist = IST.localize(expiry_time_ist)
        expiry_time_utc = expiry_time_ist.astimezone(pytz.utc)
        
        if expiry_time_utc <= datetime.utcnow().replace(tzinfo=pytz.utc):
            raise ValueError("Expiry time must be in the future.")
        
        envelope = {
            "name": envelope_name,
            "total_points": total_points,
            "remaining_points": total_points,
            "fixed_claim": claim_amount,
            "expiry_time": expiry_time_utc,
            "claimed_users": {},
            "broadcast_message_id": [],
        }
        envelope_id = (await envelop_data.insert_one(envelope)).inserted_id
        claim_link = f"https://t.me/{client.me.username}?start=claim_{envelope_id}"
        
        claim_button = InlineKeyboardMarkup([[InlineKeyboardButton("👻 Cʟᴀɪᴍ Nᴏᴡ", url=claim_link)]])
        expiry_text = f"⏳ Expires On: {expiry_time_ist.strftime('%d-%m-%y %I:%M %p')} IST"
        envelop_message = (
            f"💀 <b>Sᴇᴄʀᴇᴛ Nᴏᴅᴇ Iɴɪᴛɪᴀᴛᴇᴅ...</b>\n"
            f"🕶️ <b>Hᴀᴄᴋᴇʀ Rᴇᴡᴀʀᴅ Dɪsᴘᴇɴsɪɴɢ...</b>\n"
            f"🕷️ <b>Eɴᴛᴇʀɪɴɢ {envelope_name} Lᴀʏᴇʀs...</b>\n\n"
            f"🔥 <b>Dᴇᴇᴘ Wᴇʙ Fᴜɴᴅs:</b> <code>{total_points}</code> Pᴏɪɴᴛs\n"
            f"🛡️ <b>Cʏʙᴇʀ Sʜɪᴇʟᴅ Aᴄᴛɪᴠᴇ:</b> {expiry_text}\n"
            f"💰 <b>Rᴇᴡᴀʀᴅ Pᴀʏᴏᴜᴛ:</b> <code>{claim_amount}</code> Pᴏɪɴᴛs\n\n"
            f"🔓 <b><a href='{claim_link}'>Aᴄᴄᴇss Sʜᴀᴅᴏᴡ Nᴇᴛ</a></b>"
        )
        await message.reply(envelop_message, reply_markup=claim_button,  message_effect_id=effect_id, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        
        await message.reply("📢 Send to channel? (Yes/No)")
        if (await ask("Broadcast Confirmation")).text.strip().lower() == "yes":
            await message.reply(f"⏳ Current Time: {current_time_ist}\nEnter broadcast time (DD-MM-YY HH:MM IST) or 'now':")
            response_text = (await ask("Broadcast Time")).text.strip().lower()

            if response_text == "now":
                for chat_id in ENVELOP_DB:
                    try:
                        channel_id = int(chat_id)
                        if str(channel_id).startswith('-100'):
                            channel_id = int(str(channel_id)[4:])
                        
                        chat_id_formatted = f"-100{channel_id}" if not str(chat_id).startswith('-100') else chat_id
                        
                        # print(f"📢 Sending to chat: {chat_id_formatted}")
                        # print(f"ENVELOP_DB list: {ENVELOP_DB}")

                        sent_msg = await client.send_message(
                            chat_id=chat_id_formatted,
                            text=envelop_message,
                            reply_markup=claim_button,
                            parse_mode=ParseMode.HTML,
                            disable_web_page_preview=True
                        )
                        print(f"Sent broadcast response: {sent_msg}")

                        await envelop_data.update_one(
                            {"_id": envelope_id},
                            {"$push": {"broadcast_message_id": sent_msg.id}}
                        )

                        delete_delay = (expiry_time_utc - datetime.utcnow().replace(tzinfo=pytz.utc)).total_seconds()
                        asyncio.create_task(delete_broadcast_message(client, chat_id_formatted, sent_msg.id, delete_delay))
                    except Exception as e:
                        print(f"Error sending to channel {chat_id}: {e}")
                        continue

                await message.reply(f"✅ Broadcast sent to {len(ENVELOP_DB)} channels. 🗑️ Messages will be deleted after {int(delete_delay / 60)} minutes.")
            
            else:
                try:
                    schedule_time_ist = IST.localize(datetime.strptime(response_text, "%d-%m-%y %H:%M"))
                    schedule_time_utc = schedule_time_ist.astimezone(pytz.utc)
                    delay_seconds = (schedule_time_utc - datetime.utcnow().replace(tzinfo=pytz.utc)).total_seconds()

                    if delay_seconds <= 0:
                        await message.reply("❌ The scheduled time must be in the future. Try again.")
                        return

                    await message.reply(f"⏳ Scheduled for {response_text} IST.")
                    await asyncio.sleep(delay_seconds)

                    for chat_id in ENVELOP_DB:
                        try:
                            channel_id = int(chat_id)
                            if str(channel_id).startswith('-100'):
                                channel_id = int(str(channel_id)[4:])
                            
                            chat_id_formatted = f"-100{channel_id}" if not str(chat_id).startswith('-100') else chat_id
                            
                            # print(f"📢 Sending to chat: {chat_id_formatted}")
                            sent_msg = await client.send_message(
                                chat_id=chat_id_formatted,
                                text=envelop_message,
                                reply_markup=claim_button,
                                parse_mode=ParseMode.HTML,
                                disable_web_page_preview=True
                            )
                            # print(f"✅ Sent message to {chat_id_formatted}: {sent_msg.id}")
                            
                            await envelop_data.update_one(
                                {"_id": envelope_id},
                                {"$push": {"broadcast_message_id": sent_msg.id}}
                            )

                            delete_delay = (expiry_time_utc - datetime.utcnow().replace(tzinfo=pytz.utc)).total_seconds()
                            asyncio.create_task(delete_broadcast_message(client, chat_id_formatted, sent_msg.id, delete_delay))
                        except Exception as e:
                            print(f"Error sending to channel {chat_id}: {e}")
                            continue

                    await message.reply(f"✅ Scheduled broadcast sent to {len(ENVELOP_DB)} channels. 🗑️ Messages will be deleted after {int(delete_delay / 60)} minutes.")

                except ValueError:
                    await message.reply("❌ Invalid date/time format. Please use DD-MM-YY HH:MM format.")
                except Exception as e:
                    await message.reply(f"❌ Unexpected error: {str(e)}")

    except ValueError as e:
        await message.reply(f"❌ {str(e)}")
    except Exception as e:
        await message.reply(f"❌ Unexpected error: {str(e)}")