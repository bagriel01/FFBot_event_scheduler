import logging
from datetime import datetime as dt
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallBackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from app.handlers.thismonth_storage import save_post 

from app.config import ADMIN_USER_IDS, APPROVED_EVENT_CHANNEL_ID    

logger = logging.getLogger(__name__)


FFPOST_DATETIME = 0 

#Helpers

def parse_channel_id(channel_id_str):
    value = value.strip()
    if value.startswith('-') and value[1:].isdigit():
        return int(value)
    if value.isdigit():
        return int(value)
    return value
#Resolve o ID do canal para um formato aceitável

def get_approver_ids(update: Update) -> list[int]:
    if ADMIN_USER_IDS:
        return ADMIN_USER_IDS

    if update.effective_user:
        return [update.effective_user.id]

    return []
#Recebe o aprovador do evento via ADMIN_USER_IDS 

async def is_user_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    user = update.effective_user
    if not chat or user:
        return False
    administrators = await context.bot.get.chat_administrators(chat.id)
    return any (member.user.id and member.user.id == user.id for member in administrators)

#Valida se o usuário é administrador do grupo
def build_google_calendar_link(title: str, event_datetime: dt) -> str:
    start = event_datetime.strftime("%Y%m%dT%H%M%S")
    params = {
        "action": "TEMPLATE",
        "text": title,
        "dates": f"{start}/{start}",
    }
    return f"https://www.google.com/calendar/render?{urlencode(params)}"
#Constroi o formato do link do google calendar para o evento
#/endHelpers


