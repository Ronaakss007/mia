import asyncio
import motor.motor_asyncio
from config import  *
import random
import imaplib
import email
from email.header import decode_header
import time
from pyrogram.enums import ParseMode
from pyrogram import Client
import re
import pytz
import logging
from datetime import datetime,timedelta  
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

IST = pytz.timezone("Asia/Kolkata")

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)  # Create a logger instance

dbclient = motor.motor_asyncio.AsyncIOMotorClient(DB_URL)
database = dbclient[DB_NAME]

user_data = database['users']
admin_data = database['admins']
link_data = database['links']
envelop_data = database['envelopes']
file_collection = database['files']  # Define the files collection
claim_collection = database['claims']  # Define the claims collection
batch_data = database['batch_data']
conversation_collection = database['conversations']
video_messages_collection = database['video_messages']
# categories_collection = database['categories']
welcome_collection = database['welcome_messages']
payment_data = database['payments']
used_transactions = database['used_transactions']
group_spam = database['group_spam']
periodic_collection = database['periodic_messages']
token_collection = database['tokens']


IMAP_HOST = "imap.gmail.com"
IMAP_USER = "sainironak975@gmail.com"  # Change to your Gmail
IMAP_PASS = "olhk yawa ohbx syyr"  # Use Gmail App Password



async def fetch_upi_payments():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_HOST)
        mail.login(IMAP_USER, IMAP_PASS)
        mail.select("inbox")

        status, email_ids = mail.search(None, 'FROM "alerts@hdfcbank.net"')
        if status != "OK" or not email_ids[0]:
            return []

        email_list = email_ids[0].split()
        latest_5_emails = email_list[-5:]  # Fetch only the last 5 emails

        transactions = []
        kolkata_tz = pytz.timezone("Asia/Kolkata")

        for email_id in latest_5_emails:
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            if status != "OK":
                continue

            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            # Extract email date
            email_date = msg["Date"]
            try:
                email_datetime = datetime.strptime(email_date, "%a, %d %b %Y %H:%M:%S %z")
            except ValueError:
                continue  # Skip if date format is incorrect

            email_datetime = email_datetime.astimezone(kolkata_tz)

            # Extract email body
            email_body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/plain":
                        email_body = part.get_payload(decode=True).decode(errors="ignore")
                        break
                    elif content_type == "text/html" and not email_body:
                        email_body = part.get_payload(decode=True).decode(errors="ignore")
            else:
                email_body = msg.get_payload(decode=True).decode(errors="ignore")

            if not email_body:
                continue

            # Extract Amount
            amount_match = re.search(r"(?:INR|Rs\.?)\s?([\d,]+\.\d{2})", email_body)
            amount = float(amount_match.group(1).replace(",", "")) if amount_match else None

            # Extract UPI Reference ID
            ref_match = re.search(r"Your UPI transaction reference number is (\d+)\.", email_body)
            reference_id = ref_match.group(1) if ref_match else None

            if not reference_id or not amount:
                continue  # Skip transactions without reference number or amount

            transactions.append({
                "date": email_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                "amount": amount,
                "reference_id": reference_id
            })

        mail.logout()
        return transactions  # ✅ Always return a list

    except Exception as e:
        print(f"❌ IMAP Error: {e}")  # 🔹 Log the actual error for debugging
        return []  # ✅ Return empty list instead of error string

# async def verify_and_activate_premium(bot, user_id, plan_price, plan_duration_days):
#     transactions = fetch_upi_payments()
#     if not transactions:
#         return False, "No new payments found."

#     # Fetch user's existing premium status and used transactions
#     user = await database.users.find_one({"_id": user_id})
#     used_transactions = set(user.get("used_payments", []))  # Use a set for fast lookup

#     for txn in transactions:
#         txn_id = txn.get("txn_id") or txn.get("reference_id") or f"{txn['date']}-{txn['amount']}"  # Extract txn_id
        
#         # ✅ Ensure the payment belongs to the user (Prevent using others' payments)
#         if txn_id in used_transactions:
#             continue  # Skip already used payments

