import asyncio
from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait, MediaEmpty, RPCError
from datetime import datetime, timedelta
from database.database import *
from bot import Bot
from pymongo import InsertOne

from config import *
from helper_func import *

sent_media_history = {}
last_command_time = {}
temp_media_store = {}

MEDIA_CATEGORIES = {
    'Cutie': {'pic': 1, 'video': 2, 'emoji': '🔥'},
    'Hard': {'pic': 1, 'video': 2, 'emoji': '💪'},
    # 'Snap': {'pic': 2, 'video': 3, 'emoji': '📸'},
    # 'Viral': {'pic': 2, 'video': 3, 'emoji': '🌟'},
    'premium': {'pic': 1, 'video': 2, 'emoji': '👑'}
}

@Bot.on_callback_query(filters.regex(r"^bulk_store_(.+)$"))
async def handle_bulk_storage(client: Bot, callback: CallbackQuery):
    # Random effect
    user_id = callback.from_user.id
    category = callback.data.split("_")[2]
    
    if user_id in temp_media_store:
        stored_count = 0
        timestamp = datetime.utcnow().timestamp()
        
        bulk_operations = []
        
        # Prepare bulk operations for photos
        for file_id in temp_media_store[user_id]['photo']:
            bulk_operations.append(InsertOne({
                "file_id": file_id,
                "type": "photo",
                "category": category,
                "timestamp": timestamp
            }))
            stored_count += 1
            
        # Prepare bulk operations for videos
        for file_id in temp_media_store[user_id]['video']:
            bulk_operations.append(InsertOne({
                "file_id": file_id,
                "type": "video",
                "category": category,
                "timestamp": timestamp
            }))
            stored_count += 1
        
        # Execute bulk operation
        if bulk_operations:
            await video_messages_collection.bulk_write(bulk_operations)
        
        # Clear temporary storage
        temp_media_store[user_id] = {'photo': [], 'video': []}
        
        await callback.message.edit_text(
            f"✅ Successfully stored {stored_count} media files in {category.title()} category!"
        )

