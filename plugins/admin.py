import os
from pyrogram import Client, filters, types
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
import re
from database.database import *
import sys
from pyrogram.handlers import MessageHandler

# Database collections
WAITING_FOR_UPI = {}
admin_settings = database['admin_settings']
admins_collection = database['admins']

DEFAULT_TIME = 3600  # Default 1 hour
DEFAULT_PAID_TIME = 3600  # Default 1 hour for file expiration

### ✅ Helper Functions

async def get_settings():
    """Retrieve current bot settings from the database"""
    data = await admin_settings.find_one({"_id": "settings"}) or {}
    return {
        "waiting_timer": data.get("waiting_timer", True),
        "USE_SHORTLINK": data.get("USE_SHORTLINK", True),
        "USE_PAYMENT": data.get("USE_PAYMENT", True),  # Add USE_PAYMENT
        "U_S_E_P": data.get("U_S_E_P", False),
        "VERIFY_EXPIRE": data.get("VERIFY_EXPIRE", 28000),
        "SECONDS": data.get("SECONDS", 3600),  # Default to 3600 seconds
        "PAID_TIME": data.get("PAID_TIME", 3600),  # Default to 3600 seconds
        "TUT_VID": data.get("TUT_VID", "https://t.me/c/2396123709/2465"),
        "UPI_ID": data.get("UPI_ID", "ronaksaini922@ybl"),
        "UPI_IMAGE_URL": data.get("UPI_IMAGE_URL", "https://ibb.co/mVDMPLwW"),
        "SCREENSHOT_URL": data.get("SCREENSHOT_URL", "t.me/NyxKingX"),
        "SHORTLINK_API_URLS": data.get("SHORTLINK_API_URLS", []),
        "SHORTLINK_API_KEYS": data.get("SHORTLINK_API_KEYS", []),
        "FORCE_SUB_CHANNELS": data.get("FORCE_SUB_CHANNELS", []),  # Add this line
        "REQUEST_SUB_CHANNELS": data.get("REQUEST_SUB_CHANNELS", []),  # Request-join channels
        "PRICES": data.get("PRICES", { 
            "0": 15,
            "7": 49,
            "30": 99,
            "90": 249,
            "180": 449,
            "365": 799,
            "730": 1400
        }),
        "welcome_enabled": data.get("welcome_enabled", True)  # Initialize with default value
    }

async def set_setting(setting, value):
    """Update a specific setting in the database"""
    await admin_settings.update_one({"_id": "settings"}, {"$set": {setting: value}}, upsert=True)

async def generate_main_settings_message():
    """Generate the main settings message with buttons."""
    settings = await get_settings()
    
    status_timer = "✅ " if settings["waiting_timer"] else "✖ "
    status_shortlink = "✅ " if settings["USE_SHORTLINK"] else "✖ "
    status_payment = "✅ " if settings["USE_PAYMENT"] else "✖ "
    status_pep = "✅ " if settings["U_S_E_P"] else "✖"  # Add status for USE_PEP
    status_welcome = "✅ " if settings.get("welcome_enabled", True) else "✖"

    text = f"⚙️ **NʏxDᴇsɪʀᴇ – Aᴅᴍɪɴ Sᴇᴛᴛɪɴɢs Pᴀɴᴇʟ**\n\n" \
           f"<blockquote>🕒 **Wᴀɪᴛɪɴɢ Tɪᴍᴇʀ :** {status_timer}\n" \
           f"🔗 **Sʜᴏʀᴛʟɪɴᴋ :** {status_shortlink}\n" \
           f"💳 **Pᴀʏᴍᴇɴᴛ :** {status_payment}\n" \
           f"👋 **Wᴇʟᴄᴏᴍᴇ Mᴇssᴀɢᴇ :** {status_welcome}\n" \
           f"🔥 **Usᴇᴘ :** {status_pep}</blockquote>\n\n" \
           "Cʟɪᴄᴋ Tʜᴇ Bᴜᴛᴛᴏɴs Bᴇʟᴏᴡ Tᴏ Mᴀɴᴀɢᴇ Sᴇᴛᴛɪɴɢs..."

    keyboard = InlineKeyboardMarkup([ 
        [
            InlineKeyboardButton(f"⏱️ Tɪᴍᴇʀ: {status_timer}", callback_data="toggle_timer:waiting_timer"),
            InlineKeyboardButton(f"📢 Wᴇʟᴄᴏᴍᴇ: {status_welcome}", callback_data="toggle_welcome:welcome_enabled")
        ],
        [
            InlineKeyboardButton(f"💳 Pᴀʏᴍᴇɴᴛ: {status_payment}", callback_data="toggle_payment:USE_PAYMENT"),
            InlineKeyboardButton(f"🔥 Usᴇᴘ: {status_pep}", callback_data="toggle_pep:U_S_E_P")
        ],
        [
            InlineKeyboardButton("💸 Mᴀɴᴀɢᴇ Pᴀʏᴍᴇɴᴛ", callback_data="manage_payment"),
            InlineKeyboardButton("⚔️ Mᴀɴᴀɢᴇ Sʜᴏʀᴛʟɪɴᴋ", callback_data="manage_shortlink") 
        ],
        [
            InlineKeyboardButton("⚙️ Fᴏʀᴄᴇ Sᴜʙ Cʜᴀɴɴᴇʟs", callback_data="manage_forcesub")
        ],
        [
            InlineKeyboardButton("🧹 Aᴜᴛᴏ Dᴇʟᴇᴛᴇ", callback_data="manage_time_settings"),
            InlineKeyboardButton("Cʟᴏsᴇ ✖ ", callback_data="close")
        ]
    ])

    return text, keyboard


