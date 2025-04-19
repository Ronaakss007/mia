from operator import add
import os
# from helper_func import get_premium_badge
import random
from datetime import datetime
from urllib.parse import quote_plus
import logging
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram import Client, filters
from logging.handlers import RotatingFileHandler
from urllib.parse import quote_plus


SUPPORT_GROUP = os.environ.get("SUPPORT_GROUP", "https://t.me/+-9VcfpQgLaFlYzE1")

# WAITING_TIMER = False  # Set to False to disable waiting timer
DUMB_CHAT = int(os.environ.get("DUMB_CHAT", "-1002667750079"))
# BROADCAST_GROUPS = [-1002421255405]
# Bot settingss
DEFAULT_WELCOME = ""
envelop_db_str = os.environ.get("ENVELOP_DB", "-1002396123709,-1002421255405,-1002314871293")
ENVELOP_DB = [int(chat_id.strip()) for chat_id in envelop_db_str.split(",")]
# your bot token from @BotFather
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "7441944817:AAEabmOW7aQsLZnzIn28EZJujCHHbEv7Wgk") 
#your api id from https://my.telegram.org/apps
APP_ID = int(os.environ.get("APP_ID", "27311593"))
#your api hash from https://my.telegram.org/apps
API_HASH = os.environ.get("API_HASH", "f6a7c2f795c4e168eeb2778f8c32b133")
#your channel_id from https://t.me/MissRose_bot by forwarding dummy message to rose and applying command `/id` in reply to that message
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1002301191765"))
#your id of telegram can be found by https://t.me/MissRose_bot with '/id' command
OWNER_ID = int(os.environ.get("OWNER_ID", "7663297585"))
#port set to default 8080
PORT = os.environ.get("PORT", "8000")
#your database url mongodb only You can use mongo atlas free cloud database
DB_URL = os.environ.get("DB_URL", "mongodb+srv://ronaksaini922:NbeuC9FX8baih72p@cluster0.z6bb3.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

DB_NAME = os.environ.get("DATABASE_NAME", "Cluster0")
DB_NAME = os.environ.get("DB_NAME", "Cluster0")
 
#for creating telegram thread for bot to improve performance of the bot
TG_BOT_WORKERS = int(os.environ.get("TG_BOT_WORKERS", "100"))
# Pictures for the bot
START_PIC = os.environ.get("START_PIC", "https://ibb.co/jZVkMBZT,https://ibb.co/jZVkMBZT").split(',')
FORCE_PIC = os.environ.get("FORCE_PIC", "https://ibb.co/jZVkMBZT")
PREMIUM_IMG = os.environ.get("PREMIUM_IMG", "https://ibb.co/jZVkMBZT")
TOKEN_VERIFIED = os.environ.get("TOKEN_VERIFIED", "https://ibb.co/jZVkMBZT")
INVALID_TOKEN = os.environ.get("INVALID_TOKEN", "https://ibb.co/KzByyK0d")
EXPIRED_TOKEN = os.environ.get("EXPIRED_TOKEN", "https://envs.sh/fzC.jpg")
ABOUT_PIC = os.environ.get("ABOUT_PIC", "https://ibb.co/ZpJdfDL6")
#your start default command message.
START_MSG = os.environ.get(
    "START_MESSAGE",
    "{hall_of_fame}\n"
)

#your telegram tag without @
OWNER_TAG = os.environ.get("OWNER_TAG", "NyxKingX")

# Referral System Toggle
REFER = True  # Set to False to disable referrals
BUY_POINT = True # Set to False to disable
REFERRAL_REWARD = 25  # ✅ Set referral reward points

PLAN_BENEFITS = {
    "🆓 Fʀᴇᴇ Pʟᴀɴ": {
        "free_media": 2,
        "speed": "🐌 Sʟᴏᴡ Mᴏᴅᴇ",
        "support": "❌ Nᴏ Pʀɪᴏʀɪᴛʏ",
        "access": "🔒 Rᴇsᴛʀɪᴄᴛᴇᴅ",
        "file_access": "🔑 Pᴏɪɴᴛs Nᴇᴇᴅᴇᴅ",
        "permanent_files": "🚫 Nᴏ",
        "saved_files": "🚫 Nᴏ",
    },
    "⭐️ Sᴛᴀʀᴛᴇʀ Pʟᴀɴ": {
        "free_media": 3,
        "speed": "⚡ Fᴀsᴛ Mᴏᴅᴇ",
        "support": "💬 Sᴛᴀɴᴅᴀʀᴅ Sᴜᴘᴘᴏʀᴛ",
        "access": "🔓 Pᴀʀᴛɪᴀʟ Uɴʟᴏᴄᴋ",
        "file_access": "🔑 Pᴏɪɴᴛs Nᴇᴇᴅᴇᴅ",
        "permanent_files": "❌ Nᴏ",
        "saved_files": "📦 Lɪᴍɪᴛᴇᴅ",
    },
    "⚡️ Vɪᴘ": {
        "free_media": 5,
        "speed": "🚀 Tᴜʀʙᴏ Bᴏᴏsᴛ",
        "support": "📞 Pʀɪᴏʀɪᴛʏ Sᴜᴘᴘᴏʀᴛ",
        "access": "🛠️ Exᴛᴇɴᴅᴇᴅ Fᴇᴀᴛᴜʀᴇs",
        "file_access": "🔑 Pᴏɪɴᴛs Nᴇᴇᴅᴇᴅ",
        "permanent_files": "❌ Nᴏ",
        "saved_files": "📦 Lɪᴍɪᴛᴇᴅ",
    },
    "🔥 Pʀᴏ": {
        "free_media": 7,
        "speed": "🦾 Aɪ Sᴘᴇᴇᴅ",
        "support": "🌍 24/7 Gʟᴏʙᴀʟ Sᴜᴘᴘᴏʀᴛ",
        "access": "✅ Aʟʟ Fᴇᴀᴛᴜʀᴇs Uɴʟᴏᴄᴋᴇᴅ",
        "file_access": "🔑 Pᴏɪɴᴛs Nᴇᴇᴅᴇᴅ",
        "permanent_files": "❌ Nᴏ",
        "saved_files": "📦 Lɪᴍɪᴛᴇᴅ",
    },
    "💫 Eʟɪᴛᴇ": {
        "free_media": 10,
        "speed": "⚡ Hʏᴘᴇʀ Bᴏᴏsᴛ",
        "support": "💎 Pʀᴇᴍɪᴜᴍ Hᴇʟᴘᴅᴇsᴋ",
        "access": "🔓 Eᴠᴇʀʏᴛʜɪɴɢ + Sᴇᴄʀᴇᴛ Pᴇʀᴋs",
        "file_access": "🔥 Fʀᴇᴇ & Pᴀɪᴅ Cᴏɴᴛᴇɴᴛ",
        "permanent_files": "✅ Yᴇs",
        "saved_files": "♾️ Uɴʟɪᴍɪᴛᴇᴅ",
        "exclusive_content": "✅ Yᴇs",
        "custom_support": "👨‍💻 Dᴇᴅɪᴄᴀᴛᴇᴅ Aɢᴇɴᴛ",
        "early_access": "🔜 Yᴇs",
    },
    "⭐️ Pʀᴇsᴛɪɢᴇ": {
        "free_media": 15,
        "speed": "🚀 Wᴀʀᴘ Sᴘᴇᴇᴅ",
        "support": "🤵 Pᴇʀsᴏɴᴀʟ Assɪsᴛᴀɴᴛ",
        "access": "🌍 Gʟᴏʙᴀʟ Vɪᴘ Fᴇᴀᴛᴜʀᴇs",
        "file_access": "🔥 Fʀᴇᴇ & Pᴀɪᴅ Cᴏɴᴛᴇɴᴛ",
        "permanent_files": "✅ Yᴇs",
        "saved_files": "♾️ Uɴʟɪᴍɪᴛᴇᴅ",
        "exclusive_content": "✅ Yᴇs",
        "custom_support": "💎 Vɪᴘ Hᴏᴛʟɪɴᴇ",
        "bonus_rewards": "🎁 Mᴏɴᴛʜʟʏ Pᴇʀᴋs",
    },
    "👑 Rᴏʏᴀʟ": {
        "free_media": 20,
        "speed": "🛸 Nᴇxᴛ-Gᴇɴ Sᴘᴇᴇᴅ",
        "support": "🕶️ Pᴇʀsᴏɴᴀʟ Mᴀɴᴀɢᴇʀ",
        "access": "🔥 Aʟʟ Sʏsᴛᴇᴍs Uɴʟᴏᴄᴋᴇᴅ",
        "file_access": "🔥 Fʀᴇᴇ & Pᴀɪᴅ Cᴏɴᴛᴇɴᴛ",
        "permanent_files": "✅ Yᴇs",
        "saved_files": "♾️ Uɴʟɪᴍɪᴛᴇᴅ",
        "exclusive_content": "✅ Yᴇs",
        "custom_support": "🎩 Dᴇᴅɪᴄᴀᴛᴇᴅ Eʟɪᴛᴇ Aɢᴇɴᴛ",
        "early_access": "🔜 Yᴇs",
        "priority_access": "🚀 Uʟᴛʀᴀ Pʀɪᴏʀɪᴛʏ",
    },
    "👑 Uʟᴛɪᴍᴀᴛᴇ": {
        "free_media": 50,
        "speed": "💥 Lɪɢʜᴛsᴘᴇᴇᴅ",
        "support": "🤖 Aɪ-Pᴏᴡᴇʀᴇᴅ Vɪᴘ",
        "access": "🌍 GᴏᴅMᴏᴅᴇ Aᴄᴛɪᴠᴀᴛᴇᴅ",
        "file_access": "🔥 Fʀᴇᴇ & Pᴀɪᴅ Cᴏɴᴛᴇɴᴛ",
        "permanent_files": "✅ Yᴇs",
        "saved_files": "♾️ Uɴʟɪᴍɪᴛᴇᴅ",
        "exclusive_content": "✅ Yᴇs",
        "custom_support": "👑 24/7 Vɪᴘ Cᴏɴᴄɪᴇʀɢᴇ",
        "early_access": "🔜 Yᴇs",
        "priority_access": "🚀 Hɪɢʜᴇsᴛ Pʀɪᴏʀɪᴛʏ",
        "custom_bonuses": "🎁 Sᴇᴄʀᴇᴛ Exᴄʟᴜsɪᴠᴇ Rᴇᴡᴀʀᴅs",
    },
}

PLAN_SUPPORT_TIMES = {
    "🆓 Fʀᴇᴇ Pʟᴀɴ": "⏳ 48-72 hours",        # Increased response time for Free plan
    "⭐️ Sᴛᴀʀᴛᴇʀ Pʟᴀɴ": "⏳ 24-48 hours",   # Increased response time for Starter plan
    "⚡️ Vɪᴘ": "⏳ 12-18 hours",               # VIP plan (increased)
    "🔥 Pʀᴏ": "⏳ 6-12 hours",                 # Pro plan (increased)
    "💫 Eʟɪᴛᴇ": "⏳ 4-6 hours",               # Elite plan (increased)
    "⭐️ Pʀᴇsᴛɪɢᴇ": "⏳ 2-4 hours",           # Prestige plan (increased)
    "👑 Rᴏʏᴀʟ": "⏳ 2-4 hours",               # Royal plan (increased)
    "👑 Uʟᴛɪᴍᴀᴛᴇ": "⏳ 1 hour",             # Ultimate plan remains same
}

FREE_MEDIA_LIMIT = {
    "🆓 Fʀᴇᴇ Pʟᴀɴ": 2,        # Free users
    "⭐️ Sᴛᴀʀᴛᴇʀ Pʟᴀɴ": 3,     # Starter users
    "⚡️ Vɪᴘ": 5,         # VIP users
    "🔥 Pʀᴏ": 7,         # Pro users
    "💫 Eʟɪᴛᴇ": 10,      # Elite users
    "⭐️ Pʀᴇsᴛɪɢᴇ": 15,   # Prestige users
    "👑 Rᴏʏᴀʟ": 20,      # Royal users
    "👑 Uʟᴛɪᴍᴀᴛᴇ": 50    # Ultimate users
}


POINTS_PER_PIC = 1  # Points deducted per video or picture
POINTS_PER_VIDEO = 1

# Spin WHeel
SPIN_WHEEL_COST = 5  # Cost of spinning the wheel
REWARDS = [0, 1, 5, 10, 50]
WEIGHTS = [80, 79, 50, 2, 1]  # The weights determine the likelihood of each reward
SPIN_WHEEL_REWARD1 = 1 # Reward for 1 spin
SPIN_WHEEL_REWARD2 = 5 # Reward for 2 spin
SPIN_WHEEL_REWARD3 = 10 # Reward for 3 spin
SPIN_WHEEL_REWARD4 = 50 # Reward for 4 spin
SPIN_WHEEL_REWARD5 = 0 # Reward for 5 spin

# Mega Spin configuration
MEGA_SPIN_COST = 50  # Higher cost for Mega Spin
MEGA_REWARDS = [0, 25, 50, 100, 200,500]  # Higher rewards for Mega Spin
MEGA_WEIGHTS = [90, 85, 80, 60, 2,1]  # Adjusted weights for Mega Spin

MIN_POINTS = 1   # Minimum free points
MAX_POINTS = 9  # Maximum free points
CUSTOM_CAPTION = """
👻 <b>{title}</b>
{premium_message}
"""
def get_caption_buttons():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🧿 Dᴀʀᴋ Hᴜʙ", url="https://t.me/jffmain"),
                InlineKeyboardButton("💀 NʏxKɪɴɢX 🔥", url="https://t.me/NyxKingX")
            ]
        ]
    )


