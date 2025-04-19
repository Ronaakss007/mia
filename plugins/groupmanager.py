from pyrogram import Client, filters
from pyrogram.types import Message, ForceReply, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatMemberStatus, ChatType
from database.database import *
from datetime import datetime, timezone
from time import time
import asyncio
import pytz
IST = pytz.timezone("Asia/Kolkata")
from pyrogram.types import ChatPermissions

# CHANNEL_ID = -1002208652535  # Your target channel ID
INTERVAL = 600  # 10 minutes in seconds

# Create a new collection for welcome messages
welcome_collection = database['welcome_messages']
periodic_collection = database['periodic_messages']
periodic_msgs = database['periodic_messages']
active_tasks = {}
DEFAULT_WELCOME = "Welcome {mention} to {chat_title}! 🎉"
periodic_messages = {}

async def is_admin(chat_id: int, user_id: int, client) -> bool:
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]
    except Exception:
        return False

@Client.on_message(filters.command("clearwelcome") & filters.group)
async def delete_welcome(client, message: Message):
    if not message.from_user or not await is_admin(message.chat.id, message.from_user.id, client):
        return await message.reply("Only admins can delete welcome messages!")

    # Check if welcome text exists in database
    welcome_data = await welcome_collection.find_one({'chat_id': message.chat.id})
    if not welcome_data:
        return await message.reply("No welcome message set for this group!")

    # Delete from database
    await welcome_collection.delete_one({'chat_id': message.chat.id})

    await message.reply(f"Welcome message deleted successfully!")

@Client.on_message(filters.command("welcome") & filters.group)
async def show_welcome(client, message: Message):
    if not message.from_user or not await is_admin(message.chat.id, message.from_user.id, client):
        return await message.reply("Only admins can view welcome messages!")

    # Get welcome text from database
    welcome_data = await welcome_collection.find_one({'chat_id': message.chat.id})
    if not welcome_data:
        return await message.reply("No welcome message set for this group!")

    welcome_text = welcome_data['welcome_text']

    await message.reply(welcome_text)

@Client.on_message(filters.command("setwelcome") & filters.group)
async def set_welcome(client, message: Message):
    if not message.from_user or not await is_admin(message.chat.id, message.from_user.id, client):
        return await message.reply("Only admins can set welcome messages!")
        
    if len(message.command) < 3:
        return await message.reply("Please provide a welcome message and enable/disable option!\n\nExample:\n/setwelcome Welcome {mention} to our group! on")

    welcome_text = " ".join(message.command[1:-1])
    status = message.command[-1].lower()

    if status not in ["on", "off"]:
        return await message.reply("Please specify 'on' or 'off' to enable or disable the welcome message.")

    welcome_enabled = status == "on"
    
    # Store in database
    await welcome_collection.update_one(
        {'chat_id': message.chat.id},
        {'$set': {
            'welcome_text': welcome_text,
            'welcome_enabled': welcome_enabled
        }},
        upsert=True
    )
    
    await message.reply(f"Welcome message set successfully!\n\nPreview:\n{welcome_text}\nStatus: {'Enabled' if welcome_enabled else 'Disabled'}")

@Client.on_chat_member_updated()
async def handle_group_joins(client, chat_member_updated):
    if (chat_member_updated.new_chat_member and 
        chat_member_updated.new_chat_member.status == ChatMemberStatus.MEMBER and 
        chat_member_updated.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]):
        
        chat_id = chat_member_updated.chat.id
        user = chat_member_updated.new_chat_member.user
        chat_title = chat_member_updated.chat.title
        mention = user.mention
        
        # Get welcome message from database
        welcome_data = await welcome_collection.find_one({'chat_id': chat_id})
        
        if welcome_data and welcome_data.get('welcome_enabled', True):
            welcome_text = welcome_data['welcome_text']
        else:
            return  # Welcome message is disabled, do not send
        
        welcome_message = welcome_text.format(
            mention=mention,
            chat_title=chat_title
        )
        
        try:
            await client.send_message(
                chat_id=chat_id,
                text=welcome_message
            )
        except Exception as e:
            print(f"Could not send welcome message: {str(e)}")