@Client.on_message(filters.command("settings") & filters.user(ADMINS))
async def settings_command(client, message):
    """Handles /settings command to display bot settings and admins"""
    text, keyboard = await generate_main_settings_message()
    await message.reply(text, reply_markup=keyboard, disable_web_page_preview=True)

### 🔗 Shortlink Management Callbacks
@Client.on_callback_query(filters.regex("^manage_payment$"))
async def manage_payment_callback(client, callback_query: CallbackQuery):
    if callback_query.from_user.id not in ADMINS:
        await callback_query.answer("Yᴏᴜ Aʀᴇ Nᴏᴛ Aᴅᴍɪɴ ✖ ", show_alert=True)
        return
    """Handles 'Manage Payment' callback"""
    settings = await get_settings()
    
    text = (
        "⚙️ **Mᴀɴᴀɢᴇ Pᴀʏᴍᴇɴᴛ Sᴇᴛᴛɪɴɢs**\n\n"
        f"<blockquote>💳 **Uᴘɪ Iᴅ :** `{settings['UPI_ID']}`\n</blockquote>"
        f"🖼 **Uᴘɪ Iᴍᴀɢᴇ Uʀʟ:** [View Image]({settings['UPI_IMAGE_URL']})\n"
        f"📸 **Sᴄʀᴇᴇɴsʜᴏᴛ Uʀʟ:** [View Screenshot]({settings['SCREENSHOT_URL']})\n"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Uᴘᴅᴀᴛᴇ Uᴘɪ Iᴅ", callback_data="update_upi_id"),
        InlineKeyboardButton("🖼 Uᴘᴅᴀᴛᴇ Iᴍᴀɢᴇ Uʀʟ", callback_data="update_upi_image")],
        [InlineKeyboardButton("📸 Uᴘᴅᴀᴛᴇ Sᴄʀᴇᴇɴsʜᴏᴛ Uʀʟ", callback_data="update_screenshot")],
        [InlineKeyboardButton("👹 Mᴀɴᴀɢᴇ Pʀɪᴄᴇs", callback_data="manage_prices")],
        [InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data="back_to_main")]  # Optional Back Button
    ])

    await callback_query.message.edit_text(text, reply_markup=keyboard, disable_web_page_preview=True)
    await callback_query.answer()

@Client.on_callback_query(filters.regex("^update_upi_id$"))
async def update_upi_id_callback(client, callback_query: CallbackQuery):
    """Handles UPI ID update request"""
    await callback_query.message.edit_text(f"🔹 Please send the **new UPI ID**:"),
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data="manage_payment")]  # Optional Back Button
    ])
    await callback_query.answer()

    try:
        response = await client.listen(callback_query.from_user.id, timeout=60)
        new_upi_id = response.text.strip()

        await set_setting("UPI_ID", new_upi_id)
        await client.send_message(callback_query.from_user.id, "✅ **UPI ID updated successfully!**")
    
    except TimeoutError:
        await client.send_message(callback_query.from_user.id, "❌ No response received. UPI update canceled.")

@Client.on_callback_query(filters.regex("^update_upi_image$"))
async def update_upi_image_callback(client, callback_query: CallbackQuery):
    """Handles UPI Image update request"""
    await callback_query.message.edit_text(f"🔹 Please send the **new UPI Image URL**:"),
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data="manage_payment")]  # Optional Back Button
    ])
    await callback_query.answer()

    try:
        response = await client.listen(callback_query.from_user.id, timeout=60)
        new_upi_image = response.text.strip()

        await set_setting("UPI_IMAGE_URL", new_upi_image)
        await client.send_message(callback_query.from_user.id, "✅ **UPI Image URL updated successfully!**")

    except TimeoutError:
        await client.send_message(callback_query.from_user.id, "❌ No response received. Update canceled.")

@Client.on_callback_query(filters.regex("^update_screenshot$"))
async def update_screenshot_callback(client, callback_query: CallbackQuery):
    """Handles Screenshot URL update request"""
    await callback_query.message.edit_text(f"🔹 Please send the **new Screenshot URL**:"),
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data="manage_payment")]  # Optional Back Button
    ])
    await callback_query.answer()

    try:
        response = await client.listen(callback_query.from_user.id, timeout=60)
        new_screenshot = response.text.strip()

        await set_setting("SCREENSHOT_URL", new_screenshot)
        await client.send_message(callback_query.from_user.id, "✅ **Screenshot URL updated successfully!**")

    except TimeoutError:
        await client.send_message(callback_query.from_user.id, "❌ No response received. Update canceled.")

