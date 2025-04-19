

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot import Bot
from config import ADMINS
from database.database import *
import logging
from helper_func import *

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)  # Create a logger instance

@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command('batch'))
async def batch(client: Client, message: Message):
    while True:
        try:
            first_message = await client.ask(text="Forward the First Message from DB Channel ⏩ (with Quotes)..\n\nor Send the DB Channel Post Link\nUse /sbatch for stopping.", chat_id=message.from_user.id, filters=(filters.forwarded | (filters.text & ~filters.forwarded)), timeout=60)
        except Exception as e:
            print(e)
            return
        if first_message.text == "/sbatch":
            return
        f_msg_id = await get_message_id(client, first_message)
        
        if f_msg_id:
            break
        else:
            await first_message.reply("❌ Error\n\nthis Forwarded Post is not from my DB Channel or this Link is taken from DB Channel", quote=True)
            continue
    while True:
        try:
            second_message = await client.ask(text="Forward the Last Message from DB Channel ⏩ (with Quotes)..\nor Send the DB Channel Post link\nUse /sbatch for stopping.", chat_id=message.from_user.id, filters=(filters.forwarded | (filters.text & ~filters.forwarded)), timeout=60)
        except:
            return
        if second_message.text == "/sbatch":
            return
        s_msg_id = await get_message_id(client, second_message)
        if s_msg_id:
            break
        else:
            await second_message.reply("❌ Error\n\nthis Forwarded Post is not from my DB Channel or this Link is taken from DB Channel", quote=True)
            continue

    # Ask for the file name
    file_name_message = await client.ask(
        text="Enter the file name:",
        chat_id=message.from_user.id,
        filters=filters.text,
        timeout=60
    )
    file_name = file_name_message.text.strip()
        
    string = f"get-{f_msg_id * abs(client.db_channel.id)}-{s_msg_id * abs(client.db_channel.id)}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])

    # Store the hash in the database
    await link_data.insert_one({
        'hash': base64_string,
        'clicks': 0,
        'file_name': file_name
    })

    await second_message.reply_text(
        # f"<blockquote><b>Jᴜsᴛ Fᴏʀ Fᴜɴ Exᴄʟᴜsɪᴠᴇ 💕</b></blockquote>\n"
        f"<b>{file_name} | NʏxKɪɴɢX 🔥</b>\n"
        f"<blockquote><b>Fɪʟᴇ ʟɪɴᴋ:</b>\n<a href='{link}'>NʏxKɪɴɢX Sᴘᴇᴄɪᴀʟ Lɪɴᴋ 🤖</a></blockquote>\n"
        f"<b>Nᴏ Tᴏᴋᴇɴ Fʀᴇᴇ Fʀᴇᴇ</b>\n",
        quote=True,
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )

    # # Send alert to OWNER_ID
    # owner_alert = (
    #     f"📢 Usᴇʀ Gᴇɴᴇʀᴀᴛᴇᴅ Lɪɴᴋ:\n"
    #     f"👤 Usᴇʀ : [{message.from_user.first_name}](tg://user?id={message.from_user.id}) ({message.from_user.id})\n"
    #     f"👾 Fɪʟᴇ Nᴀᴍᴇ: {file_name}\n"
    #     f"🔗 Lɪɴᴋ: [Access Link]({link})"
    # )
    # await client.send_message(OWNER_ID, owner_alert, parse_mode=ParseMode.MARKDOWN)