async def load_periodic_messages(client):
    """Load all periodic messages from database on bot startup"""
    async for doc in welcome_collection.find({'periodic_text': {'$exists': True}}):
        chat_id = doc['chat_id']
        periodic_text = doc['periodic_text']
        interval = doc['interval']
        task = asyncio.create_task(send_periodic_message(client, chat_id, periodic_text, interval))
        periodic_messages[chat_id] = task

@Client.on_message(filters.command("setperiodic") & filters.group)
async def set_periodic(client, message: Message):
    if not message.from_user or not await is_admin(message.chat.id, message.from_user.id, client):
        return await message.reply("Only admins can set periodic messages!")
        
    if len(message.command) < 3:
        return await message.reply("Please provide interval (in minutes) and message!\n\nExample:\n/setperiodic 10 Hello everyone!")

    try:
        interval = int(message.command[1])
        periodic_text = " ".join(message.command[2:])
        chat_id = message.chat.id
        chat_title = message.chat.title
        
        # Store in dedicated collection
        await periodic_collection.update_one(
            {'chat_id': chat_id},
            {'$set': {
                'periodic_text': periodic_text,
                'interval': interval,
                'is_active': True,
                'chat_title': chat_title,
                'set_by': message.from_user.id,
                'set_time': message.date
            }},
            upsert=True
        )
        
        if chat_id in periodic_messages:
            periodic_messages[chat_id].cancel()
            
        task = asyncio.create_task(send_periodic_message(client, chat_id, periodic_text, interval))
        periodic_messages[chat_id] = task
        
        await message.reply(f"✅ Periodic message set!\nInterval: {interval} minutes\nMessage: {periodic_text}")
        
    except ValueError:
        await message.reply("Please provide a valid number for interval!")

@Client.on_message(filters.command("listperiodic") & filters.group)
async def list_periodic(client, message: Message):
    if not message.from_user or not await is_admin(message.chat.id, message.from_user.id, client):
        return await message.reply("Only admins can view periodic messages!")

    active_messages = await periodic_collection.find({'is_active': True}).to_list(length=None)
    
    if not active_messages:
        return await message.reply("No active periodic messages found!")
    
    response = "📢 Active Periodic Messages:\n\n"
    for idx, msg in enumerate(active_messages, 1):
        response += f"Group: {msg['chat_title']}\n"
        response += f"Interval: {msg['interval']} minutes\n"
        response += f"Message: {msg['periodic_text']}\n"
        response += f"Set by: {msg['set_by']}\n"
        response += "─────────────────\n"
    
    await message.reply(response)

async def load_periodic_messages(client):
    """Load active periodic messages from database on bot startup"""
    active_messages = await periodic_collection.find({'is_active': True}).to_list(length=None)
    for msg in active_messages:
        chat_id = msg['chat_id']
        periodic_text = msg['periodic_text']
        interval = msg['interval']
        task = asyncio.create_task(send_periodic_message(client, chat_id, periodic_text, interval))
        periodic_messages[chat_id] = task

async def send_periodic_message(client, group_id, message_text, interval):
    while True:
        try:
            # Add a check for bot status
            if not client.is_connected:
                await client.connect()
                
            await client.send_message(
                chat_id=group_id,
                text=message_text
            )
            
            # Update last sent time in database
            await periodic_collection.update_one(
                {'chat_id': group_id},
                {'$set': {
                    'last_sent': datetime.now(IST),
                    'status': 'success'
                }}
            )
            
            # Add a small delay between messages to prevent overload
            await asyncio.sleep(0.5)
            
        except Exception as e:
            print(f"Periodic message error: {e}")
            # Update error status in database
            await periodic_collection.update_one(
                {'chat_id': group_id},
                {'$set': {
                    'status': 'error',
                    'last_error': str(e),
                    'error_time': datetime.now(IST)
                }}
            )
            
        # Use proper interval timing
        await asyncio.sleep(interval * 60)