@Client.on_callback_query(filters.regex("^manage_prices$"))
async def manage_prices_callback(client, callback_query: CallbackQuery):
    """Handles the price management menu"""
    settings = await get_settings()
    prices = settings.get("PRICES", {})

    # Format prices for display
    price_text = "\n".join([f"📅 {days} days: ₹{price}" for days, price in prices.items()])

    text = (
        "💰 **Mᴀɴᴀɢᴇ Pʀɪᴄᴇs**\n\n"
        f"Here are the current prices:\n\n{price_text if price_text else 'No prices set.'}\n\n"
        "➕ To add/update a price, send:\n"
        "`<days> <price>` (e.g., `30 99` for ₹99 per 30 days)."
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Aᴅᴅ/ᴜᴘᴅᴀᴛᴇ Pʀɪᴄᴇ", callback_data="add_update_price")],
        [InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data="back_to_main")]
    ])

    await callback_query.message.edit_text(text, reply_markup=keyboard)
    await callback_query.answer()

@Client.on_callback_query(filters.regex("^add_update_price$"))
async def add_update_price_callback(client, callback_query: CallbackQuery):
    """Handles adding or updating a price"""
    await callback_query.message.edit_text(
        "📅 **Sᴇɴᴅ Tʜᴇ Dᴜʀᴀᴛɪᴏɴ ᴀɴᴅ Pʀɪᴄᴇ**\n\n"
        "Example: `30 99` (for ₹99 per 30 days).",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data="manage_prices")]
        ])
    )
    await callback_query.answer()

    try:
        # Wait for the user to send input
        response = await client.listen(callback_query.from_user.id, timeout=60)
        input_data = response.text.strip().split()

        # Validate input format
        if len(input_data) != 2 or not input_data[0].isdigit() or not input_data[1].isdigit():
            await client.send_message(callback_query.from_user.id, "❌ Invalid format! Send `<days> <price>`.")
            return

        # Parse input
        days, price = map(int, input_data)

        # Update prices in the database
        settings = await get_settings()
        prices = settings.get("PRICES", {})
        prices[str(days)] = price
        await set_setting("PRICES", prices)

        # Confirmation message
        await client.send_message(
            callback_query.from_user.id,
            f"✅ **Updated Price:** `{days}` days now costs ₹{price}!"
        )

    except TimeoutError:
        await client.send_message(callback_query.from_user.id, "❌ No response received. Update canceled.")
    except Exception as e:
        print(f"⚠️ Unexpected error: {e}")
        await client.send_message(callback_query.from_user.id, "❌ An error occurred while updating the price.")


@Client.on_callback_query(filters.regex("^manage_shortlink$"))
async def manage_shortlink_callback(client, callback_query: CallbackQuery):
    if callback_query.from_user.id not in ADMINS:
        await callback_query.answer("Yᴏᴜ Aʀᴇ Nᴏᴛ Aᴅᴍɪɴ ✖ ", show_alert=True)
        return
    """Handles 'Manage Shortlink' callback"""
    settings = await get_settings()
    
    text = (
        "🔗 **Mᴀɴᴀɢᴇ Sʜᴏʀᴛʟɪɴᴋ Sᴇᴛᴛɪɴɢs**\n\n"
        f"<blockquote>🔘 **Sʜᴏʀᴛʟɪɴᴋ Eɴᴀʙʟᴇᴅ:** `{settings['USE_SHORTLINK']}`\n"
        f"⏳ **Vᴇʀɪғʏ Exᴘɪʀᴇ Tɪᴍᴇ:** `{settings['VERIFY_EXPIRE']} sᴇᴄᴏɴᴅs`\n</blockquote>"
        f"🔗 **Sʜᴏʀᴛʟɪɴᴋ Aᴘɪ Uʀʟs:** `{', '.join(settings['SHORTLINK_API_URLS']) or 'None'}`\n"
        f"🔑 **Sʜᴏʀᴛʟɪɴᴋ Aᴘɪ Kᴇʏs:** `{', '.join(settings['SHORTLINK_API_KEYS']) or 'None'}`\n"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛠️ Tᴏɢɢʟᴇ Sʜᴏʀᴛʟɪɴᴋ", callback_data="toggle_shortlink")],
        [InlineKeyboardButton("⏳ Uᴘᴅᴀᴛᴇ Vᴇʀɪғʏ Exᴘɪʀᴇ", callback_data="update_verify_expire")],
        [InlineKeyboardButton("🌐 Uᴘᴅᴀᴛᴇ Aᴘɪ Uʀʟs", callback_data="update_shortlink_urls"),
         InlineKeyboardButton("🔑 Uᴘᴅᴀᴛᴇ Aᴘɪ Kᴇʏs", callback_data="update_shortlink_keys")],
        [InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data="back_to_main")]  # Optional Back Button
    ])

    await callback_query.message.edit_text(text, reply_markup=keyboard, disable_web_page_preview=True)
    await callback_query.answer()


