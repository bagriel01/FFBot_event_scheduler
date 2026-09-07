import logging
from urllib.parse import urlencode
from datetime import datetime as dt
from telegram.error import TelegramError
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from app.handlers.thismonth_storage import save_post 
from app.dicts.schedulerBR import (               #change this dict to schedulerEN to translate the bot to english. 
    FFPOST_NOTGROUP, FFPOST_NOTADMIN, FFPOST_NOREPLY,
    FFPOST_DM_FORWARD, FFPOST_DATETIME_PROMPT, FFPOST_DATETIME_INVALID,
    FFPOST_PENDING_APPROVAL, FFPOST_APPROVED, FFPOST_APPROVED_TXT,
    FFPOST_REJECTED, FFPOST_CANCELLED, FFPOST_REJECTED_TXT, FFPOST_CALLENDAR_BTN
) 
from app.config import ADMIN_USER_IDS, APPROVED_EVENT_CHANNEL_ID    

logger = logging.getLogger(__name__)


FFPOST_DATETIME = 0 

#Helpers

def parse_channel_id(channel_id_str):
    value = channel_id_str.strip()
    if value.startswith('-') and value[1:].isdigit():
        return int(value)
    if value.isdigit():
        return int(value)
    return value
#Resolves the channel ID from the config

def get_approver_ids(update: Update) -> list[int]:
    if ADMIN_USER_IDS:
        return ADMIN_USER_IDS

    if update.effective_user:
        return [update.effective_user.id]

    return []
#Receives the list of approvers from the config or defaults to the user who initiated the command

async def is_user_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user:
        return False
    administrators = await context.bot.get_chat_administrators(chat.id)
    return any (member.user and member.user.id == user.id for member in administrators)
#Validades if the user is an admin in the group where the command was issued

def build_google_calendar_link(title: str, event_datetime: dt) -> str:
    start = event_datetime.strftime("%Y%m%dT%H%M%S")
    params = {
        "action": "TEMPLATE",
        "text": title,
        "dates": f"{start}/{start}",
    }
    return f"https://www.google.com/calendar/render?{urlencode(params)}"
#Builds the Google Calendar link format for the event
#/endHelpers