@Bot.on_callback_query(filters.regex(r"^view_(photo|video)_(.+)$"))
async def handle_media_view(client: Bot, callback: CallbackQuery):
    try:
        # Extract media type and category from callback data
        media_type, category = callback.data.split("_")[1:]

        # Fetch user info
        user_id = callback.from_user.id
        user = await user_data.find_one({'_id': user_id})

        if not user:
            await callback.answer("❌ You are not in the database. Please start the bot first!", show_alert=True)
            return

        is_premium = user.get('premium', False)
        premium_badge = "👑 Pʀᴇᴍɪᴜᴍ" if is_premium else "⭐️ Free User"
        user_plan = await get_user_plan_group(user_id)

        # Check if category exists in MEDIA_CATEGORIES
        category_data = MEDIA_CATEGORIES.get(category)
        if not category_data:
            await callback.answer(f"⚠️ Invalid category: {category}!", show_alert=True)
            return

        # Determine media type key
        media_key = 'pic' if media_type == 'photo' else 'video'
        points_needed = category_data.get(media_key)

        if points_needed is None:
            await callback.answer(f"⚠️ {media_type.capitalize()} not available for {category}!", show_alert=True)
            return

        # Fetch user points and free media limits
        total_points = user.get('purchased_points', 0) + user.get('referral_points', 0)
        free_media_count = user.get('free_media_count', 0)
        user_plan_limit = FREE_MEDIA_LIMIT.get(user_plan, 2)  # Default limit = 2

        # Check if user can access the media
        if free_media_count >= user_plan_limit and total_points < points_needed:
            await callback.answer("⚠️ Not enough points! Buy points or refer friends.", show_alert=True)
            return

        # Fetch media
        media = await get_unique_media(media_type, category, user_id)
        if not media:
            await callback.answer("🚫 No content available in this category!", show_alert=True)
            return

        # Send a wait message
        wait_message = await callback.message.reply_text("⏳ Please wait...")
        await asyncio.sleep(2)
        await wait_message.delete()

        # Determine target chat
        target_chat = user_id if callback.message.chat.type == "private" else callback.message.chat.id

        # Prepare caption
        caption = f"""{'⚡️ Hᴀᴄᴋᴇᴅ Pʜᴏᴛᴏ' if media_type == 'photo' else '😈 Cʏʙᴇʀ Vɪᴅᴇᴏ'} Rᴇǫᴜᴇsᴛ 🛜  
👤 **{callback.from_user.mention}** | {premium_badge}  
🛡️ **Aᴄᴄᴇss Lᴇᴠᴇʟ:** {category.title()}  
💰 **Dᴀʀᴋ Cʀᴇᴅɪᴛs:** {total_points}  
`{f'🚀 Eɴᴊᴏʏɪɴɢ {user_plan} ᴘᴇʀᴋs!' if is_premium else '🔓 Dᴇᴄʀʏᴘᴛ Pʀɪᴠᴀᴛᴇ Sᴇʀᴠᴇʀ - Gᴏ Pʀᴇᴍɪᴜᴍ!'}`
"""

        buttons = InlineKeyboardMarkup([[
            InlineKeyboardButton("💀 Hᴀᴄᴋ Pʀᴇᴍɪᴜᴍ", callback_data="buy_prem"),
            InlineKeyboardButton("🔄 Cʀʏᴘᴛ Cᴏɴᴠᴇʀᴛ", callback_data="redeem"),
            InlineKeyboardButton("🕵️ Dᴀʀᴋ Cʀᴇᴅɪᴛs", callback_data="buy_point")
        ]]) if not is_premium else None

        # Send the media
        sent_message = None
        try:
            if media_type == 'photo':
                sent_message = await client.send_photo(
                    chat_id=target_chat,
                    photo=media['file_id'],
                    caption=caption,
                    reply_markup=buttons,
                    # message_effect_id=int(random.choice(SUCCESS_EFFECT_IDS)) , # 🔥 Effect on message
                    protect_content=await should_protect_content(user)
                )
            else:
                sent_message = await client.send_video(
                    chat_id=target_chat,
                    video=media['file_id'],
                    caption=caption,
                    reply_markup=buttons,
                    protect_content=await should_protect_content(user)
                )
        except Exception as media_error:
            logger.error(f"Error sending media: {str(media_error)}")
            await callback.answer("⚠️ Failed to send media. Try again later!", show_alert=True)
            return

        # Update user points after successful media send
        try:
            if free_media_count < user_plan_limit:
                await user_data.update_one({'_id': user_id}, {'$inc': {'free_media_count': 1}})
            else:
                deduct_from_purchased = min(user.get('purchased_points', 0), points_needed)
                deduct_from_referral = max(points_needed - deduct_from_purchased, 0)

                await user_data.update_one(
                    {'_id': user_id},
                    {'$inc': {
                        'purchased_points': -deduct_from_purchased,
                        'referral_points': -deduct_from_referral
                    }}
                )
        except Exception as db_error:
            logger.error(f"Database error while updating points: {str(db_error)}")
            await callback.answer("⚠️ Could not update points. Contact support!", show_alert=True)
            return

        # Notify owner
        try:
            user_name = callback.from_user.username or f"{callback.from_user.first_name} {callback.from_user.last_name or ''}".strip()
            await client.send_message(
                DUMB_CHAT,
                f"📢 User {user_name} ({user_id}) accessed {media_type} from {category} category. Remaining Points: {total_points}"
            )
        except Exception as owner_notify_error:
            logger.warning(f"Failed to notify owner: {str(owner_notify_error)}")

        # Auto-delete after delay
        try:
            await asyncio.sleep(6200)
            await sent_message.delete()
        except Exception as delete_error:
            logger.warning(f"Failed to delete media after timeout: {str(delete_error)}")

    except Exception as critical_error:
        logger.critical(f"Unhandled error in media view: {str(critical_error)}")
        await callback.answer("🚨 Critical error occurred! Please try again later.", show_alert=True)