PROTECT_CONTENT = True if os.environ.get("PROTECT_CONTENT", "TRUE") == "TRUE" else False
DISABLE_CHANNEL_BUTTON = True if os.environ.get("DISABLE_CHANNEL_BUTTON", "TRUE") == "TRUE" else False

ADMIN_LIST = os.environ.get("ADMINS", "").split()

ADMINS = [int(admin) for admin in ADMIN_LIST if admin.isdigit()]
ADMINS.append(OWNER_ID)


LOG_FILE_NAME = "NyxDesireX.txt"
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[
        RotatingFileHandler(
            LOG_FILE_NAME,
            maxBytes=50000000,
            backupCount=10
        ),
        logging.StreamHandler()
    ]
)

logging.getLogger("pyrogram").setLevel(logging.WARNING)
def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)


FUN_FACTS = [
    "🕶️ Dɪᴅ Yᴏᴜ Kɴᴏᴡ? Tʜᴇ Dᴀʀᴋ Wᴇʙ Oɴʟʏ Mᴀᴋᴇs ᴜᴘ 5% Oғ Tʜᴇ Dᴇᴇᴘ Wᴇʙ.",
    "💀 Hᴀᴄᴋᴇʀ Tʀɪᴠɪᴀ: 'Pᴀssᴡᴏʀᴅ' Wᴀs Tʜᴇ Mᴏsᴛ Cᴏᴍᴍᴏɴ Pᴀssᴡᴏʀᴅ ᴜsᴇᴅ ɪɴ 2023.",
    "🔺 Mᴀᴛʀɪx Mʏᴛʜ: Tʜᴇ Wᴏʀʟᴅ's Fɪʀsᴛ Cᴏᴍᴘᴜᴛᴇʀ Vɪʀᴜs Wᴀs Cʀᴇᴀᴛᴇᴅ ɪɴ 1986.",
    "⚡ Aɴ Oᴄᴛᴏᴘᴜs Hᴀs ᴛʜʀᴇᴇ Hᴇᴀʀᴛs—Oɴᴇ ᴏғ Tʜᴇᴍ Oɴʟʏ Wᴏʀᴋs ᴡʜᴇɴ Iᴛ Sᴡɪᴍs.",
    "🕶️ Tʜᴇ Fɪʀsᴛ Hᴀᴄᴋɪɴɢ Gʀᴏᴜᴘ, Tʜᴇ '414s', Wᴀs Cᴀᴜɢʜᴛ Iɴ 1983 Aғᴛᴇʀ Bʀᴇᴀᴋɪɴɢ Iɴᴛᴏ Nᴀsᴀ.",
    "💡 Bᴀɴᴀɴᴀs Aʀᴇ Bᴇʀʀɪᴇs, Bᴜᴛ Sᴛʀᴀᴡʙᴇʀʀɪᴇs Aʀᴇ Nᴏᴛ. Lɪғᴇ Is A Gʟɪᴛᴄʜ."
]