@Bot.on_message(filters.private & filters.command('link'))
async def genlink_command(client: Client, message: Message):
    print("Received /genlink command")  # Add this line to log when the command is triggered
    while True:
        try:
            channel_message = await client.ask(
                text="🎯 Fᴏʀᴡᴀʀᴅ ᴀ ᴘᴏsᴛ ғʀᴏᴍ ᴛʜᴇ Dʙ Cʜᴀɴɴᴇʟ ⏩\n\nᴏʀ 🔗 sᴇɴᴅ ᴛʜᴇ ᴘᴏsᴛ ʟɪɴᴋ.\n\n💬 Tʏᴘᴇ /sgen ᴛᴏ sᴛᴏᴘ.", 
                chat_id=message.from_user.id, 
                filters=(filters.forwarded | filters.text), 
                timeout=60
            )
        except asyncio.TimeoutError:
            await message.reply("⌛ Tɪᴍᴇ'ꜱ ᴜᴘ! Tʀʏ ᴀɢᴀɪɴ 🔁")
            return
        except Exception as e:
            await message.reply(f"⚠️ Eʀʀᴏʀ: {str(e)}")
            return
        
        if channel_message.text == "/sgen":
            return
        
        msg_id = await get_message_id(client, channel_message)
        if msg_id:
            break
        else:
            await channel_message.reply("❌ Iɴᴠᴀʟɪᴅ Pᴏsᴛ ⚠️\n\nPʟᴇᴀsᴇ sᴇɴᴅ ᴀ ᴠᴀʟɪᴅ ᴘᴏsᴛ ғʀᴏᴍ ᴛʜᴇ Dʙ Cʜᴀɴɴᴇʟ.", quote=True)
            continue
    
    # Ask for the file name
    file_name_message = await client.ask(
        text="📝 Eɴᴛᴇʀ ᴀ ɴᴀᴍᴇ ғᴏʀ ᴛʜɪs ғɪʟᴇ:",
        chat_id=message.from_user.id,
        filters=filters.text,
        timeout=60
    )
    file_name = file_name_message.text.strip()

    # Ensure the encoding function works
    base64_string = await encode(f"get-{msg_id * abs(client.db_channel.id)}")
    link = f"https://t.me/{client.username}?start={base64_string}"
    
    # Inline button
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(f"🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])

    # Store the hash in the database
    await link_data.insert_one({
        'hash': base64_string,
        'clicks': 0,
        'file_name': file_name
    })

    # Send the generated link
    await channel_message.reply_text(
# f"<blockquote><b>Jᴜsᴛ Fᴏʀ Fᴜɴ Exᴄʟᴜsɪᴠᴇ 💕</b></blockquote>\n"
        f"<b>{file_name} | NʏxKɪɴɢX 🔥</b>\n"
        f"<blockquote><b>Fɪʟᴇ ʟɪɴᴋ:</b>\n<a href='{link}'>NʏxKɪɴɢX Sᴘᴇᴄɪᴀʟ Lɪɴᴋ 🤖</a></blockquote>\n"
        f"<b>Nᴏ Tᴏᴋᴇɴ Fʀᴇᴇ Fʀᴇᴇ</b>\n",
        quote=True,
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )
    

@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command('accesslink'))
async def link_generator(client: Client, message: Message):
    while True:
        try:
            channel_message = await client.ask(
                text="Forward the message from the DB Channel ⏩ (with Quotes)\n"
                     "or Send the DB Channel Post link\n"
                     "Type /sgen to stop.",
                chat_id=message.from_user.id,
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                timeout=60
            )
        except Exception:
            return

        if channel_message.text == "/sgen":
            return

        msg_id = await get_message_id(client, channel_message)

        if msg_id:
            logger.debug(f"✅ Retrieved msg_id: {msg_id}")
            break
        else:
            logger.error("❌ Message is not from the DB Channel.")
            await channel_message.reply("❌ Error\n\nThis message is not from the DB Channel.", quote=True)
            continue

    try:
        file_name_message = await client.ask(
            text="Enter the file name:",
            chat_id=message.from_user.id,
            filters=filters.text,
            timeout=60
        )
        file_name = file_name_message.text.strip()

        points_message = await client.ask(
            text="Enter the required points to access this file:",
            chat_id=message.from_user.id,
            filters=filters.text,
            timeout=60
        )
        required_points = int(points_message.text)
    except ValueError:
        await message.reply_text("❌ Invalid number. Please enter a valid point amount.")
        return

    logger.debug(f"🔄 Encoding Points -> msg_id: {msg_id}, channel_id: {client.db_channel.id}, required_points: {required_points}")

    encoded_key = await encode_points((msg_id, client.db_channel.id, required_points))

    if not encoded_key:
        await message.reply_text("❌ Error generating access key. Please try again.")
        return

    logger.debug(f"✅ Encoded Key (Points): {encoded_key}")

    access_link = f"https://t.me/{client.username}?start=file_{encoded_key}"

    logger.debug(f"📥 Storing in MongoDB -> msg_id: {msg_id}, required_points: {required_points}, access_key: {encoded_key}, file_name: {file_name}")
    insert_result = await link_data.insert_one({
        "msg_id": msg_id,
        "required_points": required_points,
        "access_key": str(encoded_key),
        "file_name": file_name,
        "hash": encoded_key  # Ensure the hash is stored
    })

    logger.debug(f"✅ MongoDB Inserted ID: {insert_result.inserted_id}")
    
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"👻 Sʜᴀʀᴇ Lɪɴᴋ", url=f'https://telegram.me/share/url?url={access_link}')],
    ])

    await message.reply_text(
        f"<blockquote><b>NʏxKɪɴɢX Pᴀɪᴅ 🔥</b></blockquote>\n"
        f"<b>{file_name}</b>\n"
        f"<b>Rᴇǫᴜɪʀᴇᴅ Pᴏɪɴᴛs : {required_points}</b>\n"
        f"<blockquote><b>Aᴄᴄᴇss Lɪɴᴋ :\n{access_link}</b></blockquote>\n",
        quote=True,
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )

@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command('accessbatch'))
async def batch_access(client: Client, message: Message):
    try:
        # Ask for the file name and required points only once
        file_name_message = await client.ask(
            text="Enter the name for this batch of files:",
            chat_id=message.from_user.id,
            filters=filters.text,
            timeout=60
        )
        file_name = file_name_message.text.strip()
        
        points_message = await client.ask(
            text="Enter the total required points to access this batch:",
            chat_id=message.from_user.id,
            filters=filters.text,
            timeout=60
        )
        required_points = int(points_message.text)
    except Exception:
        await message.reply_text("❌ Timed out or invalid input. Please try again.")
        return
    
    # Get the first message ID
    try:
        first_message = await client.ask(
            text="Forward the FIRST message from the DB Channel:",
            chat_id=message.from_user.id,
            filters=filters.forwarded,
            timeout=60
        )
        start_msg_id = await get_message_id(client, first_message)
    except Exception:
        await message.reply_text("❌ Failed to get the first message. Try again.")
        return

    # Get the last message ID
    try:
        last_message = await client.ask(
            text="Forward the LAST message from the DB Channel:",
            chat_id=message.from_user.id,
            filters=filters.forwarded,
            timeout=60
        )
        end_msg_id = await get_message_id(client, last_message)
    except Exception:
        await message.reply_text("❌ Failed to get the last message. Try again.")
        return

    # Encode only the start ID, end ID, and required points
    encoded_key = await encode_batch_points(start_msg_id, end_msg_id, client.db_channel.id, required_points)
    access_link = f"https://t.me/{client.username}?start=batch_{encoded_key}"

    # Store the batch details in the database
    await batch_data.insert_one({
        "start_id": start_msg_id,
        "end_id": end_msg_id,
        "db_channel_id": client.db_channel.id,
        "required_points": required_points,
        "file_name": file_name,
        "access_key": encoded_key,
        "hash": encoded_key  # Ensure the hash is stored
    })

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("👻 Share Link", url=f'https://telegram.me/share/url?url={access_link}')],
    ])

    await message.reply_text(
        f"<blockquote><b>NʏxKɪɴɢX Pᴀɪᴅ 🔥</b></blockquote>\n"
        f"<b> {file_name}</b>\n"
        f"<b>Rᴇǫᴜɪʀᴇᴅ Pᴏɪɴᴛs : {required_points}</b>\n"
        f"<blockquote><b>Aᴄᴄᴇss Lɪɴᴋ :\n{access_link}</b></blockquote>",
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )

@Bot.on_message(filters.private & filters.command('click'))
async def click_command(client: Client, message: Message):
    try:
        link_message = await client.ask(
            text="⚡ Sᴇɴᴅ ᴛʜᴇ Lɪɴᴋ ᴛᴏ Gᴇᴛ Cʟɪᴄᴋ Dᴇᴛᴀɪʟs :",
            chat_id=message.from_user.id,
            filters=filters.text,
            timeout=60
        )

        link = link_message.text.strip()
        if 'start=' not in link:
            await message.reply("❌ Iɴᴠᴀʟɪᴅ Lɪɴᴋ Fᴏʀᴍᴀᴛ!**\n💡 Pʟᴇᴀsᴇ Pʀᴏᴠɪᴅᴇ A Vᴀʟɪᴅ Lɪɴᴋ.")
            return

        # Extract and normalize the hash
        hash = link.split('start=')[1]
        hash = hash.replace("file_", "").replace("batch_", "")

        # Retrieve click details
        details = await get_click_details(hash)
        
        # Advanced Reply with Inline Buttons
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("👻 Sʜᴀʀᴇ Lɪɴᴋ", switch_inline_query=link)]
        ])
        
        await message.reply(details, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)

    except Exception as e:
        await message.reply(f"❌ **Eʀʀᴏʀ:** `{str(e)}`\n🚨 _Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ!_")

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
from pyrogram import Client, filters
from pyrogram.types import Message
import re
from pathlib import Path

FONT_PATH = Path("fonts/arialbd.ttf")

TERABOX_DOMAINS = [
    'terabox.com', 'nephobox.com', '4funbox.com', 'mirrobox.com',
    'momerybox.com', 'teraboxapp.com', '1024tera.com', '1024terabox.com',
    'terabox.app', 'gibibox.com', 'goaibox.com', 'terasharelink.com',
    'teraboxlink.com', 'terafileshare.com', 'teraboxshare.com'
]

TERABOX_REGEX = r"https?://(?:www\.)?(?:" + "|".join(re.escape(domain) for domain in TERABOX_DOMAINS) + r")/s/[a-zA-Z0-9_-]+"
CHANNEL_ID = -1002571223411


def blur_corners_for_watermark_removal(image):
    """Blur the corners to remove existing watermark text like 'getnewlink.com'."""
    blur_radius = 15  # Strength of blur
    size = image.size
    crop_size = (250, 100)  # Area to blur for each corner (width, height)

    # Define corner regions
    regions = {
        "top_left": (0, 0, crop_size[0], crop_size[1]),
        "top_right": (size[0] - crop_size[0], 0, size[0], crop_size[1]),
        "bottom_left": (0, size[1] - crop_size[1], crop_size[0], size[1]),
        "bottom_right": (size[0] - crop_size[0], size[1] - crop_size[1], size[0], size[1]),
    }

    for box in regions.values():
        corner = image.crop(box).filter(ImageFilter.GaussianBlur(blur_radius))
        image.paste(corner, box)

    return image