#         if txn.get("amount") == float(plan_price):
#             # ✅ Get current time
#             current_time = datetime.utcnow().timestamp()
            
#             # ✅ Extend expiry if user already has premium
#             existing_expiry = user.get("premium_expiry", 0)
#             if user.get("premium", False) and existing_expiry > current_time:
#                 expiry_timestamp = existing_expiry + (plan_duration_days * 86400)
#             else:
#                 expiry_timestamp = current_time + (plan_duration_days * 86400)

#             expiry_date = datetime.utcfromtimestamp(expiry_timestamp).strftime('%Y-%m-%d')

#             # ✅ Alert OWNER_ID about new premium activation
#             owner_message = (
#                 f"🔔 **New Premium Activation!**\n"
#                 f"👤 **User ID:** `{user_id}`\n"
#                 f"💰 **Amount:** ₹{plan_price}\n"
#                 f"📅 **Plan Duration:** {plan_duration_days} days\n"
#                 f"⏳ **Expiry Date:** {expiry_date}\n"
#                 f"🆔 **Transaction ID:** `{txn_id}`"
#             )
#             await bot.send_message(DUMB_CHAT, owner_message)

#             # ✅ Update user in database
#             await database.users.update_one(
#                 {"_id": user_id},
#                 {
#                     "$set": {"premium": True, "premium_expiry": expiry_timestamp},
#                     "$push": {"used_payments": txn_id}  # Store txn_id to prevent reuse
#                 }
#             )

#             return True, f"✅ Payment verified! Premium extended until {expiry_date}."

#     return False, "❌ No valid payment found. Please submit proof manually."



async def store_media_with_category(file_id: str, media_type: str, category: str):
    timestamp = datetime.utcnow().timestamp()
    await video_messages_collection.insert_one({
        "file_id": file_id,
        "type": media_type,
        "category": category,
        "timestamp": timestamp
    })
default_verify = {
    'is_verified': False,
    'verified_time': 0,
    'verify_token': "", 
    'link': ""
}

def new_user(id):
    return {
        '_id': id,
        'verify_status': {
            'is_verified': False,
            'verified_time': "",
            'verify_token': "",
            'link': ""
        },
        'premium': False,  # Add this line
        'premium_expiry': 0 , # Add this line
        'referrals':0,
        'referral_points': 0,
        'purchased_points': 0 ,
        'purchased_files': [],
        'free_media_count': 0
    }

async def store_video_message_ids(client: Client, channel_id: int):
    try:
        print(f"Fetching messages from channel ID: {channel_id}")

        chat_member = await client.get_chat_member(channel_id, client.me.id)
        if chat_member.status not in ['creator', 'administrator']:
            print(f"❌ Not an admin in channel {channel_id}. Skipping...")
            return
        # Fetch messages from the channel
        messages = []
        async for msg in client.get_chat_history(channel_id, limit=1000):
            if msg.video:
                messages.append({
                    'message_id': msg.message_id,
                    'date': msg.date
                })

        # Store message IDs in the database using bulk write
        if messages:
            operations = [
                motor.motor_asyncio.UpdateOne(
                    {'message_id': msg['message_id']},
                    {'$set': msg},
                    upsert=True
                ) for msg in messages
            ]
            await video_messages_collection.bulk_write(operations)
        print("Video message IDs stored successfully.for channel ID: {channel_id}")
    except Exception as e:
        logger.error(f"Error storing video message IDs: {str(e)}")

async def new_link(hash: str):
    return {
        'clicks': 0,
        'hash': hash
    }

async def can_bypass_points(user_info):
    is_premium = user_info.get("premium", False)
    premium_status = user_info.get("premium_status", "")  # Retrieve stored premium plan
    premium_expiry = user_info.get("premium_expiry", 0)
    current_time = int(time.time())

    if not is_premium or premium_expiry <= current_time:
        return False

    # ✅ Allow bypass of points requirement for 'Elite', 'Prestige', 'Royal', and 'Ultimate' plans
    allowed_plans = ["💫 Elite", "⭐ Prestige", "👑 Royal", "👑 Ultimate"]

    if premium_status in allowed_plans:
        return True  # Bypass points requirement
    return False  # Points are required


