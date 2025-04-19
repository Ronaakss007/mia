import sys
import asyncio
import traceback
from aiohttp import web
from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyromod import listen
from datetime import datetime
import time
from config import *
from plugins.admin import *
from database.database import *
from plugins import web_server
from pyrogram import utils


async def get_waiting_timer():
    """Retrieve the current waiting timer status from the database"""
    data = await admin_settings.find_one({"_id": "settings"})
    return data.get("waiting_timer", True) if data else True  # Default True

async def load_waiting_timer():
    global WAITING_TIMER
    WAITING_TIMER = await get_waiting_timer()

async def get_user_plan(user_id: int) -> str:
    user = await user_data.find_one({'_id': user_id})
    
    if not user:
        return "🆓 Fʀᴇᴇ Pʟᴀɴ"
        
    premium_expiry = user.get('premium_expiry', 0)
    
    if premium_expiry == 0:
        return "⭐️ Sᴛᴀʀᴛᴇʀ Pʟᴀɴ"
        
    remaining_time = premium_expiry - time.time()
    
    if remaining_time <= 0:
        return "⚠️ Pʟᴀɴ Exᴘɪʀᴇᴅ"
    
    # Get plan type based on remaining duration
    days_left = remaining_time / (24 * 3600)
    if days_left > 365:
        plan = "👑 Uʟᴛɪᴍᴀᴛᴇ"     
    elif days_left > 180:
        plan = "👑 Rᴏʏᴀʟ"
    elif days_left > 90:
        plan = "⭐️ Pʀᴇsᴛɪɢᴇ" 
    elif days_left > 30:
        plan = "💫 Eʟɪᴛᴇ"
    elif days_left > 7:
        plan = "🔥 Pʀᴏ"
    else:
        plan = "⚡️ Vɪᴘ"
        
    return plan

def get_peer_type_new(peer_id: int) -> str:
    peer_id_str = str(peer_id)
    if not peer_id_str.startswith("-"):
        return "user"
    elif peer_id_str.startswith("-100"):
        return "channel"
    else:
        return "chat"
utils.get_peer_type = get_peer_type_new

