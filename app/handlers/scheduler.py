import logging
from datetime import datetime as dt
from multiprocessing import context
from app.handlers.thismonth_storage import save_post
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from app.config import ADMIN_USER_IDS, APPROVED_EVENT_CHANNEL_ID

logger = logging.getLogger(__name__)
NEWPOST_TEXT, NEWPOST_PICTURES , FFPOST_DATE = range(3)

def parse_channel_id(value: str):
    value = value.strip()
    if value.startswith("-") and value[1:].isdigit():
        return int(value)
    if value.isdigit():
        return int(value)
    return value


def get_approver_ids(update: Update) -> list[int]:
    if ADMIN_USER_IDS:
        return ADMIN_USER_IDS

    if update.effective_user:
        return [update.effective_user.id]

    return []


async def is_user_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    user = update.effective_user

    if not chat or not user:
        return False

    administrators = await context.bot.get_chat_administrators(chat.id)
    return any(member.user and member.user.id == user.id for member in administrators)

async def handle_approval_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not query.data:
        return

    await query.answer()
    action, request_id = query.data.split(":", 1)
    pending = context.bot_data.get("pending_approvals", {})
    approval = pending.get(request_id)

    if not approval:
        await query.edit_message_text("Esse request não está mais disponível.")
        return

    if action == "approve":
        if approval.get("channel_id"):
            forwarded = await context.bot.forward_message(
                chat_id=approval["channel_id"],
                from_chat_id=approval["group_chat_id"],
                message_id=approval["message_id"]
            )
            event_date = dt.strptime(approval["event_date"], "%d/%m/%Y")
            save_post(
                date=event_date,
                message_id=forwarded.message_id,
                chat_id=approval["channel_id"],
            )
            await query.edit_message_text("✅ Evento aprovado e publicado no canal!")
            await context.bot.send_message(
                chat_id=approval["group_chat_id"],
                text="O evento foi aprovado e encaminhado para o canal https://t.me/FruityFur_Events! cheque seu post lá!",
            )
    else:
        await query.edit_message_text("❌ Evento rejeitado e não será enviado para o canal.")
        await context.bot.send_message(
            chat_id=approval["group_chat_id"],
            text="O evento foi rejeitado pelo aprovador. Entre em contato com o proprietário do bot em @thenightweaver para mais informações.",
        )

    pending.pop(request_id, None)


def build_approval_handler() -> CallbackQueryHandler:
    return CallbackQueryHandler(
        handle_approval_callback,
        pattern=r"^(approve|reject):",
    )

async def ffpost(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat = update.effective_chat
    message = update.message

    if chat.type not in ("group", "supergroup"):
        await update.message.reply_text("/FFPost só pode ser utilizado em grupos, sowwy owo")
        return ConversationHandler.END

    if not await is_user_admin(update, context):
        await update.message.reply_text("Somente administradores podem usar /FFPost, sowwy uwu")
        return ConversationHandler.END

    if not message.reply_to_message:
        await update.message.reply_text("Oops, você precisa responder a uma mensagem para usar /FFPost! tente novamente owo")
        return ConversationHandler.END 

    replied = message.reply_to_message
    post_text = replied.text or ""
    photo_file_ids = [photo.file_id for photo in replied.photo] if replied.photo else []

    group_address = f"https://t.me/{chat.username}" if chat.username else None
    if group_address and post_text:
        post_text += f"\n\n*Group:* {group_address}"
    context.user_data["ffpost_replied_id"] = replied.message_id
    context.user_data["ffpost_chat_id"] = chat.id
    context.user_data["ffpost_post_text"] = post_text

    sent = await update.message.reply_text(
        "Por favor, responda essa mensagem com a data do seu evento no formato DD/MM/AAAA:"
    )
    context.user_data["ffpost_expected_reply"] = sent.message_id

    return FFPOST_DATE


async def ffpost_receive_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply = update.message.reply_to_message
    expected_id = context.user_data.get("ffpost_expected_reply")

    if not reply or reply.message_id != expected_id:
        await update.message.reply_text("Oops, você deve responder à mensagem de solicitação de data. Tente novamente owo")
        return ConversationHandler.END

    try:
        post_date = dt.strptime(update.message.text.strip(), "%d/%m/%Y")
    except ValueError:
        await update.message.reply_text("Formato inválido, por favor use DD/MM/AAAA. Tente novamente owo")
        return ConversationHandler.END

    chat_id = context.user_data["ffpost_chat_id"]
    replied_id = context.user_data["ffpost_replied_id"]
    post_text = context.user_data["ffpost_post_text"]

    await context.bot.pin_chat_message(chat_id=chat_id, message_id=replied_id)

    approver_ids = get_approver_ids(update)
    request_id = f"{chat_id}:{replied_id}"

    channel_id = None
    if APPROVED_EVENT_CHANNEL_ID:
        channel_id = parse_channel_id(APPROVED_EVENT_CHANNEL_ID)

    if approver_ids:
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("Approve", callback_data=f"approve:{request_id}"),
            InlineKeyboardButton("Reject", callback_data=f"reject:{request_id}"),
        ]])

        for approver_id in approver_ids:
            try:
                await context.bot.forward_message(
                    chat_id=approver_id,
                    from_chat_id=chat_id,
                    message_id=replied_id
                )
                await context.bot.send_message(
                    chat_id=approver_id,
                    text="Aprovar ou rejeitar este evento?",
                    reply_markup=keyboard,
                )
            except Exception:
                logger.exception("Falha em encaminhar a mensagem para %s", approver_id)

        pending = context.bot_data.setdefault("pending_approvals", {})
        pending[request_id] = {
            "group_chat_id": chat_id,
            "message_id": replied_id,
            "channel_id": channel_id,
            "event_date": post_date.strftime("%d/%m/%Y"),
        }

    context.user_data.clear()
    await update.message.reply_text("Mensagem fixada e enviada para validação. Solicitação de aprovação foi enviada para a DM do dono do bot.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END

def build_ffpost_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("FFPost", ffpost)],
        states={
            FFPOST_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ffpost_receive_date)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    ) 
