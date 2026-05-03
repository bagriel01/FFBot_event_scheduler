import logging
from datetime import datetime as dt
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from app.handlers.thismonth_storage import get_posts_this_month

logger = logging.getLogger(__name__)

async def is_user_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user:
        return False
    administrators = await context.bot.get_chat_administrators(chat.id)
    return any(member.user and member.user.id == user.id for member in administrators)

async def ffthismonth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    if chat.type not in ("group", "supergroup"):
        await update.message.reply_text("/FFThisMonth só pode ser utilizado em grupos, sowwy owo")
        return

    if not await is_user_admin(update, context):
        await update.message.reply_text("Somente administradores podem usar /FFThisMonth, sowwy uwu")
        return

    now = dt.now()
    posts = get_posts_this_month(now.year, now.month)

    if not posts:
        await update.message.reply_text("Não há eventos agendados para este mês ainda. Agende o seu com @FruityFur_Bot! :3")
        return
    await update.message.reply_text(
        f"Events for {now.strftime('%B %Y')}:",
        parse_mode="Markdown"
    )
    for day, entry in posts:
        await context.bot.forward_message(
            chat_id=update.effective_chat.id,
            from_chat_id=entry["chat_id"],
            message_id=entry["message_id"],
        )
def build_ffthismonth_handler() -> CommandHandler:
    return CommandHandler("FFThisMonth", ffthismonth)