async def should_protect_content(user_info):
    is_premium = user_info.get("premium", False)
    premium_status = user_info.get("premium_status", "⚡ VIP")  # Default to VIP if missing
    premium_expiry = user_info.get("premium_expiry", 0)
    current_time = int(time.time())

    days_left = (premium_expiry - current_time) // 86400  # Convert seconds to days

    # ✅ Protect content for "⚡ VIP" (1-day & 7-day plans)
    if premium_status in ["⚡ VIP"]:
        return True  # Content is protected

    # ✅ Unprotect content for "🔥 Pro" and above (1-month+ plans)
    if premium_status in ["🔥 Pro", "💫 Elite", "⭐ Prestige", "👑 Royal", "👑 Ultimate"]:
        return False  # Content is unprotected

    return True  # Default to protecting content


async def can_keep_files_permanently(user_info):
    is_premium = user_info.get("premium", False)
    premium_status = user_info.get("premium_status", "")  # Retrieve stored premium plan
    premium_expiry = user_info.get("premium_expiry", 0)
    current_time = int(time.time())

    if not is_premium or premium_expiry <= current_time:
        return False

    # ✅ Allow permanent file access for 'Prestige', 'Royal', and 'Ultimate' plans
    allowed_plans = ["⭐ Prestige", "👑 Royal", "👑 Ultimate"]

    if premium_status in allowed_plans:
        return True

    return False  # Files will be deleted later

async def get_user_info(user_id):
    user_info = await user_data.find_one({"_id": user_id})
    return user_info if user_info else {}
    
async def get_click_details(hash: str):
    """Fetch total clicks and timestamps for a given hash."""
    record = await link_data.find_one({"hash": hash})

    return {
        "clicks": record.get("clicks", 0) if record else 0,
        "first_click": record.get("first_click", None) if record else None,
        "last_click": record.get("last_click", None) if record else None
    }


async def gen_new_count(hash: str):
    """Insert a new link record if it does not exist."""
    if not await present_hash(hash):
        await link_data.insert_one({'hash': hash, 'clicks': 0, 'first_click': None, 'last_click': None})


async def present_hash(hash: str):
    """Check if a hash exists in the database."""
    return await link_data.count_documents({"hash": hash}) > 0


async def get_clicks(hash: str):
    data = await link_data.find_one({'hash': hash})
    if data is None:
        return 0
    clicks = data.get('clicks', 0)
    return clicks

async def inc_count(hash: str):
    """Increment click count and update timestamps properly with IST timezone."""
    now_utc = datetime.utcnow()  # Get current UTC time
    now_ist = now_utc.replace(tzinfo=pytz.utc).astimezone(IST)  # Convert to IST
    now_timestamp = int(now_ist.timestamp())  # Convert to Unix timestamp

    # Fetch existing record
    record = await link_data.find_one({"hash": hash})

    # If record exists, update timestamps
    if record:
        update_data = {
            '$inc': {'clicks': 1},
            '$set': {'last_click': now_timestamp}
        }
        
        # If first_click is missing, set it now
        if record.get("first_click") is None:
            update_data['$set']['first_click'] = now_timestamp
        
        await link_data.update_one({'hash': hash}, update_data)
    
    # If record does not exist, create a new one
    else:
        await link_data.insert_one({
            'hash': hash,
            'clicks': 1,
            'likes': 0,  # Initialize likes
            'dislikes': 0,  # Initialize dislikes
            'first_click': now_timestamp,
            'last_click': now_timestamp
        })

    # print(f"✅ Click count updated for hash: {hash} at {now_ist.strftime('%Y-%m-%d %H:%M:%S IST')}")

#users
async def present_user(user_id: int):
    found = await user_data.find_one({'_id': user_id})
    return bool(found)