@Client.on_callback_query(filters.regex("^toggle_shortlink$"))
async def toggle_shortlink_callback(client, callback_query: CallbackQuery):
    """Toggles Shortlink ON/OFF"""
    if callback_query.from_user.id not in ADMINS:
        await callback_query.answer("Yᴏᴜ Aʀᴇ Nᴏᴛ Aᴅᴍɪɴ ✖ ", show_alert=True)
        return
    settings = await get_settings()
    new_status = not settings["USE_SHORTLINK"]  # Toggle value

    await set_setting("USE_SHORTLINK", new_status)
    await callback_query.answer(f"⚙️ Sʜᴏʀᴛʟɪɴᴋ {'Eɴᴀʙʟᴇᴅ' if new_status else 'Dɪsᴀʙʟᴇᴅ'}!")
    await manage_shortlink_callback(client, callback_query)  # Refresh the menu

@Client.on_callback_query(filters.regex("^update_verify_expire$"))
async def update_verify_expire_callback(client, callback_query: CallbackQuery):
    """Handles Verify Expire Time update request"""
    await callback_query.message.edit_text(f"📝 **Sᴇɴᴅ ᴛʜᴇ ɴᴇᴡ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ ᴇxᴘɪʀʏ ᴛɪᴍᴇ ɪɴ sᴇᴄᴏɴᴅs:**\n📌 Example: `30000` (for 30,000 seconds ≈ 8 hours)"),
    reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cᴀɴᴄᴇʟ", callback_data="manage_shortlink")]
    ])
    await callback_query.answer()

    try:
        response = await client.listen(callback_query.from_user.id, timeout=60)
        new_expire_time = int(response.text.strip())  # Convert to integer

        await set_setting("VERIFY_EXPIRE", new_expire_time)
        await client.send_message(callback_query.from_user.id, "✅ **Verify Expire Time updated successfully!**")

    except ValueError:
        await client.send_message(callback_query.from_user.id, "❌ Invalid input. Please enter a valid number.")
    except TimeoutError:
        await client.send_message(callback_query.from_user.id, "❌ No response received. Update canceled.")


@Client.on_callback_query(filters.regex("^update_shortlink_urls$"))
async def update_shortlink_urls_callback(client, callback_query: CallbackQuery):
    """Handles Shortlink API URLs update"""
    await callback_query.message.edit_text(f"🌐 Please send the **new Shortlink API URLs** (comma-separated):"),
    reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cᴀɴᴄᴇʟ", callback_data="manage_shortlink")]
    ])
    await callback_query.answer()

    try:
        response = await client.listen(callback_query.from_user.id, timeout=60)
        new_urls = [url.strip() for url in response.text.split(",")]

        await set_setting("SHORTLINK_API_URLS", new_urls)
        await client.send_message(callback_query.from_user.id, "✅ **Shortlink API URLs updated successfully!**")

    except TimeoutError:
        await client.send_message(callback_query.from_user.id, "❌ No response received. Update canceled.")

@Client.on_callback_query(filters.regex("^update_shortlink_keys$"))
async def update_shortlink_keys_callback(client, callback_query: CallbackQuery):
    """Handles Shortlink API Keys update"""
    await callback_query.message.edit_text(f"🔑 Please send the **new Shortlink API Keys** (comma-separated):"),
    reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cᴀɴᴄᴇʟ", callback_data="manage_shortlink")]
    ])
    await callback_query.answer()

    try:
        response = await client.listen(callback_query.from_user.id, timeout=60)
        new_keys = [key.strip() for key in response.text.split(",")]

        await set_setting("SHORTLINK_API_KEYS", new_keys)
        await client.send_message(callback_query.from_user.id, "✅ **Shortlink API Keys updated successfully!**")

    except TimeoutError:
        await client.send_message(callback_query.from_user.id, "❌ No response received. Update canceled.")


@Client.on_callback_query(filters.regex("^back_to_main$"))
async def back_to_main_callback(client, callback_query: CallbackQuery):
    """Handles 'Back to Main Menu' callback"""
    text, keyboard = await generate_main_settings_message()  # Regenerate the main settings message
    await callback_query.message.edit_text(text, reply_markup=keyboard, disable_web_page_preview=True)
    await callback_query.answer()  # Acknowledge the callback
    