async def get_unique_media(media_type, category, user_id):
    """Get unique media with zero repetition"""
    current_time = datetime.utcnow()
    
    # Get all media IDs for this category and type
    all_media = await video_messages_collection.find({
        "type": media_type,
        "category": category
    }).to_list(None)
    
    all_media_ids = [m['file_id'] for m in all_media]
    
    if not all_media_ids:
        return None
        
    # Initialize fresh history if needed
    if user_id not in sent_media_history:
        sent_media_history[user_id] = {
            'seen': set(),
            'last_reset': current_time
        }
    
    # Reset history if all content seen
    if len(sent_media_history[user_id]['seen']) >= len(all_media_ids):
        sent_media_history[user_id] = {
            'seen': set(),
            'last_reset': current_time
        }
    
    # Get unseen media IDs
    unseen_ids = set(all_media_ids) - sent_media_history[user_id]['seen']
    
    if not unseen_ids:
        # Reset if everything seen
        sent_media_history[user_id]['seen'] = set()
        unseen_ids = set(all_media_ids)
    
    # Select random unseen media
    selected_id = random.choice(list(unseen_ids))
    sent_media_history[user_id]['seen'].add(selected_id)
    
    # Get full media document
    media = next(m for m in all_media if m['file_id'] == selected_id)
    
    return media

@Bot.on_message(filters.private & filters.command("store") & filters.user(ADMINS) & filters.media)