@Client.on_message(filters.command(["periodicstatus", "pstatus"]) & filters.group)
async def periodic_status(client, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id, client):
        return await message.reply("Only admins can check periodic message status!")
        
    chat_id = message.chat.id
    status = await periodic_collection.find_one({'chat_id': chat_id})
    
    if not status:
        return await message.reply("No periodic message configured for this group!")
        
    response = "📊 Periodic Message Status\n\n"
    response += f"▫️ Interval: {status['interval']} minutes\n"
    response += f"▫️ Active: {'✅' if status['is_active'] else '❌'}\n"
    response += f"▫️ Last Sent: {status.get('last_sent', 'Never')}\n"
    response += f"▫️ Message:\n{status['periodic_text']}"
    
    await message.reply(response)

@Client.on_message(filters.command(["stopperiodic", "pstop"]) & filters.group)
async def stop_periodic(client, message: Message):
    if not message.from_user or not await is_admin(message.chat.id, message.from_user.id, client):
        return await message.reply("Only admins can stop periodic messages!")

    chat_id = message.chat.id
    
    if chat_id in periodic_messages:
        periodic_messages[chat_id].cancel()
        del periodic_messages[chat_id]
        
        # Update database
        await periodic_collection.update_one(
            {'chat_id': chat_id},
            {'$set': {'is_active': False}}
        )
        
        await message.reply("✅ Periodic messages stopped!")
    else:
        await message.reply("No periodic messages are currently running!")

@Client.on_message(filters.command(["startperiodic", "pstart"]) & filters.group)
async def start_periodic(client, message: Message):
    if not message.from_user or not await is_admin(message.chat.id, message.from_user.id, client):
        return await message.reply("Only admins can start periodic messages!")

    chat_id = message.chat.id
    msg_data = await periodic_collection.find_one({'chat_id': chat_id})
    
    if not msg_data:
        return await message.reply("No periodic message found! Set one using /setperiodic")
        
    if msg_data.get('is_active', False):
        return await message.reply("Periodic message is already running!")
    
    # Start the periodic task
    task = asyncio.create_task(send_periodic_message(
        client, 
        chat_id, 
        msg_data['periodic_text'], 
        msg_data['interval']
    ))
    periodic_messages[chat_id] = task
    
    # Update database
    await periodic_collection.update_one(
        {'chat_id': chat_id},
        {'$set': {'is_active': True}}
    )
    
    await message.reply("✅ Periodic messages resumed!")

@Client.on_message(filters.command(["deleteperiodic", "pdel"]) & filters.group)
async def delete_periodic(client, message: Message):
    if not message.from_user or not await is_admin(message.chat.id, message.from_user.id, client):
        return await message.reply("Only admins can delete periodic messages!")

    chat_id = message.chat.id
    
    # Stop if running
    if chat_id in periodic_messages:
        periodic_messages[chat_id].cancel()
        del periodic_messages[chat_id]
    
    # Delete from database
    result = await periodic_collection.delete_one({'chat_id': chat_id})
    
    if result.deleted_count > 0:
        await message.reply("✅ Periodic message configuration deleted!")
    else:
        await message.reply("No periodic message found to delete!")

@Client.on_message(filters.command(["kick", "dkick"]) & filters.group)
async def kick_user(client: Client, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id, client):
        return await message.reply("🚫 Only admins can use this command!")
    
    if len(message.command) == 1 and not message.reply_to_message:
        return await message.reply("Reply to a user's message or provide username/id to kick")
    
    try:
        user_id = message.reply_to_message.from_user.id if message.reply_to_message else int(message.command[1])
        
        # Check if user is admin
        member = await client.get_chat_member(message.chat.id, user_id)
        if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return await message.reply("❌ Cannot kick administrators!")
        
        await client.ban_chat_member(message.chat.id, user_id)
        await client.unban_chat_member(message.chat.id, user_id)  # Immediately unban to allow rejoin
        
        user = await client.get_users(user_id)
        await message.reply(f"👞 Kicked {user.mention}")
        
        if "dkick" in message.command[0]:
            await message.delete()
            
    except Exception as e:
        await message.reply("Failed to kick user. Make sure I have proper permissions!")