@Client.on_callback_query(filters.regex("^toggle_"))
async def toggle_setting_callback(client, callback_query):
    if callback_query.from_user.id not in ADMINS:
        await callback_query.answer("Yᴏᴜ Aʀᴇ Nᴏᴛ Aᴅᴍɪɴ ✖ ", show_alert=True)
        return
    try:
        # Ensure the data is correctly formatted
        if ':' not in callback_query.data:
            raise ValueError("Callback data is incorrectly formatted.")
        
        setting_key = callback_query.data.split(":")[1]

        # Get current settings from the database
        settings = await get_settings()

        # Ensure that the setting exists before trying to toggle it
        if setting_key not in settings:
            raise ValueError(f"Setting '{setting_key}' not found in settings.")

        # Determine if the setting should be toggled
        new_value = not settings[setting_key]

        # Update the setting in the database
        await set_setting(setting_key, new_value)

        # Determine the status message based on the setting toggled
        if setting_key == "waiting_timer":
            status = "✅ Eɴᴀʙʟᴇᴅ" if new_value else "❌ Dɪsᴀʙʟᴇᴅ"
        elif setting_key == "USE_SHORTLINK":
            status = "✅ Eɴᴀʙʟᴇᴅ" if new_value else "❌ Dɪsᴀʙʟᴇᴅ"
        elif setting_key == "USE_PAYMENT":
            status = "✅ Eɴᴀʙʟᴇᴅ" if new_value else "❌ Dɪsᴀʙʟᴇᴅ"
        else:
            status = "❌ Unknown Setting"  # Fallback in case an unknown setting is toggled
        
        # Regenerate the main settings message with updated statuses
        text, keyboard = await generate_main_settings_message()

        # Edit the message with new button statuses
        await callback_query.message.edit_text(text, reply_markup=keyboard, disable_web_page_preview=True)
        await callback_query.answer()  # Acknowledge the callback

    except ValueError as e:
        print(f"Error: {e}")
        await callback_query.answer("Invalid setting or data format.")
    except Exception as e:
        print(f"Unexpected error: {e}")
        await callback_query.answer("An unexpected error occurred.")


@Client.on_callback_query(filters.regex("^toggle_pep:U_S_E_P$"))
async def toggle_pep_callback(client, callback_query: CallbackQuery):
    if callback_query.from_user.id not in ADMINS:
        await callback_query.answer("Yᴏᴜ Aʀᴇ Nᴏᴛ Aᴅᴍɪɴ ✖ ", show_alert=True)
        return
    try:
        # Get current settings from the database
        settings = await get_settings()

        # Toggle the USE_PEP setting
        new_value = not settings["USE_PEP"]

        # Update the setting in the database
        await set_setting("USE_PEP", new_value)

        # Update status message based on the new value
        status_pep = "✅ Enabled" if new_value else "❌ Disabled"

        # Regenerate the main settings message with updated statuses
        text, keyboard = await generate_main_settings_message()

        # Edit the message with the new settings
        await callback_query.message.edit_text(text, reply_markup=keyboard, disable_web_page_preview=True)
        await callback_query.answer()  # Acknowledge the callback

    except Exception as e:
        print(f"Unexpected error: {e}")
        await callback_query.answer("An unexpected error occurred.")



# 📌 Manage Force Subscription Menu
@Client.on_callback_query(filters.regex("^manage_forcesub$"))
async def manage_forcesub_callback(client, callback_query: CallbackQuery):
    if callback_query.from_user.id not in ADMINS:
        await callback_query.answer("Yᴏᴜ Aʀᴇ Nᴏᴛ Aᴅᴍɪɴ ✖", show_alert=True)
        return

    settings = await get_settings()
    normal_channels = settings.get("FORCE_SUB_CHANNELS", [])
    request_channels = settings.get("REQUEST_SUB_CHANNELS", [])

    text = "📢 **Fᴏʀᴄᴇ Sᴜʙsᴄʀɪᴘᴛɪᴏɴ Sᴇᴛᴛɪɴɢs**\n\n"

    if normal_channels:
        text += "🔹 **Normal Join Channels:**\n"
        for ch in normal_channels:
            try:
                chat = await client.get_chat(ch)
                link = f"https://t.me/{chat.username}" if chat.username else await client.export_chat_invite_link(ch)
                text += f"• [{chat.title}]({link})\n"
            except Exception as e:
                text += f"• `{ch}` (❌ Failed to fetch)\n"
    else:
        text += "❌ No normal join channels.\n"

    text += "\n"

    if request_channels:
        text += "🔸 **Request Join Channels:**\n"
        for ch in request_channels:
            try:
                chat = await client.get_chat(ch)
                link = chat.invite_link or await client.export_chat_invite_link(ch)
                text += f"• [{chat.title}]({link}) (Request Join)\n"
            except Exception as e:
                text += f"• `{ch}` (❌ Failed to fetch)\n"
    else:
        text += "❌ No request join channels.\n"

    text += "\n⚠️ **Pʟᴇᴀsᴇ Rᴇsᴛᴀʀᴛ Tʜᴇ Bᴏᴛ Aғᴛᴇʀ Uᴘᴅᴀᴛɪɴɢ Cʜᴀɴɴᴇʟs!**"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Nᴏʀᴍᴀʟ Cʜᴀɴɴᴇʟ", callback_data="add_normal_channel"),
            InlineKeyboardButton("➕ Rᴇǫᴜᴇsᴛ Cʜᴀɴɴᴇʟ", callback_data="add_request_channel")
        ],
        [
            InlineKeyboardButton("➖ Rᴇᴍᴏᴠᴇ Nᴏʀᴍᴀʟ", callback_data="remove_normal_channel"),
            InlineKeyboardButton("➖ Rᴇᴍᴏᴠᴇ Rᴇǫᴜᴇsᴛ", callback_data="remove_request_channel")
        ],
        [InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data="back_to_main")]
    ])

    await callback_query.message.edit_text(text, reply_markup=keyboard, disable_web_page_preview=True)