class Bot(Client):
    def __init__(self):
        super().__init__(
            name="Bot",
            api_hash=API_HASH,
            api_id=APP_ID,
            plugins={"root": "plugins"},
            workers=TG_BOT_WORKERS,
            bot_token=TG_BOT_TOKEN
        )
        self.LOGGER = LOGGER
        self.start_time = None
        self.processed_messages = 0
        self.invitelinks = []
        self.username = None

    async def broadcast_premium_highlights(self):
        settings = await get_settings()
        BROADCAST_GROUPS = settings.get("BROADCAST_GROUPS", [])
        while True:
            try:
                current_time = time.time()
                premium_users = await user_data.find(
                    {'premium': True, 'premium_expiry': {'$gt': current_time}}
                ).sort('premium_expiry', -1).limit(10).to_list(length=None)
                
                if premium_users:
                    text = """╭━━━━━━━━━━━━━━━━━━━━━╮  
      🌟 **Pʀᴇᴍɪᴜᴍ Sᴘᴏᴛʟɪɢʜᴛ** 🌟  
╰━━━━━━━━━━━━━━━━━━━━━╯  
🚀 **Tᴏᴅᴀʏ's Eʟɪᴛᴇ Mᴇᴍʙᴇʀs** 🚀"""

                    for index, user in enumerate(premium_users):
                        try:
                            user_info = await self.get_users(user['_id'])
                            user_plan = await get_user_plan(user['_id'])
                            medal = "🥇" if index == 0 else "🥈" if index == 1 else "🥉" if index == 2 else "⚡"
                            text += f"\n\n{medal} **{user_info.mention}**  |  🎟 **{user_plan}**"
                        except Exception as e:
                            print(f"Error getting user info: {e}")
                            continue

                    text += """  
━━━━━━━━━━━━━━━━━━━━━━  
✨ **Bᴇᴄᴏᴍᴇ Pʀᴇᴍɪᴜᴍ & Sᴇᴄᴜʀᴇ Yᴏᴜʀ Sᴘᴏᴛ!** ✨  
🚀 **Gᴇᴛ Exᴄʟᴜsɪᴠᴇ Aᴄᴄᴇss, Rᴇᴡᴀʀᴅs & Mᴏʀᴇ!** 🚀  
━━━━━━━━━━━━━━━━━━━━━━"""

                    for group_id in BROADCAST_GROUPS:
                        try:
                            await self.send_message(
                                group_id,
                                text,
                                reply_markup=InlineKeyboardMarkup([[
                                    InlineKeyboardButton("🎯  Jᴏɪɴ Pʀᴇᴍɪᴜᴍ", callback_data="buy_prem")
                                    ], [
                                        InlineKeyboardButton("💬 Support", callback_data="support")
                                    ]])
                            )
                            print(f"Broadcast sent to {group_id}")
                        except Exception as e:
                            print(f"Broadcast error for group {group_id}: {e}")
                await asyncio.sleep(1 * 24 * 60 * 60)  # Wait for 10 seconds
                
            except Exception as e:
                print(f"Premium broadcast error: {e}")
                await asyncio.sleep(300)

    async def start(self):
        settings = await get_settings() 
        FORCE_SUB_CHANNELS = settings["FORCE_SUB_CHANNELS"]
        FORCE_REQUEST_CHANNELS = settings.get("REQUEST_SUB_CHANNELS", [])
        await super().start()
        self.start_time = time.time()
        await load_waiting_timer()
        self.uptime = datetime.now()

        usr_bot_me = await self.get_me()
        self.username = usr_bot_me.username
        print(f"🚀 Bot Started as {self.username}")

        # Initialize invite links
        self.invitelinks = []  # Store the invite links for easy access
        for channel in FORCE_SUB_CHANNELS:
            try:
                chat = await self.get_chat(channel)
                invite_link = chat.invite_link
                if not invite_link:
                    invite_link = await self.export_chat_invite_link(channel)
                self.invitelinks.append(invite_link)
                print(f"✅ Got invite link for {channel}")
            except Exception as e:
                print(f"❌ Failed getting invite link for {channel}: {str(e)}")
                self.invitelinks.append(None)

        # Initialize invite links for FORCE_REQUEST_CHANNELS (Request-based channels)
        self.request_invitelinks = []  # Store invite links for request-based channels  
        for channel in FORCE_REQUEST_CHANNELS:
            try:
                chat = await self.get_chat(channel)
                invite_link = await self.create_chat_invite_link(
                    chat.id, 
                    creates_join_request=True
                
                )
                self.request_invitelinks.append(invite_link.invite_link)
                self.request_invitelinks.append(invite_link)
                print(f"✅ Got invite link for request-based channel {channel}")
            except Exception as e:
                print(f"❌ Failed getting invite link for request-based channel {channel}: {str(e)}")
                self.request_invitelinks.append(None)

        try:
            db_channel = await self.get_chat(CHANNEL_ID)
            self.db_channel = db_channel
            test = await self.send_message(chat_id=db_channel.id, text="✅ Bot Connected!")
            await test.delete()
        except Exception as e:
            print(f"❌ Bot is not admin in DB Channel: {traceback.format_exc()}")
            sys.exit()

        # Fetch and store bot admins
        initadmin = await full_adminbase()
        for x in initadmin:
            if x not in ADMINS:
                ADMINS.append(x)

        # Start premium broadcasts
        asyncio.create_task(self.broadcast_premium_highlights())

        # Notify bot owner
        await self.send_message(
            chat_id=OWNER_ID,
            text=f"<b><blockquote>🤖 Bᴏᴛ Rᴇsᴛᴀʀᴛᴇᴅ!</blockquote></b>\n\n"
                 f"☠️ <b>Dᴀᴛᴀʙᴀsᴇ Cʜᴀɴɴᴇʟ : </b> <a href='{self.db_channel.invite_link}'>{self.db_channel.title}</a>\n"
                 f"⚡ <code>{self.db_channel.id}</code>",
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )

        # Web Server Setup
        app = web.AppRunner(await web_server())
        await app.setup()
        bind_address = "0.0.0.0"
        await web.TCPSite(app, bind_address, PORT).start()

        print("🌐 Web server started!")

    async def stop(self, *args):
        await super().stop()
        print("🛑 Bot Stopped.")