async def ffpost(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat = update.effective_chat
    message = update.message
    user = update.effective_user

    if chat.type not in ("group", "supergroup"):
        await message.reply_text(FFPOST_NOTGROUP)
        return ConversationHandler.END
 
    if not await is_user_admin(update, context):
        await message.reply_text(FFPOST_NOTADMIN)
        return ConversationHandler.END
 
    if not message.reply_to_message:
        await message.reply_text(FFPOST_NOREPLY)
        return ConversationHandler.END
 
    replied = message.reply_to_message
    chat_username = chat.username
 
    
    context.user_data["ffpost_replied_id"] = replied.message_id
    context.user_data["ffpost_chat_id"] = chat.id
    context.user_data["ffpost_author"] = user.full_name or user.username
 

    await message.reply_text(FFPOST_DM_FORWARD)
 
    await context.bot.forward_message(
        chat_id=user.id,
        from_chat_id=chat.id,
        message_id=replied.message_id,
    )

    await context.bot.send_message(
        chat_id=user.id,
        text=(
            FFPOST_DATETIME_PROMPT
        ),
        parse_mode="Markdown",
    )
 
    return FFPOST_DATETIME
 

async def ffpost_dm_forward(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = update.message
    chat = update.effective_chat
 
    if chat.type != "private":
        return ConversationHandler.END
 
    if not message.forward_origin:
        return ConversationHandler.END

    origin = message.forward_origin
    forward_chat = None
    forward_message_id = None
 
    if hasattr(origin, "chat"):          # MessageOriginChannel / MessageOriginChat
        forward_chat = origin.chat.id
        forward_message_id = getattr(origin, "message_id", None)
    elif hasattr(origin, "sender_chat"): # MessageOriginHiddenUser with sender_chat
        forward_chat = origin.sender_chat.id
 
    context.user_data["ffpost_replied_id"] = forward_message_id or message.message_id
    context.user_data["ffpost_chat_id"] = forward_chat or message.chat_id
    context.user_data["ffpost_dm_message_id"] = message.message_id
    context.user_data["ffpost_group_link"] = None
 
    await message.reply_text(
        FFPOST_DATETIME_PROMPT,
        parse_mode="Markdown",
    )
 
    return FFPOST_DATETIME
 
 

async def ffpost_receive_datetime(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    raw = update.message.text.strip()
 
    #Validates and parse the date format
    try:
        event_datetime = dt.strptime(raw, "%d/%m/%Y - %H:%M")
    except ValueError:
        await update.message.reply_text(
            FFPOST_DATETIME_INVALID,
            parse_mode="Markdown",
        )
        return FFPOST_DATETIME
 
    chat_id = context.user_data["ffpost_chat_id"]
    replied_id = context.user_data["ffpost_replied_id"]
    author = context.user_data.get("ffpost_author", "FruityFur Bot")
    gcal_link = build_google_calendar_link(
        title="Evento Agendado por {author}",
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
        "author": author,
    }

    approver_ids = get_approver_ids(update)
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ ", callback_data=f"approve:{request_id}"),
        InlineKeyboardButton("❌ ", callback_data=f"reject:{request_id}"),
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
                    f"📆 Event: {event_datetime.strftime('%d/%m/%Y às %H:%M')}\n\n"
                    
                ),
                parse_mode="Markdown",
                reply_markup=keyboard,
            )
        except TelegramError:
            logger.exception("Falha ao encaminhar para o aprovador %s", approver_id)
 
    await update.message.reply_text(
        FFPOST_PENDING_APPROVAL,
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
        await query.edit_message_text("Request Expired.")
        return
 
    if action == "approve":
        channel_id = approval.get("channel_id")
        group_chat_id = approval["group_chat_id"]
        message_id = approval["message_id"]
        gcal_link = approval["gcal_link"]
        author = approval.get("author", "Desconhecido")
        event_datetime = dt.strptime(approval["event_datetime"], "%d/%m/%Y %H:%M")
 
        if channel_id:
            forwarded = await context.bot.forward_message(
                chat_id=channel_id,
                from_chat_id=group_chat_id,
                message_id=message_id,
            )
 
            #google calendar button
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    text=FFPOST_CALLENDAR_BTN,
                    url=gcal_link,
                )
            ]])
            await context.bot.send_message(
                chat_id=channel_id,
                text=f"🗓 *{event_datetime.strftime('%d/%m/%Y às %H:%M')}*",
                parse_mode="Markdown",
                reply_markup=keyboard,
            )
 
            # Saves the post to the storage for /FFThisMonth command
            save_post(
                date=event_datetime,
                message_id=forwarded.message_id,
                chat_id=channel_id,
                source_chat_id=group_chat_id,
                source_message_id=message_id,
                author=author,
            )
 
        await query.edit_message_text(FFPOST_APPROVED)
 
        await context.bot.send_message(
            chat_id=group_chat_id,
            text=FFPOST_APPROVED_TXT,
            reply_to_message_id=message_id,
        )
 
    else:
        #rejected, notifying the submitter
        submitter_id = approval.get("submitter_id")
        if submitter_id:
            await context.bot.send_message(
                chat_id=submitter_id,
                text=FFPOST_REJECTED_TXT,
            )
 
        await query.edit_message_text(FFPOST_REJECTED)
 
    pending.pop(request_id, None)
 
 
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(FFPOST_CANCELLED)
    return ConversationHandler.END
 
#builders that will be exported to main.py to be added to the application


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
        per_chat=False,
    )
 
 
def build_approval_handler() -> CallbackQueryHandler:
    return CallbackQueryHandler(
        handle_approval_callback,
        pattern=r"^(approve|reject):",
    )
 
#/end builders