@Client.on_callback_query(filters.regex("^add_normal_channel$"))
async def add_normal_channel(client, callback_query: CallbackQuery):
    if callback_query.from_user.id not in ADMINS:
        return await callback_query.answer("Yᴏᴜ Aʀᴇ Nᴏᴛ Aᴅᴍɪɴ ✖", show_alert=True)

    await callback_query.message.edit_text("📥 **Send the Normal Channel Username or ID:**")
    await callback_query.answer()

    try:
        response = await client.listen(callback_query.from_user.id, timeout=60)
        channel = response.text.strip()
        if channel.replace("-", "").isdigit():
            channel = int(channel)

        settings = await get_settings()
        normal_channels = settings.get("FORCE_SUB_CHANNELS", [])

        if channel in normal_channels:
            return await client.send_message(callback_query.from_user.id, "⚠️ Channel already in the list.")

        normal_channels.append(channel)
        await set_setting("FORCE_SUB_CHANNELS", normal_channels)

        await client.send_message(callback_query.from_user.id, f"✅ **Added `{channel}` to normal channels.**")

    except TimeoutError:
        await client.send_message(callback_query.from_user.id, "❌ Timeout. No input received.")


@Client.on_callback_query(filters.regex("^add_request_channel$"))
async def add_request_channel(client, callback_query: CallbackQuery):
    if callback_query.from_user.id not in ADMINS:
        return await callback_query.answer("Yᴏᴜ Aʀᴇ Nᴏᴛ Aᴅᴍɪɴ ✖", show_alert=True)

    await callback_query.message.edit_text("🔐 **Send the Request Join Channel ID (starts with -100):**")
    await callback_query.answer()

    try:
        response = await client.listen(callback_query.from_user.id, timeout=60)
        channel = response.text.strip()
        if channel.replace("-", "").isdigit():
            channel = int(channel)

        settings = await get_settings()
        request_channels = settings.get("REQUEST_SUB_CHANNELS", [])

        if channel in request_channels:
            return await client.send_message(callback_query.from_user.id, "⚠️ Already in the request list.")

        request_channels.append(channel)
        await set_setting("REQUEST_SUB_CHANNELS", request_channels)

        await client.send_message(callback_query.from_user.id, f"✅ **Added `{channel}` to request join channels.**")

    except TimeoutError:
        await client.send_message(callback_query.from_user.id, "❌ Timeout. No input received.")

