import base64
import re
import asyncio
import time
import logging
import datetime
from pytz import timezone
from datetime import datetime, timedelta  
import string
from plugins.admin import *
from bot import Bot
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors import FloodWait
from shortzy import Shortzy
from database.database import *
from config import *

IST = timezone("Asia/Kolkata") 

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)  # Create a logger instance

# Define greeting based on the time of day
def get_greeting():
    current_hour = datetime.now().hour
    if current_hour < 12:
        return "🌞 Gᴏᴏᴅ Mᴏʀɴɪɴɢ"
    elif current_hour < 18:
        return "🌤️ Gᴏᴏᴅ Aғᴛᴇʀɴᴏᴏɴ"
    else:
        return "🌙 Gᴏᴏᴅ Eᴠᴇɴɪɴɢ"

# Randomized cool intro phrases
cool_phrases = [
    "🚀 Bᴇʏᴏɴᴅ Lɪᴍɪᴛꜱ, Bᴇʏᴏɴᴅ Iᴍᴀɢɪɴᴀᴛɪᴏɴ!",
    "⚡ Pᴏᴡᴇʀᴇᴅ Bʏ AI, Dᴇꜱɪɢɴᴇᴅ Fᴏʀ Pᴇʀꜰᴇᴄᴛɪᴏɴ.",
    "💡 I Dᴏɴ'ᴛ Jᴜꜱᴛ Rᴇᴘʟʏ— I Tʜɪɴᴋ.",
    "🤖 Wᴇʟᴄᴏᴍᴇ Tᴏ Tʜᴇ Fᴜᴛᴜʀᴇ ᴏғ Aᴜᴛᴏᴍᴀᴛɪᴏɴ!",
]

# Function to generate the dynamic start message
def get_start_msg(mention):
    greeting = get_greeting()  # Call get_greeting to get the current greeting
    random_phrase = random.choice(cool_phrases)

    return (
        f"<blockquote>{greeting}, {mention}! </blockquote>\n\n"
        f"<b>{random_phrase}</b>\n\n"
    )


async def get_premium_badge(user_id):
    user = await user_data.find_one({"_id": user_id})
    return "🌟OɴʟʏF@ɴs Aʟʙᴜᴍ Pʀᴇᴍɪᴜᴍ Usᴇʀ" if user and user.get("premium") else "👤 OɴʟʏF@ɴs Aʟʙᴜᴍ Rᴇɢᴜʟᴀʀ Usᴇʀ"
async def inc_count(hash: str):
    """Increment click count and update timestamps."""
    now = int(datetime.utcnow().timestamp())

    # Check if hash exists
    if not await present_hash(hash):
        print(f"Hash {hash} does not exist in the database. Creating new entry...")
        await gen_new_count(hash)  # Create a new entry if it doesn't exist

    result = await link_data.update_one(
        {'hash': hash},
        {
            '$inc': {'clicks': 1},
            '$set': {'last_click': now},
            '$setOnInsert': {'first_click': now}  # Sets first_click only if it's a new record
        },
        upsert=True
    )

    if result.modified_count > 0:
        print(f"✅ Successfully incremented click count for hash: {hash}")
    else:
        print(f"⚠️ No changes made while incrementing click count for hash: {hash}")


# Store the user's join request in the database
join_request_collection = database['join_requests']  # Define the join_requests collection
    
# Store the user's request in the database
async def store_join_request(user_id, channel_id):
    """Store a user's join request in the database"""
    try:
        await join_request_collection.update_one(
            {"user_id": user_id, "channel_id": channel_id},
            {"$set": {"timestamp": time.time()}},
            upsert=True
        )
        print(f"✅ Stored join request for user {user_id} in channel {channel_id}")
        return True
    except Exception as e:
        print(f"❌ Error storing join request: {e}")
        return False

async def has_pending_request(user_id, channel_id):
    """Check if a user has a pending join request for a channel"""
    try:
        request = await join_request_collection.find_one({"user_id": user_id, "channel_id": channel_id})
        result = request is not None
        print(f"🔍 Checking pending request for user {user_id} in channel {channel_id}: {result}")
        return result
    except Exception as e:
        print(f"❌ Error checking pending request: {e}")
        return False


