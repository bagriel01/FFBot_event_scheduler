import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from app.config import BOT_TOKEN, WEBHOOK_URL, PORT
from app.handlers.scheduler import (
    build_ffnewpost_handler,
    build_ffpost_handler,
    build_approval_handler,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("FFBot is Running")


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is online.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Help message...")


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")

    if not WEBHOOK_URL:
        raise RuntimeError("WEBHOOK_URL is not set")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler(["Ping_at", "Ping"], ping))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(build_ffnewpost_handler())
    app.add_handler(build_ffpost_handler())
    app.add_handler(build_approval_handler())

    webhook_path = f"/webhook/{BOT_TOKEN}"
    webhook_url = f"{WEBHOOK_URL}{webhook_path}"

    logger.info(f"Starting webhook at {webhook_url}")

    # 🔥 CRITICAL FIX FOR PYTHON 3.14
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