async def add_user(user_id: int):
    user = new_user(user_id)
    await user_data.insert_one(user)
    return

async def db_verify_status(user_id):
    user = await user_data.find_one({'_id': user_id})
    if user:
        return user.get('verify_status', default_verify)
    return default_verify

async def db_update_verify_status(user_id, verify):
    await user_data.update_one({'_id': user_id}, {'$set': {'verify_status': verify}})

async def full_userbase():
    user_docs = user_data.find()
    user_ids = [doc['_id'] async for doc in user_docs]
    return user_ids

async def delete_user(user_id: int):
    """Delete a user and log success in the console."""
    result = await user_data.delete_one({'_id': user_id})
    
    if result.deleted_count > 0:
        logger.info(f"✅ User with ID {user_id} deleted successfully from the database.")
        print(f"✅ User with ID {user_id} deleted successfully from the database.")  # Console log
    else:
        logger.warning(f"⚠️ User with ID {user_id} not found in the database.")
        print(f"⚠️ User with ID {user_id} not found in the database.")  # Console log

    return result.deleted_count  # Returns 1 if deleted, 0 if not found


#admins

async def present_admin(user_id: int):
    found = await admin_data.find_one({'_id': user_id})
    return bool(found)


async def add_admin(user_id: int):
    user = new_user(user_id)
    await admin_data.insert_one(user)
    ADMINS.append(int(user_id))
    return

async def del_admin(user_id: int):
    await admin_data.delete_one({'_id': user_id})
    ADMINS.remove(int(user_id))
    return

async def full_adminbase():
    user_docs = admin_data.find()
    user_ids = [int(doc['_id']) async for doc in user_docs]
    return user_ids

async def update_referrals(user_id: int):
    await user_data.update_one({'_id': user_id}, {'$inc': {'referrals': 1}})

# async def get_referral_points(user_id: int):
#     user = await user_data.find_one({'_id': user_id})
#     if user:
#         return user.get('referral_points', 0)
#     return 0

async def get_users_with_referrals():
    # Use the globally defined 'user_data' collection directly
    user_data_collection = user_data  # Directly use the user_data collection initialized earlier
    
    # Query users with at least 1 referral
    user_data_list = await user_data_collection.find({'referrals': {'$gte': 1}}).to_list(length=None)
    
    users = []
    for user in user_data_list:
        user_id = user.get("_id")
        first_name = user.get("first_name", "N/A")
        referral_count = len(user.get("referrals", []))  # Count referrals properly
        points = user.get("referral_points", 0)
        
        users.append({
            "user_id": user_id,
            "first_name": first_name,
            "referral_count": referral_count,
            "points": points
        })
    
    return users


# async def update_referrals(user_id):
#     user = await user_data.find_one({'_id': user_id})
#     if user:
#         referrals = user.get('referrals', 0)
#         if isinstance(referrals, list):
#             referrals.append(user_id)
#         else:
#             referrals = [user_id]
#         await user_data.update_one({'_id': user_id}, {'$set': {'referrals': referrals}})
#     else:
#         await user_data.update_one({'_id': user_id}, {'$set': {'referrals': [user_id]}})

async def update_referrals(user_id, new_referral_count):
    await user_data.update_one({'_id': user_id}, {'$set': {'referral_count': new_referral_count}})
# async def get_referral_count(referrer_id):
#     user = await user_data.find_one({'_id': referrer_id})
#     if user:
#         referrals = user.get('referrals', [])
#         return len(referrals)
#     return 0

async def get_referral_count(user_id):
    # Get the referral count for the user (pseudo-function, implement as needed)
    user = await database['users'].find_one({'user_id': user_id})
    return user.get("referral_count", 0)