# In your is_subscribed function:
async def is_subscribed(filter, client, update):
    """Check if user is subscribed to all FORCE_SUB_CHANNELS and REQUEST_SUB_CHANNELS."""
    settings = await get_settings()
    FORCE_SUB_CHANNELS = settings.get("FORCE_SUB_CHANNELS", [])
    REQUEST_SUB_CHANNELS = settings.get("REQUEST_SUB_CHANNELS", [])
    
    if not FORCE_SUB_CHANNELS and not REQUEST_SUB_CHANNELS:
        return True

    user_id = update.from_user.id
    if user_id in ADMINS:  # Allow admins without forcing them to join
        return True

    # Check regular force subscription channels
    for channel in FORCE_SUB_CHANNELS:
        try:
            member = await client.get_chat_member(channel, user_id)
            if member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]:
                continue  # User is subscribed to this channel, check next one
            else:
                return False  # Not subscribed
        except UserNotParticipant:
            return False  # User is not a participant
        except Exception as e:
            print(f"Error checking subscription: {e}")
            return False  # If any error occurs, assume not subscribed

    # Check request force subscription channels
    for channel in REQUEST_SUB_CHANNELS:
        try:
            # First check if user has a pending request
            if await has_pending_request(user_id, channel):
                continue  # User has a pending request, consider as subscribed
                
            # Then check if user is a member
            member = await client.get_chat_member(channel, user_id)
            if member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]:
                continue  # User is subscribed to this channel, check next one
            else:
                return False  # Not subscribed
        except UserNotParticipant:
            return False  # User is not a participant
        except Exception as e:
            print(f"Error checking request subscription: {e}")
            return False  # If any error occurs, assume not subscribed

    return True  # User is subscribed to all channels


async def is_subscribed2(filter, client, update):
    """Check if the user is subscribed to at least one channel from FORCE_SUB_CHANNELS."""
    settings = await get_settings()
    FORCE_SUB_CHANNELS = settings["FORCE_SUB_CHANNELS"]
    if not FORCE_SUB_CHANNELS:
        return True

    user_id = update.from_user.id
    if user_id in ADMINS:
        return True

    for channel in FORCE_SUB_CHANNELS:
        try:
            member = await client.get_chat_member(channel, user_id)
            if member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]:
                return True  # User is subscribed to at least one channel
        except Exception as e:
            print(f"Error checking subscription status for channel {channel}: {e}")

    return False  # User is not subscribed to any required channel


async def encode(string):
    if not isinstance(string, str):
        raise ValueError("Input must be a string")

    try:
        string_bytes = string.encode("ascii")
        base64_bytes = base64.urlsafe_b64encode(string_bytes)
        base64_string = (base64_bytes.decode("ascii")).strip("=")
        return base64_string
    except Exception as e:
        print(f"Error encoding string: {e}")
        return None

async def decode(base64_string):
    if not isinstance(base64_string, str):
        raise ValueError("Input must be a string")

    print(f"Base64 string: {base64_string}")  # Print the base64 string

    try:
        # Add padding to the base64 string
        base64_string = base64_string + "=" * (-len(base64_string) % 4)
        string_bytes = base64.urlsafe_b64decode(base64_string) 
        string = string_bytes.decode("ascii")
        return string
    except Exception as e:
        print(f"Error decoding base64 string: {e}")
        return None
# ✅ Function to Encode msg_id, channel_id, and required_points
async def encode_points(batch_data):
    """Encodes single or multiple msg_id, channel_id, and required_points into base64 keys."""
    try:
        if isinstance(batch_data, list):  # Handle batch of links
            encoded_keys = []
            for data in batch_data:
                msg_id, channel_id, required_points = data
                data_string = f"{msg_id}:{channel_id}:{required_points}"
                encoded_key = base64.urlsafe_b64encode(data_string.encode()).decode()
                encoded_keys.append(encoded_key)
                logger.debug(f"✅ Encoded Key for msg_id {msg_id}: {encoded_key}")
            return encoded_keys
        else:  # Handle single file
            msg_id, channel_id, required_points = batch_data
            data_string = f"{msg_id}:{channel_id}:{required_points}"
            encoded_key = base64.urlsafe_b64encode(data_string.encode()).decode()
            logger.debug(f"✅ Encoded Key for msg_id {msg_id}: {encoded_key}")
            return encoded_key
    except Exception as e:
        logger.error(f"❌ Error encoding file keys: {str(e)}")
        return None


# ✅ Function to Decode Access Key
async def decode_points(encoded_key):
    try:
        # URL-safe base64 decoding to handle special characters
        decoded_bytes = base64.urlsafe_b64decode(encoded_key)
        
        # Check if the decoding is successful and log the raw decoded bytes
        logger.debug(f"✅ Decoded Bytes: {decoded_bytes}")

        # Attempt to decode the bytes into a UTF-8 string, ignoring invalid characters
        decoded_string = decoded_bytes.decode('utf-8', errors='ignore')  # Ignores problematic characters
        
        logger.debug(f"✅ Decoded String: {decoded_string}")  # Debugging output

        # Split the decoded string by ":" to retrieve the msg_id, db_channel_id, and required_points
        decoded_parts = decoded_string.split(":")
        
        # Ensure the decoded string has the expected format
        if len(decoded_parts) != 3:
            logger.error(f"❌ Decoded key has an invalid format: {decoded_string}")
            return None
        
        return decoded_parts  # Returns [msg_id, db_channel_id, required_points]
    
    except Exception as e:
        logger.error(f"❌ Error decoding Base64: {e}")
        return None  # Return None instead of crashing