# 🔧 Channel Remove Handler
@Client.on_callback_query(filters.regex("^(remove_normal_channel|remove_request_channel)$"))
async def remove_channel_handler(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in ADMINS:
        return await callback_query.answer("Nᴏᴛ Aᴅᴍɪɴ ✖", show_alert=True)

    setting_type = "FORCE_SUB_CHANNELS" if "normal" in callback_query.data else "REQUEST_SUB_CHANNELS"
    label = "Normal" if "normal" in callback_query.data else "Request"

    settings = await get_settings()
    channels = settings.get(setting_type, [])

    if not channels:
        return await callback_query.message.edit_text(f"⚠️ No {label} channels to remove.")

    buttons = [
        [InlineKeyboardButton(f"❌ {ch}", callback_data=f"confirm_remove_{setting_type}_{i}")]
        for i, ch in enumerate(channels)
    ]
    buttons.append([InlineKeyboardButton("◀️ Back", callback_data="manage_forcesub")])

    await callback_query.message.edit_text(
        f"➖ **Select a {label} channel to remove:**",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


@Client.on_callback_query(filters.regex("^confirm_remove_(FORCE_SUB_CHANNELS|REQUEST_SUB_CHANNELS)_\\d+$"))
async def confirm_remove_channel(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in ADMINS:
        return await callback_query.answer("Nᴏᴛ Aᴅᴍɪɴ ✖", show_alert=True)

    parts = callback_query.data.split("_")
    setting_type = "_".join(parts[2:-1])
    index = int(parts[-1])

    settings = await get_settings()
    channels = settings.get(setting_type, [])

    try:
        removed = channels.pop(index)
        await set_setting(setting_type, channels)
        await callback_query.message.edit_text(f"✅ Removed `{removed}` from channel list.")
    except IndexError:
        await callback_query.message.edit_text("❌ Invalid index.")

    # Show updated menu or confirmation (optional)


        
# # 📌 Remove Force Sub Channel (Show List)
# @Client.on_callback_query(filters.regex("^remove_forcesub_channel$"))
# async def remove_forcesub_channel_callback(client, callback_query: CallbackQuery):
#     if callback_query.from_user.id not in ADMINS:
#         await callback_query.answer("Yᴏᴜ Aʀᴇ Nᴏᴛ Aᴅᴍɪɴ ✖ ", show_alert=True)
#         return
#     """Handles removing an existing Force Sub Channel"""
#     settings = await get_settings()
#     force_sub_channels = settings["FORCE_SUB_CHANNELS"]

#     if not force_sub_channels:
#         await callback_query.answer("❌ No channels to remove!", show_alert=True)
#         return

#     keyboard = InlineKeyboardMarkup([
#         [InlineKeyboardButton(f"❌ {str(ch)}", callback_data=f"remove_channel_{ch}")] for ch in force_sub_channels
#     ] + [[InlineKeyboardButton("🔙 Back", callback_data="manage_forcesub")]])

#     await callback_query.message.edit_text(f"➖ **Sᴇʟᴇᴄᴛ ᴀ ᴄʜᴀɴɴᴇʟ ᴛᴏ ʀᴇᴍᴏᴠᴇ:**", reply_markup=keyboard),
#     reply_markup=InlineKeyboardMarkup([
#         [InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data="manage_forcesub")]
#     ])
#     await callback_query.answer()

# # 📌 Confirm Channel Removal
# @Client.on_callback_query(filters.regex("^remove_channel_(.+)$"))
# async def confirm_remove_channel_callback(client, callback_query: CallbackQuery):
#     if callback_query.from_user.id not in ADMINS:
#         await callback_query.answer("Yᴏᴜ Aʀᴇ Nᴏᴛ Aᴅᴍɪɴ ✖ ", show_alert=True)
#         return
#     """Removes a specific Force Sub Channel"""
#     channel_to_remove = callback_query.data.split("_", 2)[-1]

#     settings = await get_settings()
#     force_sub_channels = settings["FORCE_SUB_CHANNELS"]

#     # Convert numeric ID back to integer if needed
#     if channel_to_remove.isdigit():
#         channel_to_remove = int(channel_to_remove)

#     if channel_to_remove in force_sub_channels:
#         force_sub_channels.remove(channel_to_remove)
#         await set_setting("FORCE_SUB_CHANNELS", force_sub_channels)
#         await callback_query.answer(f"✅ Rᴇᴍᴏᴠᴇᴅ `{channel_to_remove}`!", show_alert=True)

#     await manage_forcesub_callback(client, callback_query)  # Refresh the menu


@Client.on_callback_query(filters.regex("^restart$") & filters.user(ADMINS))
async def restart_callback(client, callback_query: CallbackQuery):
    if callback_query.from_user.id not in ADMINS:
        await callback_query.answer("Yᴏᴜ Aʀᴇ Nᴏᴛ Aᴅᴍɪɴ ✖ ", show_alert=True)
        return
    """Handles the restart process initiated by an admin."""
    
    # Log the restart attempt
    logging.info(f"Restart initiated by user {callback_query.from_user.id}")

    try:
        # Send initial restart message
        restart_msg = await callback_query.message.reply_text(
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

        await callback_query.message.reply_text(
            f"🚨 <b>Cʀɪᴛɪᴄᴀʟ Rᴇsᴛᴀʀᴛ Eʀʀᴏʀ</b>\n"
            f"An unexpected error occurred: <code>{str(overall_error)}</code>",
            quote=True
        )

    await callback_query.answer()  # Acknowledge the callback


@Client.on_callback_query(filters.regex("^manage_time_settings$"))
async def manage_time_settings_callback(client, callback_query):
    if callback_query.from_user.id not in ADMINS:
        await callback_query.answer("Yᴏᴜ Aʀᴇ Nᴏᴛ Aᴅᴍɪɴ ✖ ", show_alert=True)
        return
    """Handles managing TIME and PAID_TIME settings dynamically"""
    settings = await get_settings()
    TIME = settings.get("SECONDS", DEFAULT_TIME)
    PAID_TIME = settings.get("PAID_TIME", DEFAULT_PAID_TIME)

    text = (
        "⏳ **Mᴀɴᴀɢᴇ Tɪᴍᴇ Sᴇᴛᴛɪɴɢs**\n\n"
        f"🔹 **Cᴜʀʀᴇɴᴛ TIME:** `{TIME}` sᴇᴄᴏɴᴅs\n"
        f"🔸 **Cᴜʀʀᴇɴᴛ PAID_TIME:** `{PAID_TIME}` sᴇᴄᴏɴᴅs\n\n"
        "➕ **Sᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ:**"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Tɪᴍᴇ", callback_data="update_time"),
        InlineKeyboardButton("✏️ Pᴀɪᴅ Tɪᴍᴇ", callback_data="update_paid_time")],
        [InlineKeyboardButton("🔄 Rᴇsᴇᴛ Aʟʟ Tᴏ Dᴇғᴀᴜʟᴛ", callback_data="reset_time_settings")],
        [InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data="back_to_main")]
    ])

    await callback_query.message.edit_text(text, reply_markup=keyboard)
    await callback_query.answer()


# Callback Query: Update TIME
@Client.on_callback_query(filters.regex("^update_time$"))
async def update_time_callback(client, callback_query):
    if callback_query.from_user.id not in ADMINS:
        await callback_query.answer("Yᴏᴜ Aʀᴇ Nᴏᴛ Aᴅᴍɪɴ ✖ ", show_alert=True)
        return
    """Handles updating TIME setting"""
    await callback_query.message.edit_text(
        "⏳ **Sᴇɴᴅ ɴᴇᴡ TIME ɪɴ sᴇᴄᴏɴᴅs**\n\nExample: `1800` for 30 minutes.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data="manage_time_settings")]
        ])
    )
    await callback_query.answer()

    try:
        response = await client.listen(callback_query.from_user.id, timeout=60)
        new_time = response.text.strip()

        if not new_time.isdigit():
            await client.send_message(callback_query.from_user.id, "❌ Invalid format! Send a number in seconds.")
            return

        new_time = int(new_time)

        await set_setting("SECONDS", new_time)

        await client.send_message(
            callback_query.from_user.id,
            f"✅ **Updated TIME:** `{new_time}` seconds!"
        )

    except asyncio.TimeoutError:
        await client.send_message(callback_query.from_user.id, "❌ No response received. Update canceled.")
    except Exception as e:
        print(f"⚠️ Unexpected error: {e}")
        await client.send_message(callback_query.from_user.id, "❌ An error occurred while updating TIME.")


