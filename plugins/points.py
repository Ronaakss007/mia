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

owner_conversations = {}
@Client.on_message(filters.command('addpoint') & filters.private & filters.user(OWNER_ID))
async def add_point(client: Client, message: Message):
    user_id = message.from_user.id

    # Ask for target user ID or 'all' to add points to all users
    await message.reply("🕶️ <b>Iᴅᴇɴᴛɪғʏ Tᴀʀɢᴇᴛ:</b>\n\n"
                        "🔰 <i>Enter the User ID to credit points, or type</i> <code>all</code> <i>to distribute globally.</i> 🔗",
                        parse_mode=ParseMode.HTML)

    response = await client.listen(message.chat.id, timeout=60)  # Listen for user input
    target_input = response.text.strip().lower()

    # Handle 'all' case
    if target_input == 'all':
        users = await user_data.find({}).to_list(length=None)  # Get all users

        # Ask for points to add
        await message.reply("💾 <b>Dᴇғɪɴᴇ Tʀᴀɴsғᴇʀ Aᴍᴏᴜɴᴛ:</b>\n\n"
                            "🔗 <i>Enter the number of credits to deploy:</i>",
                            parse_mode=ParseMode.HTML)

        response = await client.listen(message.chat.id, timeout=60)  

        try:
            points_to_add = int(response.text.strip())
        except ValueError:
            await message.reply("❌ Iɴᴠᴀʟɪᴅ Fᴏʀᴍᴀᴛ! Eɴᴛᴇʀ ɴᴜᴍᴇʀɪᴄ ᴠᴀʟᴜᴇs ᴏɴʟʏ.", parse_mode=ParseMode.HTML)
            return

        # Progress tracking
        progress_msg = await message.reply("⏳ Dᴇᴘʟᴏʏɪɴɢ Cʀᴇᴅɪᴛs... Sᴛᴀʏ Tᴜɴᴇᴅ.", parse_mode=ParseMode.HTML)

        total_users = len(users)
        successful, blocked_users, deleted_accounts, unsuccessful = 0, 0, 0, 0

        for index, user in enumerate(users):
            user_id = user.get('_id')

            try:
                if user.get('status') == 'blocked':
                    blocked_users += 1
                    continue
                if user.get('status') == 'deleted':
                    deleted_accounts += 1
                    continue

                new_purchased_points = user.get('purchased_points', 0) + points_to_add

                await user_data.update_one({'_id': user_id}, {'$set': {'purchased_points': new_purchased_points}})
                successful += 1

                # Send user confirmation
                await client.send_message(user_id,
                                          f"🕶️ <b>ACCESS GRANTED, Oᴘᴇʀᴀᴛᴏʀ!</b> 🕶️\n\n"
                                          f"🔰 <b>Dᴀᴛᴀ Pᴀᴄᴋᴇᴛ Rᴇᴄᴇɪᴠᴇᴅ:</b> <code>{points_to_add}</code> ᴄʀᴇᴅɪᴛs\n"
                                          f"💾 <b>Wᴀʟʟᴇᴛ Uᴘᴅᴀᴛᴇᴅ:</b> <code>{new_purchased_points}</code> ᴄʀᴇᴅɪᴛs\n"
                                          f"📟 <b>Sᴛᴀᴛᴜs:</b> ✅ Eɴᴄʀʏᴘᴛᴇᴅ & Vᴇʀɪғɪᴇᴅ\n\n"
                                          f"🕸️ Tʜᴇ Sʏsᴛᴇᴍ ɪs Wᴀᴛᴄʜɪɴɢ... Sᴛᴀʏ Lᴏᴡ. Sᴛᴀʏ Wᴏʀᴛʜʏ. 🔗",
                                          parse_mode=ParseMode.HTML)

            except Exception as e:
                unsuccessful += 1
                print(f"Error updating user {user_id}: {e}")

            # Update progress message
            progress_percent = (index + 1) / total_users
            filled_length = int(progress_percent * 40)
            bar = '█' * filled_length + '-' * (40 - filled_length)

            try:
                await client.edit_message_text(chat_id=message.chat.id, message_id=progress_msg.message_id,
                                               text=f"<b>Pʀᴏɢʀᴇss:</b>\n{bar} {progress_percent:.1%}",
                                               parse_mode=ParseMode.HTML)
            except Exception as e:
                print(f"Error updating progress message: {e}")

        # Summary
        summary = (f"📜 <b>Oᴘᴇʀᴀᴛɪᴏɴ Cᴏᴍᴘʟᴇᴛᴇᴅ!</b>\n\n"
                   f"🔰 <b>Tᴏᴛᴀʟ Uꜱᴇʀꜱ:</b> {total_users}\n"
                   f"✅ <b>Sᴜᴄᴄᴇꜱꜱғᴜʟ:</b> {successful}\n"
                   f"🚫 <b>Bʟᴏᴄᴋᴇᴅ:</b> {blocked_users}\n"
                   f"💀 <b>Dᴇʟᴇᴛᴇᴅ Aᴄᴄᴏᴜɴᴛꜱ:</b> {deleted_accounts}\n"
                   f"⚠️ <b>Fᴀɪʟᴜʀᴇꜱ:</b> {unsuccessful}\n\n"
                   f"🕸️ <i>Sʏꜱᴛᴇᴍ Sᴇᴄᴜʀᴇ.</i> 🔗")

        await message.reply(summary, parse_mode=ParseMode.HTML)

    else:
        try:
            target_user_id = int(target_input)
        except ValueError:
            await message.reply("❌ Iɴᴠᴀʟɪᴅ ID! Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ɴᴜᴍᴇʀɪᴄ ᴠᴀʟᴜᴇ.", parse_mode=ParseMode.HTML)
            return

        await message.reply("💾 <b>Dᴇғɪɴᴇ Tʀᴀɴsғᴇʀ Aᴍᴏᴜɴᴛ:</b>\n\n"
                            "🔗 <i>Enter the number of credits to deploy:</i>",
                            parse_mode=ParseMode.HTML)

        response = await client.listen(message.chat.id, timeout=60)

        try:
            points_to_add = int(response.text.strip())
        except ValueError:
            await message.reply("❌ Iɴᴠᴀʟɪᴅ Fᴏʀᴍᴀᴛ! Eɴᴛᴇʀ ɴᴜᴍᴇʀɪᴄ ᴠᴀʟᴜᴇs ᴏɴʟʏ.", parse_mode=ParseMode.HTML)
            return

        user = await user_data.find_one({'_id': target_user_id})
        if not user:
            await message.reply(f"🚫 Uꜱᴇʀ {target_user_id} ɴᴏᴛ ꜰᴏᴜɴᴅ.", parse_mode=ParseMode.HTML)
            return

        new_purchased_points = user.get('purchased_points', 0) + points_to_add
        await user_data.update_one({'_id': target_user_id}, {'$set': {'purchased_points': new_purchased_points}})

        await message.reply(f"✅ <b>Operation Successful:</b>\n\n"
                            f"🕶️ <b>{points_to_add} ᴄʀᴇᴅɪᴛs</b> ᴅᴇᴘʟᴏʏᴇᴅ ᴛᴏ <b>{target_user_id}</b>.\n"
                            f"💰 <b>Nᴇᴡ Bᴀʟᴀɴᴄᴇ:</b> <code>{new_purchased_points}</code>",
                            parse_mode=ParseMode.HTML)

        await client.send_message(target_user_id,
                                  f"🕶️ <b>ACCESS GRANTED, Oᴘᴇʀᴀᴛᴏʀ!</b> 🕶️\n\n"
                                  f"🔰 <b>Dᴀᴛᴀ Pᴀᴄᴋᴇᴛ Rᴇᴄᴇɪᴠᴇᴅ:</b> <code>{points_to_add}</code> ᴄʀᴇᴅɪᴛs\n"
                                  f"💾 <b>Wᴀʟʟᴇᴛ Uᴘᴅᴀᴛᴇᴅ:</b> <code>{new_purchased_points}</code> ᴄʀᴇᴅɪᴛs\n"
                                  f"📟 <b>Sᴛᴀᴛᴜs:</b> ✅ Eɴᴄʀʏᴘᴛᴇᴅ & Vᴇʀɪғɪᴇᴅ 🔗",
                                  parse_mode=ParseMode.HTML)


