import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes
from app.handlers.thismonth_storage import find_and_remove_post

logger = logging.getLogger(__name__)


async def is_user_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user:
        return False
    administrators = await context.bot.get_chat_administrators(chat.id)
    return any(member.user and member.user.id == user.id for member in administrators)


async def ffremove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.message

    if chat.type not in ("group", "supergroup"):
        await update.message.reply_text("/FFRemove só pode ser utilizado em grupos, sowwy owo")
        return

    if not await is_user_admin(update, context):
        await update.message.reply_text("Somente administradores podem usar /FFRemove, sowwy uwu")
        return

    if not message.reply_to_message:
        await update.message.reply_text("Responda a mensagem do evento que deseja remover com o comando /FFRemove.")
        return

    replied = message.reply_to_message
    source_chat_id = replied.chat.id
    source_message_id = replied.message_id

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("Confirmar Remoção", callback_data=f"ffremove_confirm:{source_chat_id}:{source_message_id}"),
        InlineKeyboardButton("Cancelar", callback_data="ffremove_cancel"),
    ]])

    await update.message.reply_text(
        "Tem certeza que deseja remover este evento? Esta ação não pode ser desfeita.",
        reply_markup=keyboard
    )


async def ffremove_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.data:
        return

    await query.answer() 

    if query.data == "ffremove_cancel":
        await query.edit_message_text("Remoção cancelada.")
        return

    _, source_chat_id_str, source_message_id_str = query.data.split(":")
    source_chat_id = int(source_chat_id_str)
    source_message_id = int(source_message_id_str)

    entry = find_and_remove_post(source_chat_id, source_message_id)
    if not entry:
        await query.edit_message_text("Evento não encontrado ou já removido.")
        return

    try:
        await context.bot.delete_message(
            chat_id=entry["chat_id"],
            message_id=entry["message_id"]
        )
    except Exception:
        logger.exception("Falha ao deletar mensagem do canal %s", entry["chat_id"])
        await query.edit_message_text("Evento removido do registro, mas não foi possível deletar a mensagem do canal. Pode ter sido deletada manualmente.")
        return

    await query.edit_message_text("Evento removido com sucesso!")


def build_ffremove_handler(): 
    return [
        CommandHandler("FFRemove", ffremove),
        CallbackQueryHandler(ffremove_callback, pattern=r"^ffremove_"),
    ]