# Callback Query: Update PAID_TIME
@Client.on_callback_query(filters.regex("^update_paid_time$"))
async def update_paid_time_callback(client, callback_query):
    if callback_query.from_user.id not in ADMINS:
        await callback_query.answer("Yᴏᴜ Aʀᴇ Nᴏᴛ Aᴅᴍɪɴ ✖ ", show_alert=True)
        return
    """Handles updating PAID_TIME setting"""
    await callback_query.message.edit_text(
        "⏳ **Sᴇɴᴅ ɴᴇᴡ PAID_TIME ɪɴ sᴇᴄᴏɴᴅs**\n\nExample: `7200` for 2 hours.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data="manage_time_settings")]
        ])
    )
    await callback_query.answer()

    try:
        response = await client.listen(callback_query.from_user.id, timeout=60)
        new_paid_time = response.text.strip()

        if not new_paid_time.isdigit():
            await client.send_message(callback_query.from_user.id, "❌ Invalid format! Send a number in seconds.")
            return

        new_paid_time = int(new_paid_time)

        await set_setting("PAID_TIME", new_paid_time)

        await client.send_message(
            callback_query.from_user.id,
            f"✅ **Updated PAID_TIME:** `{new_paid_time}` seconds!"
        )

    except asyncio.TimeoutError:
        await client.send_message(callback_query.from_user.id, "❌ No response received. Update canceled.")
    except Exception as e:
        print(f"⚠️ Unexpected error: {e}")
        await client.send_message(callback_query.from_user.id, "❌ An error occurred while updating PAID_TIME.")


# Callback Query: Reset TIME & PAID_TIME to Default
@Client.on_callback_query(filters.regex("^reset_time_settings$"))
async def reset_time_settings_callback(client, callback_query):
    if callback_query.from_user.id not in ADMINS:
        await callback_query.answer("Yᴏᴜ Aʀᴇ Nᴏᴛ Aᴅᴍɪɴ ✖ ", show_alert=True)
        return
    """Handles resetting TIME and PAID_TIME to default values"""
    await set_setting("SECONDS", DEFAULT_TIME)
    await set_setting("PAID_TIME", DEFAULT_PAID_TIME)

    await callback_query.message.edit_text(
        f"🔄 **TIME and PAID_TIME have been reset to defaults:**\n"
        f"🕒 **TIME:** `{DEFAULT_TIME}` seconds\n"
        f"📂 **PAID_TIME:** `{DEFAULT_PAID_TIME}` seconds",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data="manage_time_settings")]
        ])
    )
    await callback_query.answer()


@Client.on_callback_query(filters.regex("^toggle_welcome$"))
async def toggle_welcome_callback(client, callback_query: CallbackQuery):
    if callback_query.from_user.id not in ADMINS:
        await callback_query.answer("Yᴏᴜ Aʀᴇ Nᴏᴛ Aᴅᴍɪɴ ✖ ", show_alert=True)
        return
    settings = await get_settings()
    
    # Toggle the welcome message status
    new_status = not settings.get("welcome_enabled", True)  # Default to True if not set
    await set_setting("welcome_enabled", new_status)

    status_message = "✅ Welcome message has been enabled!" if new_status else "❌ Welcome message has been disabled!"
    
    # Regenerate the main settings message to reflect the change
    text, keyboard = await generate_main_settings_message()
    
    await callback_query.message.edit_text(text, reply_markup=keyboard, disable_web_page_preview=True)
    await callback_query.answer(status_message)