async def encode_batch_points(start_id, end_id, channel_id, required_points):
    """Encodes start_id, end_id, channel_id, and required_points into a short base64 string."""
    try:
        data_string = f"{start_id}:{end_id}:{channel_id}:{required_points}"
        encoded_key = base64.urlsafe_b64encode(data_string.encode()).decode().strip("=")
        logger.debug(f"✅ Encoded Batch Key: {encoded_key}")
        return encoded_key
    except Exception as e:
        logger.error(f"❌ Error encoding batch: {str(e)}")
        return None
async def decode_batch_points(encoded_key):
    try:
        missing_padding = len(encoded_key) % 4
        if missing_padding:
            encoded_key += '=' * (4 - missing_padding)
        decoded_bytes = base64.urlsafe_b64decode(encoded_key)
        decoded_str = decoded_bytes.decode('utf-8')

        # Split by ':' instead of ','
        parts = decoded_str.split(':')
        if len(parts) != 4:
            logger.error(f"❌ Unexpected decoded key format: {parts}")
            return None
        return parts  # Now returns 4 values
    except Exception as e:
        logger.error(f"❌ Error decoding Base64: {e}")
        return None


async def get_messages(client, message_ids):
    if not message_ids:  # Ensure message_ids is valid
        print("No message IDs provided.")
        return []

    messages = []
    total_messages = 0

    while total_messages < len(message_ids):
        batch_ids = message_ids[total_messages:total_messages + 200]  # Limit batch size

        try:
            # Validate message IDs
            batch_ids = [int(msg_id) for msg_id in batch_ids if isinstance(msg_id, int) and 0 < msg_id < 2**31]
            
            if not batch_ids:
                print("No valid message IDs found.")
                break

            fetched_messages = await client.get_messages(
                chat_id=client.db_channel.id,
                message_ids=batch_ids
            )

            messages.extend(fetched_messages)
            total_messages += len(batch_ids)  # Increment processed messages

        except FloodWait as e:
            print(f"FloodWait triggered, waiting {e.x} seconds.")
            await asyncio.sleep(e.x)

        except Exception as e:
            print(f"Error fetching messages: {e}")

    return messages

async def get_message_id(client, message):
    if message.forward_from_chat:
        if message.forward_from_chat.id == client.db_channel.id:
            return message.forward_from_message_id
        else:
            return 0
    elif message.forward_sender_name:
        return 0
    elif message.text:
        pattern = r"https://t.me/(?:c/)?(.*)/(\d+)"
        matches = re.match(pattern, message.text)
        if not matches:
            return 0
        channel_id = matches.group(1)
        msg_id = int(matches.group(2))
        if channel_id.isdigit():
            if f"-100{channel_id}" == str(client.db_channel.id):
                return msg_id
        else:
            if channel_id == client.db_channel.username:
                return msg_id
    else:
        return 0

def get_readable_time(seconds):
    periods = [
        ('year', 60 * 60 * 24 * 365),
        ('month', 60 * 60 * 24 * 30),
        ('day', 60 * 60 * 24),
        ('hour', 60 * 60),
        ('minute', 60),
        ('second', 1)
    ]

    result = []
    for period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            result.append(f"{int(period_value)} {period_name}{'s' if period_value > 1 else ''}")

    return ', '.join(result)

async def get_verify_status(user_id):
    verify = await db_verify_status(user_id)
    return verify

async def update_verify_status(user_id, verify_token="", is_verified=False, verified_time=0, link=""):
    current = await db_verify_status(user_id)
    current['verify_token'] = verify_token
    current['is_verified'] = is_verified
    current['verified_time'] = verified_time
    current['link'] = link
    await db_update_verify_status(user_id, current)

def generate_token():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

async def get_reward_token(api_urls, api_keys, long_url):
    index = random.choice([0, 1])  # 50-50 probability
    shortzy = Shortzy(api_key=api_keys[index], base_site=api_urls[index])  # Use function parameters
    return await shortzy.convert(long_url)  # Fix `link` to `long_url`