@Client.on_message(filters.command('subpoint') & filters.private & filters.user(OWNER_ID))
async def sub_point(client: Client, message: Message):
    user_id = message.from_user.id

    # Ask for target user ID or 'all' to subtract points from all users
    await message.reply("Please enter the user ID to subtract points from, or type 'all' to subtract points from all users:")

    response = await client.listen(message.chat.id, timeout=60)  # Listen for user input

    target_input = response.text.strip().lower()

    # Handle 'all' case
    if target_input == 'all':
        # Fetch all users from the database
        users = await user_data.find({}).to_list(length=None)  # Get all users from the database

        # Ask for points to subtract
        await message.reply("Please enter the number of points to subtract:")
        response = await client.listen(message.chat.id, timeout=60)  # Listen for user input

        try:
            points_to_subtract = int(response.text.strip())  # Convert to integer
        except ValueError:
            await message.reply("Invalid points format. Please try again.")
            return

        # Initialize progress message
        progress_msg = await message.reply("Processing users... 0% completed.")

        # Variables to track statuses
        total_users = len(users)
        successful = 0
        blocked_users = 0
        deleted_accounts = 0
        unsuccessful = 0

        # Loop through users to subtract points
        for index, user in enumerate(users):
            user_id = user.get('_id')

            try:
                # If the user is blocked or deleted, skip them
                if user.get('status') == 'blocked':  # Example check for blocked users
                    blocked_users += 1
                    continue
                if user.get('status') == 'deleted':  # Example check for deleted accounts
                    deleted_accounts += 1
                    continue

                # Get the user's points data
                referral_points = user.get('referral_points', 0)
                purchased_points = user.get('purchased_points', 0)

                # Ensure points to subtract doesn't exceed available purchased points
                if points_to_subtract > purchased_points:
                    unsuccessful += 1
                    continue

                new_purchased_points = purchased_points - points_to_subtract

                # Update the database
                await user_data.update_one(
                    {'_id': user_id},
                    {'$set': {'purchased_points': new_purchased_points}}
                )

                successful += 1
                # Send confirmation to the user
                await client.send_message(user_id, f"❌ {points_to_subtract} points have been subtracted from your balance. Your new total is {new_purchased_points} purchased points.")

            except Exception as e:
                unsuccessful += 1
                print(f"Error updating user {user_id}: {e}")

            # Calculate the progress percentage
            progress_percent = (index + 1) / total_users
            filled_length = int(progress_percent * 40)  # Length of the filled part (based on 40 segments)
            bar = '█' * filled_length + '-' * (40 - filled_length)

            # Update progress message with the custom bar
            try:
                await client.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=progress_msg.message_id,
                    text=f"<b>Progress:</b>\n{bar} {progress_percent:.1%}"
                )
            except Exception as e:
                print(f"Error updating progress message: {e}")

        # Send summary message
        summary = f"""
        Total Users: {total_users}
        Successful: {successful}
        Blocked Users: {blocked_users}
        Deleted Accounts: {deleted_accounts}
        Unsuccessful: {unsuccessful}
        """

        await message.reply(summary)

    else:
        # Subtract points from a specific user (if not 'all')
        try:
            target_user_id = int(target_input)  # Convert to integer
        except ValueError:
            await message.reply("Invalid user ID format. Please try again.")
            return

        # Fetch the user from the database
        user = await user_data.find_one({'_id': target_user_id})
        if not user:
            await message.reply(f"User with ID {target_user_id} not found.")
            return

        # Get the user's points data
        referral_points = user.get('referral_points', 0)
        purchased_points = user.get('purchased_points', 0)
        total_points = referral_points + purchased_points  # Calculate total points

        # Show the user their current balance
        balance_message = (
            f"📊 User ID: {target_user_id}\n"
            f"💼 Referral points: {referral_points}\n"
            f"💰 Purchased points: {purchased_points}\n"
            f"🎯 Total points: {total_points}\n\n"
            "Please enter the number of points to subtract:"
        )
        await message.reply(balance_message)

        # Listen for points to subtract
        response = await client.listen(message.chat.id, timeout=60)  # Listen for user input

        try:
            points_to_subtract = int(response.text.strip())  # Convert to integer
        except ValueError:
            await message.reply("Invalid points format. Please try again.")
            return

        # Ensure points to subtract doesn't exceed available purchased points
        if points_to_subtract > purchased_points:
            await message.reply(f"Cannot subtract {points_to_subtract} points as the user only has {purchased_points} purchased points.")
            return

        new_purchased_points = purchased_points - points_to_subtract

        # Update the database
        await user_data.update_one(
            {'_id': target_user_id},
            {'$set': {'purchased_points': new_purchased_points}}
        )

        # Send a confirmation message to the owner
        await message.reply(f"Successfully subtracted {points_to_subtract} points from user {target_user_id}. New total purchased points: {new_purchased_points}")

        # Send a confirmation to the target user
        try:
            await client.send_message(target_user_id, f"❌ {points_to_subtract} points have been subtracted from your balance. Your new total is {new_purchased_points} purchased points.")
        except Exception as e:
            print(f"Could not send message to user {target_user_id}. Error: {e}")
