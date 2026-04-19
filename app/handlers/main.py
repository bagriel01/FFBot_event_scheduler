import logging
import asyncio
import datetime as dt
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from app.config import BOT_TOKEN, WEBHOOK_URL, PORT
from app.handlers.scheduler import build_ffpost_handler
from app.handlers.thismonth import build_ffthismonth_handler
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to FFBot! Add me to your group and pretty pwease give me admin permissions (all of them) so i can properly work! I promisse that i wont do anything malicious uwu")


async def FFPing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Bot is online as of {dt.datetime.now()}. Current Version is 1.1L (Banana)")


async def FFHelp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
       
        "📨 */FFPost*\n"
        "Use this by *replying to an existing message*.\n"
        "The bot will:\n"
        "- Pin the message\n"
        "- Send it for approval to admins\n\n"

        "📅 */FFThisMonth*\n"
        "Show events for the current month.\n\n"

        "⛔ */cancel*\n"
        "Cancel the current event creation process.\n\n"

        "🏓 */FFPing*\n"
        "Check if the bot is online.\n\n"

        "⚠️ Notes:\n"
        "- /FFPost and /FFThisMonth only work in groups\n"
        "- Only group admins can use /FFThisMonth\n"
        "- There's a Limit of one post a day for each group\n"
        "- Make sure the bot has permission to pin messages\n",)


def main():
    if not BOT_TOKEN:
        raise RuntimeError("Epic Sadface: BOT_TOKEN is not set. GG")

    if not WEBHOOK_URL:
        raise RuntimeError("Epic Sadface: WEBHOOK_URL is not set. GG")

    app = ApplicationBuilder().token(BOT_TOKEN).build()


    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("FFPing", FFPing))
    app.add_handler(CommandHandler("FFHelp", FFHelp))
    app.add_handler(build_ffpost_handler())
    app.add_handler(build_ffthismonth_handler())

    webhook_path = f"/webhook/{BOT_TOKEN}"
    webhook_url = f"{WEBHOOK_URL}{webhook_path}"

    logger.info(f"Starting webhook at {webhook_url}")


    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=webhook_path,
        webhook_url=webhook_url,
    )


if __name__ == "__main__":
    main()