async def collect_media(client: Client, message: Message):
    user_id = message.from_user.id

    # Initialize or reset user store
    if user_id not in temp_media_store:
        temp_media_store[user_id] = {
            'photo': [],
            'video': [],
            'last_media_time': datetime.utcnow(),
            'message_sent': False,
            'timer': None
        }
    else:
        # Reset message_sent flag for existing users
        temp_media_store[user_id]['message_sent'] = False

    user_store = temp_media_store[user_id]

    # Store media
    if message.photo:
        user_store['photo'].append(message.photo.file_id)
    elif message.video:
        user_store['video'].append(message.video.file_id)

    async def show_category_selection():
        total_media = len(user_store['photo']) + len(user_store['video'])
        keyboard = [
            [InlineKeyboardButton(
                f"{MEDIA_CATEGORIES[category]['emoji']} {category.title()}",
                callback_data=f"bulk_store_{category}"
            )]
            for category in MEDIA_CATEGORIES.keys()
        ]

        await message.reply_text(
            f"🕶️ <b>Dᴀᴛᴀ Iɴᴊᴇᴄᴛɪᴏɴ Pᴏɪɴᴛ</b>\n\n"
            f"📂 Sᴇʟᴇᴄᴛ A Sᴇᴄᴛɪᴏɴ Tᴏ Sᴛᴏʀᴇ {total_media} Fɪʟᴇs:\n"
            f"📸 Pʜᴏᴛᴏ Dᴀᴛᴀ: {len(user_store['photo'])} Eɴᴛʀɪᴇs\n"
            f"🎥 Vɪᴅᴇᴏ Dᴀᴛᴀ: {len(user_store['video'])} Eɴᴛʀɪᴇs\n\n"
            "<i>⚡ Cʜᴏᴏsᴇ Yᴏᴜʀ Sᴛᴏʀᴀɢᴇ Dᴇꜱᴛɪɴᴀᴛɪᴏɴ</i> ⬇",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        user_store['message_sent'] = True

    async def delayed_execution():
        await asyncio.sleep(0.5)
        await show_category_selection()

    # Cancel existing timer if any
    if user_store.get('timer') and not user_store['timer'].done():
        user_store['timer'].cancel()

    # Create new timer
    user_store['timer'] = asyncio.create_task(delayed_execution())


@Bot.on_message(filters.text & filters.regex("💀 Video") | filters.command(["video", f'video@{Bot().username}'])  & (filters.private | filters.group))
async def send_random_video(client: Client, message: Message):
    try:
        settings = await get_settings()
        FORCE_SUB_CHANNELS = settings["FORCE_SUB_CHANNELS"]
        user_id = message.from_user.id
        user = await user_data.find_one({'_id': user_id})
        is_premium = user and user.get('premium', False)
        premium_badge = "👑 PREMIUM" if is_premium else "⭐️ FREE USER"
        user_plan = await get_user_plan_group(user_id)

        if message.service:
            logger.warning(f"Skipping service message in chat {message.chat.id}")
            return
        
        # Force Subscribe Check
        buttons = []
        force_text = (
            "🔰 <b>Aᴄᴄᴇss Dᴇɴɪᴇᴅ! Jᴏɪɴ Tʜᴇ Nᴇᴛᴡᴏʀᴋ</b>\n"
            "🔹 Sᴛᴇᴘ ①: Cʟɪᴄᴋ ᴏɴ ᴛʜᴇ Cʜᴀɴɴᴇʟ ʟɪɴᴋs Bᴇʟᴏᴡ\n"
            "🔹 Sᴛᴇᴘ ②: Jᴏɪɴ Aʟʟ Rᴇǫᴜɪʀᴇᴅ Cʜᴀɴɴᴇʟs\n"
            "🔹 Sᴛᴇᴘ ③: Rᴇᴛᴜʀɴ Hᴇʀᴇ ᴀɴᴅ Rᴇᴛʀʏ\n"
            "💻 Nᴇᴇᴅ Hᴇʟᴘ? Uꜱᴇ /help 🕶️\n"
        )

        temp_buttons = []

        for i, channel in enumerate(FORCE_SUB_CHANNELS):
            try:
                chat = await client.get_chat(channel)
                try:
                    member = await client.get_chat_member(channel, message.from_user.id)
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
            await message.reply_photo(
                photo=FORCE_PIC,
                caption=force_text,
                reply_markup=InlineKeyboardMarkup(buttons),
                quote=True
            )
            return

        # Show category selection for videos with 2 buttons per row
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

        # Add any remaining buttons
        if temp_row:
            keyboard.append(temp_row)

        await message.reply_text(
            "👁‍🗨 <b>Sᴇʟᴇᴄᴛ Yᴏᴜʀ Dᴇꜱᴛɪɴᴀᴛɪᴏɴ</b>\n\n"
            "🔰 Eᴀᴄʜ Cᴀᴛᴇɢᴏʀʏ Hᴏʟᴅs Uɴɪǫᴜᴇ Cᴏɴᴛᴇɴᴛ\n"
            "💎 Pᴏɪɴᴛs Aʀᴇ Rᴇǫᴜɪʀᴇᴅ Fᴏʀ Pʀᴇᴍɪᴜᴍ Fɪʟᴇꜱ\n"
            "🔥 Wᴀɴᴛ A Cᴜꜱᴛᴏᴍ Cᴀᴛᴇɢᴏʀʏ? Dᴍ @NyxKingX\n\n"
            "<i>💻 Cʟɪᴄᴋ Aɴʏ Cᴀᴛᴇɢᴏʀʏ Bᴇʟᴏᴡ ⬇</i>",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        logger.error(f"Critical error in video command: {str(e)}")
        await message.reply_text("⚠️ Something went wrong. Try again later!")

@Bot.on_message(filters.text & filters.regex("📸 Pics") | filters.command(["pic", f'pic@{Bot().username}'])  & (filters.private | filters.group))
async def send_random_pic(client: Client, message: Message):
    try:
        settings = await get_settings()
        FORCE_SUB_CHANNELS = settings["FORCE_SUB_CHANNELS"]
        user_id = message.from_user.id
        user = await user_data.find_one({'_id': user_id})
        is_premium = user and user.get('premium', False)
        premium_badge = "👑 PREMIUM" if is_premium else "⭐️ FREE USER"
        user_plan = await get_user_plan_group(user_id)
        if message.service:
            logger.warning(f"Skipping service message in chat {message.chat.id}")
            return
        
        # Force Subscribe Check
        buttons = []
        force_text = (
            "🔰 <b>Aᴄᴄᴇss Dᴇɴɪᴇᴅ! Jᴏɪɴ Tʜᴇ Nᴇᴛᴡᴏʀᴋ</b>\n"
            "🔹 Sᴛᴇᴘ ①: Cʟɪᴄᴋ ᴏɴ ᴛʜᴇ Cʜᴀɴɴᴇʟ ʟɪɴᴋs Bᴇʟᴏᴡ\n"
            "🔹 Sᴛᴇᴘ ②: Jᴏɪɴ Aʟʟ Rᴇǫᴜɪʀᴇᴅ Cʜᴀɴɴᴇʟs\n"
            "🔹 Sᴛᴇᴘ ③: Rᴇᴛᴜʀɴ Hᴇʀᴇ ᴀɴᴅ Rᴇᴛʀʏ\n"
            "💻 Nᴇᴇᴅ Hᴇʟᴘ? Uꜱᴇ /help 🕶️\n"
        )

        temp_buttons = []

        for i, channel in enumerate(FORCE_SUB_CHANNELS):
            try:
                chat = await client.get_chat(channel)
                try:
                    member = await client.get_chat_member(channel, message.from_user.id)
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
            await message.reply_photo(
                photo=FORCE_PIC,
                caption=force_text,
                reply_markup=InlineKeyboardMarkup(buttons),
                quote=True
            )
            return

        # Show category selection for photos with 2 buttons per row
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

        # Add any remaining buttons
        if temp_row:
            keyboard.append(temp_row)

        await message.reply_text(
            "👁‍🗨 <b>Sᴇʟᴇᴄᴛ Yᴏᴜʀ Dᴇꜱᴛɪɴᴀᴛɪᴏɴ</b>\n\n"
            "🔰 Eᴀᴄʜ Cᴀᴛᴇɢᴏʀʏ Hᴏʟᴅs Uɴɪǫᴜᴇ Cᴏɴᴛᴇɴᴛ\n"
            "💎 Pᴏɪɴᴛs Aʀᴇ Rᴇǫᴜɪʀᴇᴅ Fᴏʀ Pʀᴇᴍɪᴜᴍ Fɪʟᴇꜱ\n"
            "🔥 Wᴀɴᴛ A Cᴜꜱᴛᴏᴍ Cᴀᴛᴇɢᴏʀʏ? Dᴍ @NyxKingX\n\n"
            "<i>💻 Cʟɪᴄᴋ Aɴʏ Cᴀᴛᴇɢᴏʀʏ Bᴇʟᴏᴡ ⬇</i>",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        logger.error(f"Critical error in pic command: {str(e)}")
        await message.reply_text("⚠️ Something went wrong. Try again later!")

        

@Bot.on_message(filters.command('listcontent') & filters.user(ADMINS))
async def list_stored_content(client: Client, message: Message):
    stats = {}
    for category in MEDIA_CATEGORIES:
        photos = await video_messages_collection.count_documents({"type": "photo", "category": category})
        videos = await video_messages_collection.count_documents({"type": "video", "category": category})
        stats[category] = {"photos": photos, "videos": videos}

    text = "📊 Stored Content Stats:\n\n"
    for cat, data in stats.items():
        text += f"{MEDIA_CATEGORIES[cat]['emoji']} {cat.title()}\n"
        text += f"📸 Photos: {data['photos']}\n"
        text += f"🎥 Videos: {data['videos']}\n\n"

    await message.reply_text(text)

@Bot.on_message(filters.command('delcontent') & filters.user(ADMINS))
async def delete_category_content(client: Client, message: Message):
    args = message.text.split(maxsplit=2)
    
    if len(args) != 3:
        await message.reply_text(
            "⚠️ Usage: `/delcontent [category] [type]`\n"
            "📌 Types: `photo`, `video`, `all`\n"
            "✅ Example: `/delcontent desi photo`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    category = args[1].title()  # Convert to Title Case for consistency
    content_type = args[2].lower()

    # Validate category
    if category not in MEDIA_CATEGORIES:
        valid_categories = ", ".join(MEDIA_CATEGORIES.keys())
        await message.reply_text(f"❌ Invalid category!\n\n✅ Available categories: `{valid_categories}`", parse_mode=ParseMode.MARKDOWN)
        return

    # Prepare MongoDB query
    query = {"category": category.lower()}  # Store in lowercase for consistency
    if content_type != "all":
        if content_type not in ["photo", "video"]:
            await message.reply_text("❌ Invalid type! Choose from `photo`, `video`, or `all`.", parse_mode=ParseMode.MARKDOWN)
            return
        query["type"] = content_type

    # Confirm deletion
    result = await video_messages_collection.delete_many(query)
    deleted_count = result.deleted_count

    if deleted_count > 0:
        await message.reply_text(f"✅ Successfully deleted `{deleted_count}` {content_type if content_type != 'all' else 'media'} files from `{category}` category.", parse_mode=ParseMode.MARKDOWN)
    else:
        await message.reply_text(f"⚠️ No matching content found in `{category}` for `{content_type}`.", parse_mode=ParseMode.MARKDOWN)

@Bot.on_message(filters.command('findcontent') & filters.user(ADMINS))
async def find_content(client: Client, message: Message):
    args = message.text.split()
    if len(args) != 3:
        await message.reply_text(
            "Usage: /findcontent [category] [type]\n"
            "Types: photo, video\n"
            "Example: /findcontent desi photo"
        )
        return

    category = args[1].lower()
    content_type = args[2].lower()

    media_items = await video_messages_collection.find({
        "category": category,
        "type": content_type
    }).to_list(length=None)

    for i, item in enumerate(media_items):
        if content_type == "photo":
            sent_msg = await client.send_photo(
                message.chat.id,
                item['file_id'],
                caption=f"Media #{i+1}\nCategory: {category}"
            )
        else:
            sent_msg = await client.send_video(
                message.chat.id,
                item['file_id'], 
                caption=f"Media #{i+1}\nCategory: {category}"
            )

        # Using shorter callback data
        await sent_msg.reply_text(
            "Delete this media?",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    "🗑 Delete",
                    callback_data=f"d_{i}"  # Shorter callback data
                )
            ]])
        )
        
        # Store file_id mapping temporarily
        if not hasattr(client, 'temp_file_ids'):
            client.temp_file_ids = {}
        client.temp_file_ids[str(i)] = item['file_id']

