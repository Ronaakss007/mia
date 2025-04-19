# from pyrogram import __version__, filters, Client
# from bot import Bot
# from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message, InputMediaPhoto
# from pyrogram.errors import FloodWait, PeerIdInvalid
# import time
# import asyncio
# import random
# import logging
# from pymongo import InsertOne
# from helper_func import *
# from database.database import *
# from tqdm import tqdm  # Progress bar library
# from config import *
# from datetime import datetime, timedelta, timezone
# from pyromod import listen
# from bson.objectid import ObjectId
# from pyrogram.enums import ParseMode
# from plugins.channel_post import *

# # @Bot.on_callback_query(filters.regex("^sponsorship$"))
# # async def sponsorship_callback(client, query):
# #     """Handle sponsorship inquiries"""
# #     try:
# #         user_id = query.from_user.id
# #         user = await user_data.find_one({'_id': user_id})
        
# #         # Get user's current plan for personalized rates
# #         current_plan = await get_user_plan(user_id)

# #         total_users = await user_data.count_documents({})
        
# #         # Prepare sponsorship information with different tiers
# #         sponsorship_text = f"""
# # <b>🤝 Sponsorship Opportunities 🤝</b>

# # Reach our growing community of {total_users}+ active users through strategic sponsorship!

# # <b>📊 Sponsorship Tiers:</b>

# # <b>🥉 Bronze Tier - $XX/week</b>
# # • Logo in bot messages
# # • 1 promotional message per day
# # • Basic analytics

# # <b>🥈 Silver Tier - $XX/week</b>
# # • All Bronze benefits
# # • Custom command with your info
# # • 3 promotional messages per day
# # • Detailed user engagement analytics

# # <b>🥇 Gold Tier - $XX/week</b>
# # • All Silver benefits
# # • Featured in bot welcome message
# # • Unlimited promotional messages
# # • Premium user targeting
# # • Full analytics dashboard

# # <b>👑 Custom Partnership</b>
# # • Tailored to your specific needs
# # • Co-branded features
# # • Exclusive access to our audience

# # <b>Contact our admin to discuss sponsorship options:</b>
# # """
        
# #         # Create contact button
# #         contact_button = InlineKeyboardMarkup([
# #             [InlineKeyboardButton("📞 Contact Admin", url=SCREENSHOT_URL)],
# #             [InlineKeyboardButton("🔙 Back", callback_data="backtostart")]
# #         ])
        
# #         await query.message.reply_text(
# #             sponsorship_text,
# #             reply_markup=contact_button,
# #             disable_web_page_preview=True
# #         )
        
# #     except Exception as e:
# #         print(f"Error in sponsorship callback: {e}")
# #         await query.answer("An error occurred. Please try again later.", show_alert=True)