@Client.on_message(filters.command(["mute", "dmute"]) & filters.group)
async def mute_user(client: Client, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id, client):
        return await message.reply("🚫 Only admins can use this command!")

    # Check if user is banned
    if await is_banned(user_id):
        await message.reply_text(f"🚫 You are banned from using this bot.\nContact @{OWNER_TAG}")
        return

    # Get target user
    user_id = None
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
    elif len(message.command) > 1:
        if message.command[1].isdigit():
            user_id = int(message.command[1])
        else:
            try:
                user = await client.get_users(message.command[1])
                user_id = user.id
            except:
                return await message.reply("✨ Please provide a valid user ID/username or reply to a message")

    if not user_id:
        return await message.reply("👉 Specify who to mute - reply to their message or use their username/ID")

    # Set mute duration
    duration = 0
    if len(message.command) > 1 and message.command[-1][-1] in ['m', 'h', 'd']:
        time_value = message.command[-1]
        unit = time_value[-1]
        try:
            amount = int(time_value[:-1])
            duration = {
                'm': amount * 60,
                'h': amount * 3600,
                'd': amount * 86400
            }[unit]
        except ValueError:
            pass

    try:
        # Check if target user is admin
        member = await client.get_chat_member(message.chat.id, user_id)
        if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return await message.reply("❌ Cannot mute administrators!")

        # Set mute permissions
        permissions = ChatPermissions(
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_polls=False,
            can_add_web_page_previews=False,
            can_invite_users=False,
            can_pin_messages=False
        )

        until_date = int(time()) + duration if duration > 0 else 0

        await client.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=user_id,
            permissions=permissions,
            until_date=until_date
        )

        user = await client.get_users(user_id)
        duration_text = f" for {message.command[-1]}" if duration > 0 else " permanently"
        await message.reply(f"🔇 Muted {user.mention}{duration_text}")

        if "dmute" in message.command[0]:
            await message.delete()

    except Exception as e:
        print(f"Mute error: {str(e)}")
        await message.reply("❌ Failed to mute user. Make sure I have proper permissions!")



@Client.on_message(filters.command(["unmute", "dunmute"]) & filters.group)
async def unmute_user(client: Client, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id, client):
        return await message.reply("🚫 Only admins can use this command!")
    
    if len(message.command) == 1 and not message.reply_to_message:
        return await message.reply("Reply to a user's message or provide username/id to unmute")
    
    try:
        user_id = message.reply_to_message.from_user.id if message.reply_to_message else int(message.command[1])
        
        # Set default chat permissions
        permissions = ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_polls=True,
            can_add_web_page_previews=True,
            can_invite_users=True,
            can_pin_messages=False
        )
        
        await client.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=user_id,
            permissions=permissions
        )
        
        user = await client.get_users(user_id)
        await message.reply(f"🔊 Unmuted {user.mention}")
        
        if "dunmute" in message.command[0]:
            await message.delete()
            
    except Exception as e:
        print(f"Unmute error: {str(e)}")
        await message.reply("❌ Failed to unmute user. Make sure the user exists and I have proper permissions!")

async def send_periodic_message(client, group_id, message_text, interval):
    while True:
        try:
            await client.send_message(
                chat_id=group_id,
                text=message_text
            )
            print(f"✅ Message sent to {group_id}")
            await asyncio.sleep(interval)
        except Exception as e:
            print(f"Send error: {e}")
            await asyncio.sleep(60)


async def send_periodic_message(client, group_id, message_text, interval):
    while True:
        try:
            await client.send_message(chat_id=group_id, text=message_text)
            print(f"✅ Message sent to group {group_id}")
            
            # Update last sent time in database
            await group_spam.update_one(
                {'group_id': group_id},
                {'$set': {'last_sent': datetime.now(IST)}}
            )
            
        except Exception as e:
            print(f"❌ Failed to send to group {group_id}: {e}")
            
        await asyncio.sleep(interval)

@Client.on_message(filters.command("startmsg") & filters.private)
async def start_messages(client, message):
    try:
        # Get all stored messages and groups
        stored_configs = await group_spam.find().to_list(length=None)
        
        if not stored_configs:
            return await message.reply_text("No messages configured. Use /groupmsg to set up first!")

        # Start periodic tasks for each configured group
        for config in stored_configs:
            group_id = config['group_id']
            
            if group_id in active_tasks:
                continue  # Skip if already running
                
            task = asyncio.create_task(send_periodic_message(
                client=client,
                group_id=group_id,
                message_text=config['message'],
                interval=600  # 10 minutes
            ))
            active_tasks[group_id] = task
            
        await message.reply_text(f"✅ Started periodic messages for {len(stored_configs)} groups")
        
    except Exception as e:
        print(f"Error starting messages: {e}")
        await message.reply_text("Failed to start messages")