async def get_shortlink(api_urls, api_keys, long_url):
    """Get a short link for the provided long URL using the Shortzy service."""
    if len(api_urls) < 2 or len(api_keys) < 2:
        raise ValueError("Insufficient API URLs or keys provided.")

    index = random.choice([0, 1])  # 50-50 probability
    shortzy = Shortzy(api_key=api_keys[index], base_site=api_urls[index])  # Use function parameters
    return await shortzy.convert(long_url)


def get_exp_time(seconds):
    periods = [('days', 86400), ('hours', 3600), ('mins', 60), ('secs', 1)]
    result = ''
    for period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            result += f'{int(period_value)} {period_name}'
    return result

async def increasepremtime(user_id: int, timeforprem: int):
    if timeforprem == 0:
        realtime = 86400 * 1  # 1 day
        plan_status = "⚡ VIP"
    elif timeforprem == 1:
        realtime = 86400 * 7  # 7 days
        plan_status = "⚡ VIP"
    elif timeforprem == 2:
        realtime = 86400 * 30  # 1 month
        plan_status = "🔥 Pro"
    elif timeforprem == 3:
        realtime = 86400 * 90  # 3 months
        plan_status = "💫 Elite"
    elif timeforprem == 4:
        realtime = 86400 * 180  # 6 months
        plan_status = "⭐ Prestige"
    elif timeforprem == 5:
        realtime = 86400 * 365  # 1 year
        plan_status = "👑 Royal"
    else:
        realtime = 86400 * timeforprem  # Custom duration
        plan_status = "👑 Ultimate"  # You can define rules for custom plans later

    current_time = time.time()
    user = await user_data.find_one({'_id': user_id})
    
    if user and user.get('premium_expiry', 0) > current_time:
        expiry_time = user['premium_expiry'] + realtime
    else:
        expiry_time = current_time + realtime

    await update_verify_status(user_id, is_verified=True, verified_time=expiry_time)
    await user_data.update_one(
        {'_id': user_id},
        {'$set': {'premium': True, 'premium_expiry': expiry_time, 'premium_status': plan_status}}
    )

async def premiumreward(user_id: int, timeforprem: int):
    duration_mapping = [
        86400 * 1,    # 1 day
        86400 * 7,    # 7 days
        86400 * 30,   # 30 days (1 month)
        86400 * 90,   # 90 days (3 months)
        86400 * 180,  # 180 days (6 months)
        86400 * 365   # 365 days (1 year)
    ]
    
    premium_categories = {
        1: "⚡ VIP",         # 1 day - 7 days
        7: "⚡ VIP",
        30: "🔥 Pro",        # 7 - 30 days
        90: "💫 Elite",      # 30 - 90 days
        180: "⭐ Prestige",  # 90 - 180 days
        365: "👑 Royal",     # 180 - 365 days
        366: "👑 Ultimate"   # More than 365 days
    }

    # Ensure correct duration mapping
    realtime = duration_mapping[timeforprem] if timeforprem < len(duration_mapping) else 86400 * 1

    current_time = time.time()
    user = await user_data.find_one({'_id': user_id})

    if user and user.get('premium_expiry', 0) > current_time:
        expiry_time = user['premium_expiry'] + realtime
    else:
        expiry_time = current_time + realtime

    # Calculate total days for category assignment
    days_total = (expiry_time - current_time) // 86400
    premium_status = next((status for days, status in premium_categories.items() if days_total <= days), "⚡ VIP")

    # Update premium status
    await update_verify_status(user_id, is_verified=True, verified_time=expiry_time)
    await user_data.update_one({'_id': user_id}, {'$set': {
        'premium': True,
        'premium_expiry': expiry_time,
        'premium_status': premium_status  # Store user category
    }})

    print(f"Premium updated for {user_id}: {premium_status} until {expiry_time}")


async def autopayment(user_id: int, plan_days: int):
    current_time = int(time.time())
    user = await user_data.find_one({'_id': user_id})

    # Determine expiry
    if user and user.get('premium_expiry', 0) > current_time:
        expiry_time = user['premium_expiry'] + (plan_days * 86400)
    else:
        expiry_time = current_time + (plan_days * 86400)

    # Assign premium category
    days_total = (expiry_time - current_time) // 86400
    if days_total <= 7:
        premium_status = "⚡ VIP"
    elif days_total <= 30:
        premium_status = "🔥 Pro"
    elif days_total <= 90:
        premium_status = "💫 Elite"
    elif days_total <= 180:
        premium_status = "⭐ Prestige"
    elif days_total <= 365:
        premium_status = "👑 Royal"
    else:
        premium_status = "👑 Ultimate"

    # Update user status
    await update_verify_status(user_id, is_verified=True, verified_time=expiry_time)
    await user_data.update_one({'_id': user_id}, {
        '$set': {
            'premium': True,
            'premium_expiry': expiry_time,
            'premium_status': premium_status
        }
    })

    print(f"Premium updated for {user_id}: {premium_status} until {expiry_time}")