async def store_referrer(referrer_id, referred_id, bot, OWNER_ID):
    referrer = await user_data.find_one({'_id': referrer_id})

    if referrer:
        referrals = referrer.get('referrals', [])
        referral_points = referrer.get('referral_points', 0)
        purchased_points = referrer.get('purchased_points', 0)  # Get purchased points

        if not isinstance(referrals, list):
            referrals = []

        # ✅ Prevent re-referral
        if referred_id in referrals:
            print(f"User {referred_id} was already referred by {referrer_id}, skipping.")
            return

        # ✅ Update referrals and points
        referrals.append(referred_id)
        referral_points += REFERRAL_REWARD

        await user_data.update_one(
            {'_id': referrer_id},
            {'$set': {'referrals': referrals, 'referral_points': referral_points}}
        )

        print(f"✅ User {referrer_id} referred user {referred_id} and earned {REFERRAL_REWARD} points!")

        # ✅ Calculate total points
        total_points = referral_points + purchased_points

        # ✅ Send alert to OWNER_ID with all points details
        alert_message = (
            f"<b>📣 Rᴇғᴇʀʀᴀʟ Aʟᴇʀᴛ !</b>\n\n"
            f"<b>👤 Rᴇғᴇʀʀᴇʀ Iᴅ : {referrer_id}</b>\n"
            f"<b>👥 Nᴇᴡ Rᴇғᴇʀʀᴇʀ Iᴅ : {referred_id}</b>\n"
            f"<b>🏆 Pᴏɪɴᴛs Eᴀʀɴᴇᴅ : {REFERRAL_REWARD}</b>\n"
            f"<b>💯 Tᴏᴛᴀʟ Rᴇғᴇʀʀᴀʟs : {len(referrals)}</b>\n"
            f"<b>💰 Tᴏᴛᴀʟ Rᴇғᴇʀʀᴀʟs Pᴏɪɴᴛs : {referral_points}</b>\n"
            f"<b>🛒 Pᴜʀᴄʜᴀsᴇᴅ Pᴏɪɴᴛs : {purchased_points}</b>\n"
            f"<b>🎯 Tᴏᴛᴀʟ Pᴏɪɴᴛs : {total_points}</b>"
        )

        await bot.send_message(chat_id=OWNER_ID, text=alert_message)


async def reward_referral_points(referrer_id):
    """Adds points to the referrer when they successfully refer a user."""
    referrer = await user_data.find_one({'_id': referrer_id})
    if referrer:
        new_points = referrer.get('referral_points', 0) + point_per_referral
        await user_data.update_one({'_id': referrer_id}, {'$set': {'referral_points': new_points}})
        
        # Notify the referrer
        await Bot.send_message(referrer_id, f"🎉 You referred a new user! You earned {point_per_referral} points. Total: {new_points} points.")

async def increment_referral_count(client, referrer_id, referred_id):
    """Stores referral and rewards points."""
    user = await user_data.find_one({'_id': referrer_id})
    
    if user:
        referrals = user.get('referrals', [])

        # Ensure the referred user is not already in the list
        if referred_id not in referrals:
            await user_data.update_one({'_id': referrer_id}, {'$push': {'referrals': referred_id}})
            await reward_referral_points(referrer_id)
        else:
            await client.send_message(referred_id, "You have already been referred by this user!")

async def get_referral_points(user_id: int):
    try:
        # Fetch user data from the database
        user_info = await user_data.find_one({'_id': user_id})
        
        if user_info is None:
            return 0
        
        return user_info.get('referral_points', 0)
    except Exception as e:
        logger.error(f"Error fetching points for user {user_id}: {str(e)}")
        return 0


async def update_referral_points(user_id: int, new_points: int):
    try:
        user_info = await get_user_data(user_id)
        if user_info is None:
            await user_data.insert_one({'_id': user_id, 'referral_points': new_points})
            logger.debug(f"User {user_id} not found. Creating new user with points {new_points}.")
            return new_points
        
        current_points = user_info.get('referral_points', 0)
        logger.debug(f"Current points for {user_id}: {current_points}, New points: {new_points}")
        
        if current_points == new_points:
            logger.debug(f"Points for user {user_id} are already at {current_points}. No update needed.")
            return current_points
        
        result = await user_data.update_one(
            {'_id': user_id},
            {'$set': {'referral_points': new_points}}
        )
        
        if result.modified_count == 0:
            logger.warning(f"No update was made for user {user_id}. Current points: {current_points}, New points: {new_points}")
        else:
            logger.debug(f"Updated referral points for {user_id} to {new_points}.")
        
        return new_points
    except Exception as e:
        logger.error(f"Error updating referral points for user {user_id}: {str(e)}")
        return None