@Bot.on_message(filters.private & filters.user(ADMINS) & filters.media)
async def terabox_command(client: Client, message: Message):

    if not (message.photo and message.caption):
        return await message.reply("🚫 Sᴇɴᴅ ᴀɴ ɪᴍᴀɢᴇ + ᴄᴀᴘᴛɪᴏɴ ᴡɪᴛʜ Tᴇʀᴀʙᴏx ʟɪɴᴋs.")
    
    # Extract Terabox links from the caption
    links = re.findall(TERABOX_REGEX, message.caption)
    if not links:
        return await message.reply("❌ Nᴏ Tᴇʀᴀʙᴏx ʟɪɴᴋs ᴅᴇᴛᴇᴄᴛᴇᴅ.")

    # Download image
    image_path = await client.download_media(message.photo.file_id)


    # Open and process image
    im = Image.open(image_path).convert("RGBA")

    # Remove watermark by blurring corners
    im = blur_corners_for_watermark_removal(im)

    # Apply custom watermark
    txt = Image.new("RGBA", im.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(txt)

    try:
        font_center = ImageFont.truetype(str(FONT_PATH), size=int(im.height * 0.1))
        font_border = ImageFont.truetype(str(FONT_PATH), size=int(im.height * 0.05))
    except IOError:
        font_center = ImageFont.load_default()
        font_border = ImageFont.load_default()

    text_center = "@NʏxKɪɴɢX"

    # Center watermark
    bbox_center = draw.textbbox((0, 0), text_center, font=font_center)
    text_width_center = bbox_center[2] - bbox_center[0]
    text_height_center = bbox_center[3] - bbox_center[1]

    x_center = (im.width - text_width_center) // 2
    y_center = (im.height - text_height_center) // 2

    draw.text((x_center, y_center), text_center, font=font_center, fill=(0, 0, 0, 180))

    # Repeated border watermark
    for x in range(0, im.width, text_width_center + 10):
        draw.text((x, 10), text_center, font=font_border, fill=(0, 0, 0, 50))  # Top
        draw.text((x, im.height - text_height_center - 10), text_center, font=font_border, fill=(0, 0, 0, 50))  # Bottom

    for y in range(0, im.height, text_height_center + 10):
        draw.text((10, y), text_center, font=font_border, fill=(0, 0, 0, 50))  # Left
        draw.text((im.width - text_width_center - 10, y), text_center, font=font_border, fill=(0, 0, 0, 50))  # Right

    # Merge watermark with original
    watermarked = Image.alpha_composite(im, txt)

    final_path = "watermarked.jpg"
    watermarked.convert("RGB").save(final_path, "JPEG")

    formatted_links = "\n".join(f"{i+1}. {link}" for i, link in enumerate(links))
    caption = f"<b>NʏxKɪɴɢX Oғғɪᴄɪᴀʟ</b>\n\nVɪᴅᴇᴏ Lɪɴᴋ :- \n{formatted_links}"

    await client.send_photo(
        chat_id=-1002637047900,
        photo=final_path,
        caption=caption
    )

    os.remove(image_path)
    os.remove(final_path)




# @Client.on_callback_query(filters.regex("send_to_channel_yes"))
# async def send_to_channel_yes(client: Client, callback_query):
#     # Extract the media content and caption
#     message = callback_query.message
#     caption = message.caption
#     media = message.photo

#     # Prepare the media for sending to the channel
#     if media:
#         # Forward the message (image + caption) to the channel
#         await client.send_photo(
#             CHANNEL_ID,  # Channel ID
#             media.file_id,  # Image
#             caption=caption,  # Caption
#             reply_markup=InlineKeyboardMarkup([  # Optional buttons
#                 [InlineKeyboardButton("Tᴇʀᴀʙᴏx Dᴏᴡɴʟᴏᴀᴅᴇʀ ( Fʀᴇᴇ )", url="https://t.me/NyxTeraBoxxRobot")]
#             ])
#         )

#         # Inform the user that the message has been sent
#         await callback_query.answer("✅ Message sent to the channel!")

#     else:
#         # Handle the case if there's no media to send
#         await callback_query.answer("❌ No media found to send.")


# @Client.on_callback_query(filters.regex("send_to_channel_no"))
# async def send_to_channel_no(client: Client, callback_query):
#     await callback_query.answer("❌ Cʜᴏsᴇɴ ᴛᴏ ɴᴏᴛ sᴇɴᴅ ᴛᴏ ᴄʜᴀɴɴᴇʟ.")
#     await callback_query.message.reply("🚫 Yᴏᴜ ᴄʜᴏsᴇ ᴛᴏ ɴᴏᴛ sᴇɴᴅ ᴛᴏ ᴄʜᴀɴɴᴇʟ.")