async def freetrial(user_id: int, timeforprem: int):
    # We only need the 10-minute duration for the free trial
    duration_mapping = [
        86400 * 1,    # 1 day, kept for structure, though not used here
    ]
    
    # Only the VIP category for the free trial
    premium_categories = {
        1: "⚡ VIP",  # 1 day (VIP), can be used for 10-minute free trial
    }

    # Set the duration to 10 minutes
    if timeforprem == 0:  # Special case for 10-minute free trial
        realtime = 10 * 60  # 10 minutes
    else:
        realtime = duration_mapping[timeforprem] if timeforprem < len(duration_mapping) else 86400 * 1

    current_time = time.time()
    user = await user_data.find_one({'_id': user_id})

    if user and user.get('premium_expiry', 0) > current_time:
        expiry_time = user['premium_expiry'] + realtime
    else:
        expiry_time = current_time + realtime

    # For the 10-minute trial, we always assign "⚡ VIP"
    premium_status = "⚡ VIP"

    # Update premium status and set free_trial_claimed to True
    await update_verify_status(user_id, is_verified=True, verified_time=expiry_time)
    
    await user_data.update_one(
        {'_id': user_id},
        {
            '$set': {
                'premium': True,
                'premium_expiry': expiry_time,
                'premium_status': premium_status,  # Always "⚡ VIP" for free trial
                'free_trial_claimed': True  # Mark the free trial as claimed
            }
        }
    )

    print(f"Premium updated for {user_id}: {premium_status} until {expiry_time}")


async def is_premium(user_id: int):
    user = await user_data.find_one({'_id': user_id})
    return user.get('premium', False)

async def get_premium_days_left(user_id: int):
    user = await user_data.find_one({'_id': user_id})
    if user and user.get('premium', False):
        premium_expiry = user.get('premium_expiry', 0)
        current_time = time.time()
        return max(0, (premium_expiry - current_time) / (24 * 3600))  # Convert seconds to days
    return 0  # Not premium

async def get_user_plan(user_id: int):
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
        
    return f"{plan} • {get_readable_time(remaining_time)}"


async def get_user_plan_group(user_id: int) -> str:
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

async def get_premium_showcase():
    current_time = int(time.time())

    premium_users = await database.users.find(
        {'premium': True, 'premium_expiry': {'$gt': current_time}}
    ).sort('premium_expiry', -1).limit(6).to_list(length=None)

    if not premium_users:  # Debugging step
        print("❌ No premium users found!")
        return []

    # print(f"Found {len(premium_users)} premium users:", premium_users)

    return premium_users  # Now it's a proper list

async def get_premium_showcase_no():
    current_time = int(time.time())

    premium_users = await database.users.find(
        {'premium': True, 'premium_expiry': {'$gt': current_time}}
    ).sort('premium_expiry', -1).limit(100).to_list(length=None)

    if not premium_users:  # Debugging step
        print("❌ No premium users found!")
        return []

    # print(f"Found {len(premium_users)} premium users:", premium_users)

    return premium_users  # Now it's a proper list

async def get_premium_users():
    current_time = time.time()
    premium_users = await user_data.find({'premium': True, 'premium_expiry': {'$gt': current_time}}).to_list(length=None)
    
    result = []
    for user in premium_users:
        user_id = user['_id']
        username = user.get('username', 'Unknown')
        remaining_seconds = int(user['premium_expiry'] - current_time)

        # Convert remaining time into a readable format
        remaining_time = get_readable_time(remaining_seconds)

        # Assign a premium category
        if remaining_seconds <= 7 * 86400:
            premium_status = "⚡ VIP"
        elif remaining_seconds <= 30 * 86400:
            premium_status = "🔥 Pro"
        elif remaining_seconds <= 90 * 86400:
            premium_status = "💫 Elite"
        elif remaining_seconds <= 180 * 86400:
            premium_status = "⭐ Prestige"
        elif remaining_seconds <= 365 * 86400:
            premium_status = "👑 Royal"
        else:
            premium_status = "👑 Ultimate"

        result.append((user_id, username, remaining_time, premium_status))

    return result


from pymongo import UpdateOne