async def calculate_referral_points(referral_count: int):
    return referral_count * REFERRAL_REWARD  # 25 points per referral

async def get_user_data(user_id: int):
    try:
        logger.debug(f"Type of user_data: {type(user_data)}")  # Debug the type of user_data
        user_info = await user_data.find_one({'_id': user_id})  # Use 'user_info' instead of 'user_data'
        if not user_info:
            raise ValueError(f"User  data not found for user ID: {user_id}")
        return user_info  # Return the user document as a dictionary
    except Exception as e:
        logger.error(f"Error fetching data for user {user_id}: {str(e)}")
        return None  # Indicate error

async def get_all_users():
    try:
        users = []
        async for user in user_data.find({}):  # Fetch all users from 'users' collection
            users.append(user)
        return users
    except Exception as e:
        logger.error(f"Error fetching all users: {e}")
        return []

async def get_user_points(user_id: int):
    try:
        user_data = await get_user_data(user_id)  # Use get_user_data function
        return user_data  # If user_data is returned successfully, it means points are available
    except Exception as e:
        logger.error(f"Error fetching points for user {user_id}: {str(e)}")
        return 0  # Return default 0 points if there's an issue

async def buy_points(user_id, points_to_buy):
    # Fetch the user's data from the database
    user = await user_data.find_one({'_id': user_id})
    
    if not user:
        return "User not found."

    # Get the current purchased points (we'll leave referral points unchanged)
    purchased_points = user.get('purchased_points', 0)

    # Add the points purchased by the user
    new_purchased_points = purchased_points + points_to_buy

    # Update only the purchased_points in the user's data
    await user_data.update_one(
        {'_id': user_id},
        {'$set': {'purchased_points': new_purchased_points}}
    )

    # Calculate total points (referral points + purchased points)
    total_points = user.get('referral_points', 0) + new_purchased_points

    # Return the updated total points to the user
    return f"Your points have been successfully updated! You now have {total_points} points in total, including {new_purchased_points} purchased points."


async def subtract_points(user_id, points_to_subtract):
    # Fetch the user's data from the database
    user = await user_data.find_one({'_id': user_id})
    
    if not user:
        return "User not found."

    # Get the current purchased points (we'll leave referral points unchanged)
    purchased_points = user.get('purchased_points', 0)

    # Ensure the user has enough purchased points to subtract
    if points_to_subtract > purchased_points:
        return f"You don't have enough purchased points. You currently have {purchased_points} purchased points."

    # Subtract the points from purchased points
    new_purchased_points = purchased_points - points_to_subtract

    # Update only the purchased_points in the user's data
    await user_data.update_one(
        {'_id': user_id},
        {'$set': {'purchased_points': new_purchased_points}}
    )

    # Calculate total points (referral points + purchased points)
    total_points = user.get('referral_points', 0) + new_purchased_points

    # Return the updated total points to the user
    return f"Your points have been successfully updated! You now have {total_points} points in total, including {new_purchased_points} purchased points."

async def del_user(user_id):
    try:
        # Logic to remove the user from the database
        user_collection = db.users  # Adjust to your MongoDB collection name
        result = await user_collection.delete_one({'_id': user_id})  # Delete user by user_id
        if result.deleted_count > 0:
            print(f"User {user_id} successfully removed from the database.")
        else:
            print(f"User {user_id} not found in the database.")
    except Exception as e:
        print(f"Error removing user {user_id}: {e}")