REACTIONS = ["🙅", "🤖", "☠️", "👾", "🥰", "🤩", "😱", "😈", "🎉", "⚡️", "😎", "🔥", "👻", "😁"]

BOT_STATS_TEXT = os.environ.get(
    "BOTS_STATS_TEXT",
    "<b>💻 Sʏsᴛᴇᴍ Oᴠᴇʀᴠɪᴇᴡ</b>\n"
    "☠️ <b>Uᴘᴛɪᴍᴇ:</b> {uptime}\n"
    "👥 <b>Uꜱᴇʀꜱ:</b> {total_users}  |  💎 <b>Pʀᴇᴍ:</b> {premium_users}\n"
    "⚙️ <b>Vᴇʀꜱɪᴏɴ:</b> 2.0\n"
    "🧠 <b>Rᴀᴍ:</b> {memory_usage}  |  🕸️ <b>CPU:</b> {cpu_usage}\n"
    "📡 <b>Ops Hᴀɴᴅʟᴇᴅ:</b> {messages_processed}\n\n"
    "<b>☣️ Nʏx Nᴇᴛ Hᴜʙ :</b> <a href=\"https://t.me/NyxKingX\">NʏxKɪɴɢ</a>"
)

USER_REPLY_TEXT = os.environ.get(
    "USER_REPLY_TEXT",
    "<b>🕸 Aᴄᴄᴇss Dᴇɴɪᴇᴅ</b>\n"
    "⚠️ Yᴏᴜ Lᴀᴄᴋ Aᴜᴛʜᴏʀɪᴢᴀᴛɪᴏɴ Tᴏ Mᴇssᴀɢᴇ Dɪʀᴇᴄᴛʟʏ.\n"
    "👾 <a href=\"t.me/NyxKingX\">Cᴏɴɴᴇᴄᴛ Vɪᴀ Aɢᴇɴᴛ NʏxKɪɴɢ</a>"
)



USER_REPLY_BUTTONS = [
    [
        InlineKeyboardButton("🕸️ Jᴏɪɴ Tʜᴇ Nᴇᴛ", url="https://t.me/jffmain"),
        InlineKeyboardButton("👤 Sᴜᴍᴍᴏɴ NʏxKɪɴɢ", url="https://t.me/NyxKingX")
    ]
]

DISABLE_WEB_PAGE_PREVIEW = True


SUCCESS_EFFECT_IDS = [
    "5104841245755180586",  # 🔥
    "5107584321108051014",  # 👍
    "5159385139981059251",  # ❤️
    "5046509860389126442",  # 🎉
]