@Client.on_message(filters.command("stopmsg") & filters.private)
async def stop_messages(client, message):
    try:
        for group_id, task in active_tasks.items():
            task.cancel()
        active_tasks.clear()
        await message.reply_text("✅ Stopped all periodic messages")
    except Exception as e:
        print(f"Error stopping messages: {e}")
        await message.reply_text("Failed to stop messages")

async def send_periodic_message(client, group_id, message_text, interval):
    while True:
        try:
            await client.send_message(
                chat_id=group_id,
                text=message_text
            )
            print(f"✅ Message sent to group {group_id}")
            
            # Update last sent time
            await group_spam.update_one(
                {'group_id': group_id},
                {'$set': {'last_sent': datetime.now(IST)}}
            )
            
        except Exception as e:
            print(f"❌ Failed to send to group {group_id}: {e}")
            
        await asyncio.sleep(interval)



@Client.on_message(filters.command("groupmsg") & filters.private)
async def set_group_message(client, message: Message):
    # First ask for group ID
    await message.reply_text("Send the group ID:", reply_markup=ForceReply())
    
    try:
        group_id_msg = await client.listen(message.chat.id, timeout=60)
        group_id = int(group_id_msg.text)
        
        # Now ask for the message
        await message.reply_text("Send the message you want to set:", reply_markup=ForceReply())
        msg_response = await client.listen(message.chat.id, timeout=300)
        
        # Store in database
        await group_spam.update_one(
            {'group_id': group_id},
            {
                '$set': {
                    'message': msg_response.text,
                    'updated_at': datetime.now(IST),
                    'updated_by': message.from_user.id
                }
            },
            upsert=True
        )
        
        # Confirm storage with inline button to view messages
        await message.reply_text(
            "✅ Message stored successfully!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("View Messages", callback_data="view_msgs")
            ]])
        )
        
    except asyncio.TimeoutError:
        await message.reply_text("❌ Time limit exceeded. Please try again.")
    except ValueError:
        await message.reply_text("❌ Invalid group ID. Please send a valid number.")

@Client.on_message(filters.command("listmsg") & filters.private)
async def list_stored_messages(client, message):
    stored_msgs = await group_spam.find().to_list(length=None)
    
    if not stored_msgs:
        return await message.reply_text("No messages stored yet")
    
    response = "📝 Stored Messages:\n\n"
    for msg in stored_msgs:
        response += f"Group ID: {msg['group_id']}\n"
        response += f"Message:\n{msg['message']}\n"
        response += f"Updated: {msg['updated_at']}\n"
        response += "─────────────────\n"
    
    await message.reply_text(response)

@Client.on_message(filters.command("delgroup") & filters.private)
async def delete_group(client, message):
    try:
        # First show existing groups
        stored_groups = await group_spam.find().to_list(length=None)
        if not stored_groups:
            return await message.reply_text("No groups configured to delete")
            
        # Display groups
        groups_text = "Current groups:\n\n"
        for group in stored_groups:
            groups_text += f"ID: {group['group_id']}\n"
        groups_text += "\nSend the group ID you want to delete:"
        
        await message.reply_text(groups_text, reply_markup=ForceReply())
        
        # Get group ID to delete
        response = await client.listen(message.chat.id, timeout=60)
        group_id = int(response.text)
        
        # Stop task if running
        if group_id in active_tasks:
            active_tasks[group_id].cancel()
            del active_tasks[group_id]
        
        # Delete from database
        result = await group_spam.delete_one({'group_id': group_id})
        
        if result.deleted_count > 0:
            await message.reply_text(f"✅ Group {group_id} deleted successfully")
        else:
            await message.reply_text("Group not found in database")
            
    except asyncio.TimeoutError:
        await message.reply_text("Time limit exceeded. Try again.")
    except ValueError:
        await message.reply_text("Please provide a valid group ID")