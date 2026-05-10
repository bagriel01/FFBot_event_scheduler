import logging
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from app.config import ADMIN_USER_IDS
from app.handlers.thismonth_storage import purge_all

logger = logging.getLogger(__name__)


async def ffpurge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type != "private":
        await update.message.reply_text("/Purge só pode ser utilizado na DM do bot.")
        return

    if not ADMIN_USER_IDS or user.id not in ADMIN_USER_IDS:
        await update.message.reply_text("Você não tem permissão para usar /Purge.")
        return

    purge_all()
    await update.message.reply_text("✅ Registro de eventos limpo com sucesso.")


def build_purge_handler() -> CommandHandler:
    return CommandHandler("Purge", ffpurge)