async def check_premium_expiry(bot_instance):
    current_time = time.time()
    
    # Fetch expired users in one query
    expired_users = await user_data.find({'premium': True, 'premium_expiry': {'$lt': current_time}}).to_list(length=None)
    
    if not expired_users:
        print("DEBUG: No expired premium users found.")
        return

    bulk_updates = []
    
    for user in expired_users:
        user_id = user['_id']

        # Prepare bulk update to reset premium status
        bulk_updates.append(UpdateOne(
            {'_id': user_id},
            {'$set': {'premium': False, 'premium_expiry': 0, 'premium_status': "⚡ Free", 'free_trial_claimed': True}}  # Reset free trial claim
        ))

        # Update verification status
        await update_verify_status(user_id, is_verified=False, verified_time=0)

        # Notify the user about expiry
        try:
            await bot_instance.send_message(
                chat_id=user_id,
                text="🐦‍🔥 Yᴏᴜʀ Pʀᴇᴍɪᴜᴍ Pʟᴀɴ Hᴀs Exᴘɪʀᴇᴅ. \n\n"
                     "Bᴇɴᴇғɪᴛs Exᴘɪʀᴇᴅ:\n"
                     "🔸 Aᴅs Fʀᴇᴇ\n"
                     "🔸 Dɪʀᴇᴄᴛ Fɪʟᴇs\n"
                     "🔸 Uɴʟɪᴍɪᴛᴇᴅ Cᴏɴᴛᴇɴᴛs\n"
                     "🔸 Sᴀᴠᴇ Tᴏ Gᴀʟʟᴇʀʏ\n\n"
                     "Pʟᴇᴀsᴇ Rᴇɴᴇᴡ Yᴏᴜʀ Pʟᴀɴ Tᴏ Kᴇᴇᴘ Usɪɴɢ Bᴇɴᴇғɪᴛs.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Rᴇɴᴇᴡ Yᴏᴜʀ Pʟᴀɴ", callback_data="buy_prem")]
                ])
            )
        except Exception as e:
            print(f"Error notifying user {user_id}: {e}")

        # Notify the owner
        try:
            await bot_instance.send_message(
                chat_id=OWNER_ID,
                text=f"🔔 User {user_id}'s premium plan has expired. Premium benefits revoked."
            )
        except Exception as e:
            print(f"Error notifying owner: {e}")

    # Apply bulk update to MongoDB
    if bulk_updates:
        await user_data.bulk_write(bulk_updates)
        print(f"DEBUG: Updated {len(bulk_updates)} expired premium users.")


async def check_not_banned(_, __, message):
    # Look up the user in the database.
    user = await user_data.find_one({'_id': message.from_user.id})
    # If the user is banned, return False (block this message);
    # if not either no entry or banned is False, return True.
    return not (user and user.get("banned", False))

    
BOT_START_TIME = time.time()

# # Reactions based on ping
# def get_ping_rating(ping_ms):
#     if ping_ms < 100:
#         return "🚀 Super Fast"
#     elif ping_ms < 300:
#         return "⚡ Fast"
#     else:
#         return "🐢 Slow"

# Uptime calculation
def get_uptime():
    uptime_seconds = time.time() - BOT_START_TIME
    uptime_str = str(timedelta(seconds=int(uptime_seconds)))  # ✅ Now it works
    return uptime_str

async def get_file_details(msg):
    """Extract basic file details for any media type"""
    if msg.document:
        return {
            'file_id': msg.document.file_id,
            'file_name': msg.document.file_name,
            'file_size': msg.document.file_size,
            'file_type': 'Document'
        }
    elif msg.video:
        return {
            'file_id': msg.video.file_id,
            'file_name': msg.video.file_name or f"video_{msg.video.file_unique_id}.mp4",
            'file_size': msg.video.file_size,
            'file_type': 'Video'
        }
    elif msg.audio:
        return {
            'file_id': msg.audio.file_id,
            'file_name': msg.audio.file_name or f"audio_{msg.audio.file_unique_id}.mp3",
            'file_size': msg.audio.file_size,
            'file_type': 'Audio'
        }
    elif msg.photo:
        photo = msg.photo[-1]
        return {
            'file_id': photo.file_id,
            'file_name': f"photo_{photo.file_unique_id}.jpg",
            'file_size': photo.file_size,
            'file_type': 'Photo'
        }
    return None