async def spin_wheel(user_id):
    try:

        # Simulate the wheel spin result
        spin_result = random.choices(REWARDS, weights=WEIGHTS, k=1)[0]
        
        logging.info(f"Spin result for user {user_id}: {spin_result}")

        # Fetch user from the database
        user = await user_data.find_one({'_id': user_id})

        if not user:
            logging.error(f"User {user_id} not found in the database.")
            return None  # Return None if the user is not found
        
        # Add points to the user's account based on the result
        if spin_result > 0:
            updated_points = user.get('purchased_points', 0) + spin_result

            # Update the user's points in the database
            await user_data.update_one({'_id': user_id}, {"$set": {'purchased_points': updated_points}})
            logging.info(f"User {user_id}'s points updated to {updated_points}.")
            return spin_result  # Return the points awarded
        else:
            logging.info(f"User {user_id} received no reward.")
            return 0  # No reward this time

    except Exception as e:
        logging.error(f"Error occurred during spin for user {user_id}: {e}")
        return None  # Return None in case of any exception

# Mega Spin 
async def mega_spin_wheel(user_id):
    """Handle Mega Spin Wheel."""
    spin_result = random.choices(MEGA_REWARDS, weights=MEGA_WEIGHTS, k=1)[0]
    
    # Fetch user from database
    user = await user_data.find_one({'_id': user_id})
    
    if not user:
        return False  # User doesn't exist
    
    # Add points to user based on spin result
    if spin_result > 0:
        updated_points = user.get('purchased_points', 0) + spin_result
        
        # Update the user's points in the database
        await user_data.update_one({'_id': user_id}, {"$set": {'purchased_points': updated_points}})
        
        return spin_result  # Return the points awarded
    else:
        return 0  # No points awarded

def convert_seconds_to_hours(seconds):
    hours = seconds // 3600  # Integer division to get the full hours
    minutes = (seconds % 3600) // 60  # Remainder for minutes
    remaining_seconds = seconds % 60  # Remaining seconds after minutes

    return f"{hours} Hᴏᴜʀ {minutes} Mɪɴ {remaining_seconds} Sᴇᴄ"

async def cleanup_expired_envelopes(client):
    print("🔄 Checking for expired envelopes...")  # Debugging

    expired_envelopes = await envelop_data.find({"expiry_time": {"$lt": datetime.utcnow()}}).to_list(length=100)
    print(f"Found {len(expired_envelopes)} expired envelopes.")  # Debugging

    for envelope in expired_envelopes:
        envelope_name = envelope["name"]
        remaining_points = envelope["remaining_points"]

        print(f"⏳ Expiring envelope: {envelope_name} with {remaining_points} points.")  # Debugging

        # ✅ Notify OWNER about expiry
        try:
            notification_text = (
                f"📩 Eɴᴠᴇʟᴏᴘ Exᴘɪʀᴇᴅ ❌\n"
                f"🏷 Nᴀᴍᴇ : {envelope_name}\n"
                f"💰Pᴏɪɴᴛs Exᴘɪʀᴇᴅ :  {remaining_points}\n"
                f"⏳ Exᴘɪʀᴇᴅ Aᴛ : {envelope['expiry_time'].strftime('%Y-%m-%d %H:%M:%S UTC')}"
            )
            await client.send_message(OWNER_ID, notification_text, parse_mode=ParseMode.MARKDOWN)
            print("✅ Expiry notification sent to OWNER.")  # Debugging
        except Exception as e:
            print(f"❌ Failed to notify owner about expired envelope: {e}")

        # ✅ Delete the expired envelope
        await envelop_data.delete_one({"_id": envelope["_id"]})
        print(f"🗑 Deleted expired envelope: {envelope_name}")  # Debugging

async def delete_broadcast_message(client, chat_id, message_id, delay):
    await asyncio.sleep(delay)
    try:
        await client.delete_messages(chat_id, message_id)
        print(f"✅ Deleted message {message_id} from chat {chat_id}")
    except Exception as e:
        print(f"❌ Failed to delete message {message_id}: {e}")

# Add this function before the envelop command handler


