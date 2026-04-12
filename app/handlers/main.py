import logging
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from app.handlers.scheduler import build_ffpost_handler, build_approval_handler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("FFBot is Running")

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("FruityFur Bot is online and working. Version 1.0 Alpha")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Use /FFPost in a group to create a new event.\n"
        "Reply to each prompt for Header, Description, Date/Time, Location, and optional pictures.\n"
        "The bot will send an approval request to @thenightweaver (bot's owner) after the group post is created.\n"
        "Use /cancel during event creation to stop, and /skip to continue without pictures.\n"
        "Use /Ping to check if the bot is working."
    )

def main():
    load_dotenv()
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN is not set in the environment variables.")
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler(["Ping_at", "Ping"], ping))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(build_ffpost_handler())
    app.add_handler(build_approval_handler())
    logger.info("FFBot is Running")
    app.run_polling()

if __name__ == "__main__":  
    main() 