def convert_size(size_bytes):
    """Convert bytes to human readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    for unit in ['KB', 'MB', 'GB']:
        size_bytes /= 1024
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"

from pyrogram.errors import UserNotParticipant

async def not_joined_giveaway(client, message):
    """Force users to join required channels before entering the giveaway."""

    settings = await get_settings()
    FORCE_SUB_CHANNELS = settings["FORCE_SUB_CHANNELS"]

    buttons = []
    force_text = (
        "🚀 <b>Yᴏᴜ Nᴇᴇᴅ Tᴏ Jᴏɪɴ Oᴜʀ Cʜᴀɴɴᴇʟ & Gʀᴏᴜᴘ Tᴏ Pᴀʀᴛɪᴄɪᴘᴀᴛᴇ Iɴ Tʜᴇ Gɪᴠᴇᴀᴡᴀʏ!\n\n"
        "🔹 Jᴏɪɴ Aʟʟ Bᴇʟᴏᴡ Cʜᴀɴɴᴇʟs Aɴᴅ Cʟɪᴄᴋ 'Cᴏɴᴛɪɴᴜᴇ' !\n"
        "📌 Nᴇᴇᴅ Aɴʏ Hᴇʟᴘ ? /help 🫡</b>\n\n"
    )

    temp_buttons = []
    user_id = message.from_user.id
    not_joined_channels = []  # List to store channels the user hasn't joined

    for i, channel in enumerate(FORCE_SUB_CHANNELS):
        try:
            chat = await client.get_chat(channel)
            member = await client.get_chat_member(channel, user_id)

            # Check if user is a valid member
            if member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                continue  # Skip this channel since user has already joined

        except UserNotParticipant:
            # User is NOT in the channel, generate an invite button
            try:
                invite_link = await client.export_chat_invite_link(channel)
            except Exception as e:
                print(f"⚠️ Error generating invite link for {channel}: {e}")
                invite_link = f"https://t.me/{chat.username}" if chat.username else f"https://t.me/joinchat/{chat.invite_link}"

            temp_buttons.append(InlineKeyboardButton(f"👾 {chat.title}", url=invite_link))
            not_joined_channels.append(channel)

            if len(temp_buttons) == 2:
                buttons.append(temp_buttons)
                temp_buttons = []

        except Exception as e:
            print(f"⚠️ Error checking subscription status for {channel}: {e}")
            continue  # Skip this channel if there's an error

    # Add remaining buttons
    if temp_buttons:
        buttons.append(temp_buttons)

    command_param = message.command[1] if message.command and len(message.command) > 1 else ""

    if not not_joined_channels:
        return False  # User has joined all required channels, continue giveaway

    # Show "Continue" button only after joining all channels
    buttons.append([
        InlineKeyboardButton("✅ Cᴏɴᴛɪɴᴜᴇ", url=f"https://t.me/{client.username}?start={command_param}"),
        InlineKeyboardButton("❓ Aɴʏ Hᴇʟᴘ", url=SUPPORT_GROUP)
    ])

    await message.reply_photo(
        photo=FORCE_PIC,  # Use image from config.py
        caption=force_text,
        reply_markup=InlineKeyboardMarkup(buttons),
        quote=True
    )

    return True  # User has NOT joined all channels


 # Ensure IST timezone consistency

GIVEAWAY_DB = "giveaway_users"
PRIZES = [500, 200, 200, 100, 100, 100, 50, 50, 50, 25, 25, 25, 25]  # Balanced prize distribution
WINNER_ANNOUNCEMENT_TIME = "2025-03-22 09:00:00"
ENTRY_DEADLINE = "2025-03-21 22:58:00"  # Users can't enter after this time
WINNERS_CHANNEL_ID = -1002396123709

@Bot.on_message(filters.text & filters.regex("🎁 Join Giveaway"))
async def join_giveaway(client, message):
    now = datetime.now(IST)
    deadline_time = IST.localize(datetime.strptime(ENTRY_DEADLINE, "%Y-%m-%d %H:%M:%S"))
    winner_time = IST.localize(datetime.strptime(WINNER_ANNOUNCEMENT_TIME, "%Y-%m-%d %H:%M:%S"))    

    if now >= winner_time:
        await message.reply("❌ Tʜᴇ Gɪᴠᴇᴀᴡᴀʏ Iꜱ Oᴠᴇʀ! Tʜᴇ Wɪɴɴᴇʀs Hᴀᴠᴇ Aʟʀᴇᴀᴅʏ Bᴇᴇɴ Aɴɴᴏᴜɴᴄᴇᴅ.")
        return
    
    if now >= deadline_time:
        await message.reply("❌ Tʜᴇ Gɪᴠᴇᴀᴡᴀʏ Eɴᴛʀʏ Hᴀs Cʟᴏsᴇᴅ! Yᴏᴜ Cᴀɴɴᴏᴛ Jᴏɪɴ Nᴏᴡ.")
        return

    user_id = message.from_user.id
    user = await user_data.find_one({"_id": user_id})

    if not user:
        await message.reply("❌ Yᴏᴜ ᴀʀᴇ ɴᴏᴛ ʀᴇɢɪsᴛᴇʀᴇᴅ ɪɴ ᴛʜᴇ ʙᴏᴛ. Pʟᴇᴀsᴇ sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ ғɪʀsᴛ!")
        return

    if await not_joined_giveaway(client, message):  
        return  

    existing_entry = await database[GIVEAWAY_DB].find_one({"_id": user_id})

    if existing_entry:
        await message.reply("✅ Yᴏᴜ Aʀᴇ Aʟʀᴇᴀᴅʏ Jᴏɪɴᴇᴅ Tʜᴇ Gɪᴠᴇᴀᴡᴀʏ!")
    else:
        username = message.from_user.first_name or "Unknown"
        await database[GIVEAWAY_DB].insert_one({"_id": user_id, "username": username})
        total_members = await database[GIVEAWAY_DB].count_documents({})

        await client.send_message(
            OWNER_ID,
            f"🚨 <b>Nᴇᴡ Gɪᴠᴇᴀᴡᴀʏ Eɴᴛʀʏ</b> 🚨\n\n"
            f"👤 <b>User:</b> {message.from_user.mention}\n"
            f"🆔 <b>User ID:</b> <code>{user_id}</code>\n"
            f"📊 <b>Total Participants:</b> {total_members}"
        )
        
        await message.reply(
            "🎉 Yᴏᴜ Hᴀᴠᴇ Sᴜᴄᴄᴇssғᴜʟʟʏ Eɴᴛᴇʀᴇᴅ Tʜᴇ Gɪᴠᴇᴀᴡᴀʏ!\n\n"
            "🎁 Pʀɪᴢᴇs:\n"
            "🥇 500 Pᴏɪɴᴛs (1 Winner - Rare)\n"
            "🥈 200 Pᴏɪɴᴛs (2 Winners)\n"
            "🥉 100 Pᴏɪɴᴛs (3 Winners)\n"
            "🎊 50 Pᴏɪɴᴛs (3 Winners)\n"
            "🎁 25 Pᴏɪɴᴛs (4 Winners)\n\n"
            f"📅 Eɴᴛʀʏ Cʟᴏsᴇs Oɴ {ENTRY_DEADLINE}!\n"
            f"🏆 Wɪɴɴᴇʀs Aɴɴᴏᴜɴᴄᴇᴍᴇɴᴛ Oɴ {WINNER_ANNOUNCEMENT_TIME}!"
        )


async def pick_giveaway_winners(client):
    now = datetime.now(IST)
    winner_time = IST.localize(datetime.strptime(WINNER_ANNOUNCEMENT_TIME, "%Y-%m-%d %H:%M:%S"))
    
    if now < winner_time:
        return  # Not time yet

    all_entries = await database[GIVEAWAY_DB].find().to_list(length=1000)  
    if not all_entries:
        return  

    num_winners = min(len(all_entries), len(PRIZES))
    random.shuffle(all_entries)
    winners = all_entries[:num_winners]  

    results_text = "🏆 Gɪᴠᴇᴀᴡᴀʏ Wɪɴɴᴇʀs Aʀᴇ Hᴇʀᴇ! 🎉\n\n"

    for i, winner in enumerate(winners):
        user_id = winner["_id"]
        username = winner.get("username", "Unknown")  
        user_mention = f"[{username}](tg://user?id={user_id})"
        prize = PRIZES[i]
        results_text += f"🎖 {user_mention} - {prize} Pᴏɪɴᴛs\n"
        
        await user_data.update_one({"_id": user_id}, {"$inc": {"purchased_points": prize}})

        try:
            await client.send_message(
                user_id,
                f"🎉 Cᴏɴɢʀᴀᴛᴜʟᴀᴛɪᴏɴs {username}! 🎊\n\n"
                f"🎁 Yᴏᴜ Hᴀᴠᴇ Wᴏɴ {prize} Pᴏɪɴᴛs Iɴ Tʜᴇ Gɪᴠᴇᴀᴡᴀʏ! 🎉\n"
                "🏆 Tʜᴀɴᴋ Yᴏᴜ Fᴏʀ Pᴀʀᴛɪᴄɪᴘᴀᴛɪɴɢ!"
            )
        except Exception as e:
            print(f"❌ Failed to send message to {user_id}: {e}")

    await client.send_message(WINNERS_CHANNEL_ID, results_text)
    
    # Clear giveaway database after announcing winners
    await database[GIVEAWAY_DB].delete_many({})
        

async def get_multiple_user_plans(user_ids):
    users = await database.users.find({"_id": {"$in": user_ids}}).to_list(None)
    return {user["_id"]: user.get("premium_status", "N/A") for user in users}



not_banned = filters.create(check_not_banned)

subscribed = filters.create(is_subscribed)
subscribed2 = filters.create(is_subscribed2)