# 🔹 **Step 4: Run Cleanup Periodically**
async def schedule_cleanup(client):
    while True:
        await cleanup_expired_envelopes(client)
        await asyncio.sleep(60)  # Run every 10 minutes

async def delete_old_media(client: Client):
    while True:
        try:
            now = datetime.utcnow().timestamp()
            cutoff_time = now - (60 * 24 * 60 * 60)  # 15 days retention
            
            result = await video_messages_collection.delete_many({"timestamp": {"$lt": cutoff_time}})
            
            if result.deleted_count > 0:
                await client.send_message(
                    OWNER_ID, 
                    f"📢 {result.deleted_count} media items were deleted"
                )

        except Exception as e:
            await client.send_message(OWNER_ID, f"⚠️ Error in delete_old_media: {str(e)}")

        await asyncio.sleep(3600)  # Runs every hour

async def initialize_file_record(file_id: str):
    """Ensure likes, dislikes, and user interactions are initialized for a file."""
    await link_data.update_one(
        {"_id": ObjectId(file_id)},
        {
            "$setOnInsert": {
                "likes": 0,
                "dislikes": 0,
                "user_interactions": {}  # Track user interactions (user_id -> "like" or "dislike")
            }
        },
        upsert=True
    )

# Ensure likes and dislikes fields are initialized when adding a new file
# await link_data.update_one(
#     {"_id": ObjectId(file_id)},
#     {"$setOnInsert": {"likes": 0, "dislikes": 0}},
#     upsert=True
# )

async def get_click_details(hash: str):
    """Fetch total clicks, likes, dislikes, and timestamps for a given hash."""
    record = await link_data.find_one({"hash": hash})
    
    if not record:
        return "❌ 𝗡𝗼 𝗖𝗹𝗶𝗰𝗸𝘀 𝗙𝗼𝘂𝗻𝗱 𝗳𝗼𝗿 𝘁𝗵𝗶𝘀 𝗟𝗶𝗻𝗸."

    clicks = record.get("clicks", 0)
    likes = record.get("likes", 0)
    dislikes = record.get("dislikes", 0)
    first_click = record.get("first_click")
    last_click = record.get("last_click")

    # Convert timestamps to readable format in IST
    local_tz = pytz.timezone('Asia/Kolkata')

    first_click_str = "⏳ Nᴏᴛ Rᴇᴄᴏʀᴅᴇᴅ" if not first_click else \
        datetime.fromtimestamp(first_click, tz=pytz.utc).astimezone(local_tz).strftime('%d-%b-%Y | %I:%M %p')
    
    last_click_str = "⏳ Nᴏᴛ Rᴇᴄᴏʀᴅᴇᴅ" if not last_click else \
        datetime.fromtimestamp(last_click, tz=pytz.utc).astimezone(local_tz).strftime('%d-%b-%Y | %I:%M %p')

    return f"""
🎯 **Lɪɴᴋ Cʟɪᴄᴋ Sᴛᴀᴛs**
━━━━━━━━━━━━━━━━━━
🔗 **Hᴀsʜ:** `{hash}`
👀 **Tᴏᴛᴀʟ Cʟɪᴄᴋs:** `{clicks}`
👍 **Lɪᴋᴇs:** `{likes}`
👎 **Dɪsʟɪᴋᴇs:** `{dislikes}`
📌 **Fɪʀsᴛ Cʟɪᴄᴋ:** `{first_click_str}`
📍 **Lᴀsᴛ Cʟɪᴄᴋ:** `{last_click_str}`
━━━━━━━━━━━━━━━━━━
""".strip()

# Function to create a progress bar
def progress_bar(referral_count, next_tier):
    progress = int((referral_count / next_tier) * 10)  
    return f"{'■' * progress}{'□' * (10 - progress)} {referral_count}/{next_tier}"

referral_tiers = {
    2: 30,    # Increased from 25  
    5: 120,   # Increased from 100  
    10: 300,  # Increased from 250  
    25: 800,  # Increased from 650  
    50: 1800, # New tier with extra bonus  
    100: 4000 # New tier with a big reward  
}