@Bot.on_callback_query(filters.regex(r"^d_(\d+)$"))
async def delete_specific_media(client: Bot, callback: CallbackQuery):
    index = callback.data.split("_")[1]
    file_id = client.temp_file_ids.get(index)
    
    if file_id:
        result = await video_messages_collection.delete_one({"file_id": file_id})
        if result.deleted_count > 0:
            await callback.message.edit_text("✅ Media deleted successfully!")
            del client.temp_file_ids[index]
        else:
            await callback.message.edit_text("❌ Media not found!")


async def reset_daily_free_media(client):
    """Reset the free media count for all users daily."""
    while True:
        try:
            # Reset free_media_count to 0 for all users
            result = await user_data.update_many(
                {},  # Match all documents
                {"$set": {"free_media_count": 0}}
            )
            
            # Log the reset
            print(f"🔄 Reset free media count for {result.modified_count} users")
            
            # Notify owner
            if DUMB_CHAT:
                await client.send_message(
                    DUMB_CHAT, 
                    f"📢 Daily free media limit reset for {result.modified_count} users"
                )

        except Exception as e:
            print(f"❌ Error in reset_daily_free_media: {str(e)}")
            if DUMB_CHAT:
                try:
                    await client.send_message(DUMB_CHAT, f"⚠️ Error in reset_daily_free_media: {str(e)}")
                except Exception as msg_error:
                    print(f"Failed to send error message: {str(msg_error)}")
        
        # Calculate time until next reset (midnight UTC)
        now = datetime.utcnow()
        tomorrow = now + timedelta(days=1)
        midnight = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 0, 0)
        seconds_until_midnight = (midnight - now).total_seconds()
        
        # Sleep until midnight
        await asyncio.sleep(seconds_until_midnight)
