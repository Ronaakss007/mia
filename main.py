import asyncio
import sys
import traceback
import subprocess
from datetime import datetime

from pyrogram import idle
from bot import Bot
from helper_func import *
from config import *
from plugins.channel_post import *
from database.database import *
from plugins.groupmanager import *
from plugins.cache import *

# 🧠 Caching user data
async def fetch_and_cache_user_data(bot_instance):
    global premium_cache
    tasks = [
        get_premium_showcase(),
        get_premium_showcase_no(),
        get_premium_badge(OWNER_ID)
    ]
    premium_users, premium_number, premium_badge = await asyncio.gather(*tasks)

    premium_cache["premium_users"] = premium_users
    premium_cache["premium_number"] = premium_number
    premium_cache["premium_badge"] = premium_badge
    premium_cache["last_fetched"] = datetime.now()
    print("✅ User data cached successfully.")

# 🔄 Periodic refresh
async def refresh_cache_periodically(bot_instance):
    while True:
        await fetch_and_cache_user_data(bot_instance)
        await asyncio.sleep(4200)

# ⏳ Premium expiry checker
async def start_check_premium_expiry(bot_instance):
    while True:
        try:
            await check_premium_expiry(bot_instance)
            print("✅ Checked expired premium accounts.")
        except Exception:
            print(f"❌ Premium expiry error:\n{traceback.format_exc()}")
        await asyncio.sleep(1100)

# 🧹 Cleanup envelopes
async def schedule_cleanup(bot_instance):
    while True:
        try:
            await cleanup_expired_envelopes(bot_instance)
            print("🧹 Envelope cleanup done.")
        except Exception:
            print(f"❌ Envelope cleanup error:\n{traceback.format_exc()}")
        await asyncio.sleep(3600)

# 🎁 Giveaway system
async def giveaway_scheduler(bot_instance):
    while True:
        try:
            await pick_giveaway_winners(bot_instance)
        except Exception:
            print(f"❌ Giveaway error:\n{traceback.format_exc()}")
        await asyncio.sleep(300)

# 📦 Old media cleanup
async def delete_old_media_task(bot_instance):
    while True:
        try:
            await delete_old_media(bot_instance)
            print("🗑️ Old media cleaned.")
        except Exception:
            print(f"❌ Old media cleanup error:\n{traceback.format_exc()}")
        await asyncio.sleep(3600)

# 🧠 Main runner
async def main():
    bot = Bot()
    await bot.start()
    print("🚀 NʏxDesire Bot is now live!")

    await load_periodic_messages(bot)
    print("📢 Periodic messages loaded.")

    await fetch_and_cache_user_data(bot)

    asyncio.create_task(start_check_premium_expiry(bot))
    asyncio.create_task(schedule_cleanup(bot))
    asyncio.create_task(giveaway_scheduler(bot))
    asyncio.create_task(delete_old_media_task(bot))
    asyncio.create_task(reset_daily_free_media(bot))
    asyncio.create_task(refresh_cache_periodically(bot))

    try:
        await store_video_message_ids(bot, CHANNEL_ID)
        print("🎥 Video IDs stored.")
    except Exception:
        print(f"❌ Video ID storage error:\n{traceback.format_exc()}")

    await idle()
    print("🛑 Bot shutdown signal received.")
    await bot.stop()

# 🔄 Restart utility
async def restart_bot():
    print("🔁 Restarting bot in 5 seconds...")
    await asyncio.sleep(5)
    subprocess.run([sys.executable, sys.argv[0]])

# 🧠 Entry point
if __name__ == "__main__":
    try:
        import nest_asyncio
        nest_asyncio.apply()

        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("🧹 Gracefully shutting down bot (Ctrl+C detected)...")
        sys.exit(0)
    except Exception:
        print(f"🔥 Unexpected crash:\n{traceback.format_exc()}")
        asyncio.run(restart_bot())