async def ffpost(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat = update.effective_chat
    message = update.message
 
    if chat.type not in ("group", "supergroup"):
        await message.reply_text("/FFPost só pode ser utilizado em grupos, sowwy owo.")
        return ConversationHandler.END
 
    if not await is_user_admin(update, context):
        await message.reply_text("Somente administradores podem usar /FFPost, sowwy uwu.")
        return ConversationHandler.END
 
    if not message.reply_to_message:
        await message.reply_text("Oops, você precisa responder a uma mensagem para usar /FFPost! Tente novamente owo.")
        return ConversationHandler.END
 
    replied = message.reply_to_message
    chat_username = chat.username
    group_link = f"https://t.me/{chat_username}" if chat_username else None
 
    #contexto para ser resolvido via dm
    context.user_data["ffpost_replied_id"] = replied.message_id
    context.user_data["ffpost_chat_id"] = chat.id
    context.user_data["ffpost_group_link"] = group_link
 
    await message.reply_text("Te chamei na DM para concluirmos a publicação do post.")
 
    #abre a conversa na DM
    user = update.effective_user
    await context.bot.send_message(
        chat_id=user.id,
        text=(
            "Respondendo o post encaminhado, digite a data e hora do seu evento "
            "no seguinte formato:\n\n"
            "*DIA/MÊS/ANO - HORA:MINUTO*\n"
            "_(exemplo: 01/01/2026 - 13:00)_"
        ),
        parse_mode="Markdown",
    )
 
    return FFPOST_DATETIME
 
async def ffpost_dm_forward(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = update.message
    chat = update.effective_chat
 
    if chat.type != "private":
        return ConversationHandler.END
 
    if not message.forward_origin and not message.forward_from_chat and not message.forward_date:
        return ConversationHandler.END
 
    forward_chat = getattr(message.forward_from_chat, "id", None)
    forward_message_id = getattr(message, "forward_from_message_id", None)
 
    context.user_data["ffpost_replied_id"] = forward_message_id or message.message_id
    context.user_data["ffpost_chat_id"] = forward_chat or message.chat_id
    context.user_data["ffpost_dm_message_id"] = message.message_id
    context.user_data["ffpost_group_link"] = None
 
    await message.reply_text(
        "Respondendo o post encaminhado, digite a data e hora do seu evento "
        "no seguinte formato:\n\n"
        "*DIA/MÊS/ANO - HORA:MINUTO*\n"
        "_(exemplo: 01/01/2026 - 13:00)_",
        parse_mode="Markdown",
    )
 
    return FFPOST_DATETIME
 
async def ffpost_receive_datetime(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    raw = update.message.text.strip()
 
    # Valida e faz o parse do formato DD/MM/YYYY - HH:MM
    try:
        event_datetime = dt.strptime(raw, "%d/%m/%Y - %H:%M")
    except ValueError:
        await update.message.reply_text(
            "Formato inválido. Por favor use *DIA/MÊS/ANO - HORA:MINUTO*\n"
            "_(exemplo: 01/01/2026 - 13:00)_\n\n"
            "Tente novamente:",
            parse_mode="Markdown",
        )
        return FFPOST_DATETIME
 
    chat_id = context.user_data["ffpost_chat_id"]
    replied_id = context.user_data["ffpost_replied_id"]
    group_link = context.user_data.get("ffpost_group_link")
 

    gcal_date = event_datetime.strftime("%m/%d/%Y")
    gcal_link = build_google_calendar_link(
        title="Evento FruityFur",
        event_datetime=event_datetime,
    )
 
    request_id = f"{chat_id}:{replied_id}"
    channel_id = parse_channel_id(APPROVED_EVENT_CHANNEL_ID) if APPROVED_EVENT_CHANNEL_ID else None
 
    pending = context.bot_data.setdefault("pending_approvals", {})
    pending[request_id] = {
        "group_chat_id": chat_id,
        "message_id": replied_id,
        "channel_id": channel_id,
        "event_datetime": event_datetime.strftime("%d/%m/%Y %H:%M"),
        "gcal_link": gcal_link,
        "submitter_id": update.effective_user.id,
    }

    approver_ids = get_approver_ids(update)
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Aprovar", callback_data=f"approve:{request_id}"),
        InlineKeyboardButton("❌ Rejeitar", callback_data=f"reject:{request_id}"),
    ]])
 
    for approver_id in approver_ids:
        try:
            await context.bot.forward_message(
                chat_id=approver_id,
                from_chat_id=chat_id,
                message_id=replied_id,
            )
            await context.bot.send_message(
                chat_id=approver_id,
                text=(
                    f"📋 *Novo evento para aprovação*\n"
                    f"📆 Data: {event_datetime.strftime('%d/%m/%Y às %H:%M')}\n\n"
                    "Aprovar ou rejeitar este evento?"
                ),
                parse_mode="Markdown",
                reply_markup=keyboard,
            )
        except Exception:
            logger.exception("Falha ao encaminhar para o aprovador %s", approver_id)
 
    await update.message.reply_text(
        "✅ Obrigado! O aprovador irá revisar o post e aprovar ou recusar o evento em breve.",
    )
 
    context.user_data.clear()
    return ConversationHandler.END
 
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
        channel_id = approval.get("channel_id")
        group_chat_id = approval["group_chat_id"]
        message_id = approval["message_id"]
        gcal_link = approval["gcal_link"]
        event_datetime = dt.strptime(approval["event_datetime"], "%d/%m/%Y %H:%M")
 
        if channel_id:
            forwarded = await context.bot.forward_message(
                chat_id=channel_id,
                from_chat_id=group_chat_id,
                message_id=message_id,
            )
 
            #Botão do Google callendar
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    text="📅 Quero participar do evento",
                    url=gcal_link,
                )
            ]])
            await context.bot.send_message(
                chat_id=channel_id,
                text=f"🗓 *{event_datetime.strftime('%d/%m/%Y às %H:%M')}*",
                parse_mode="Markdown",
                reply_markup=keyboard,
            )
 
            # Salva no JSON para o /FFThisMonth
            save_post(
                date=event_datetime,
                message_id=forwarded.message_id,
                chat_id=channel_id,
                source_chat_id=group_chat_id,
                source_message_id=message_id,
            )
 
        await query.edit_message_text("✅ Evento aprovado e publicado no canal!")
 
        await context.bot.send_message(
            chat_id=group_chat_id,
            text="Sucesso! Este evento foi aprovado e postado no canal https://t.me/FruityFur_Events! Cheque seu post lá!",
            reply_to_message_id=message_id,
        )
 
    else:
        #Rejeição: avisa no privado do submitter
        submitter_id = approval.get("submitter_id")
        if submitter_id:
            await context.bot.send_message(
                chat_id=submitter_id,
                text="Seu post não foi aprovado, por favor entre em contato com o desenvolvedor do bot em @thenightweaver para mais informações.",
            )
 
        await query.edit_message_text("❌ Evento rejeitado.")
 
    pending.pop(request_id, None)
 
 
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("Operação cancelada.")
    return ConversationHandler.END
 
#builders que serão exportados para o main.py


def build_ffpost_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("FFPost", ffpost),
            MessageHandler(filters.FORWARDED & filters.ChatType.PRIVATE, ffpost_dm_forward),
        ],
        states={
            FFPOST_DATETIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ffpost_receive_datetime)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )
 
 
def build_approval_handler() -> CallbackQueryHandler:
    return CallbackQueryHandler(
        handle_approval_callback,
        pattern=r"^(approve|reject):",
    )
 
#/end builders
