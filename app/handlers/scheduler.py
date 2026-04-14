import logging
from datetime import datetime
from multiprocessing import context
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
NEWPOST_TEXT, NEWPOST_PICTURES = range(2)


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

async def ffnewpost_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat = update.effective_chat

    if chat.type not in ("group", "supergroup"):
        await update.message.reply_text("/FFNewPost can only be used in groups.")
        return ConversationHandler.END

    if not await is_user_admin(update, context):
        await update.message.reply_text(
            "Sowwy, only group administrators can create event posts :c"
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Please provide all event details in one message, copy and paste the following format and fill your info!:\n\n"
        "Header: [Event Name]\n"
        "Description: [Event Description]\n"
        "Date: [DD/MM/YYYY HH:MM]\n"
        "Location: [Location with Google Maps link]\n\n"
        "Reply to this message with the details."
    )
    return NEWPOST_TEXT


async def newpost_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    

    lines = text.split('\n')
    data = {}
    for line in lines:
        if line.startswith('Header:'):
            data['name'] = line.replace('Header:', '').strip()
        elif line.startswith('Description:'):
            data['description'] = line.replace('Description:', '').strip()
        elif line.startswith('Date:'):
            data['datetime'] = line.replace('Date:', '').strip()
        elif line.startswith('Location:'):
            data['location'] = line.replace('Location:', '').strip()
    

    if not all(key in data for key in ['name', 'description', 'datetime', 'location']):
        await update.message.reply_text(
            "Invalid format. Please include Header, Description, Date, and Location or type /cancel to abort."
        )
        return NEWPOST_TEXT
    

    try:
        datetime.strptime(data['datetime'], "%d/%m/%Y %H:%M")
    except ValueError:
        await update.message.reply_text(
            "Invalid date format. Use DD/MM/YYYY HH:MM."
        )
        return NEWPOST_TEXT
    
    context.user_data.update(data)
    context.user_data["photo_file_ids"] = []

    await update.message.reply_text(
        "Details saved. Send one or more pictures to illustrate the event, or type /skip if you want to continue without pictures."
    )
    return NEWPOST_PICTURES


async def newpost_pictures(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    photos = update.message.photo
    if not photos:
        await update.message.reply_text(
            "Please send a photo or type /skip to continue without pictures."
        )
        return NEWPOST_PICTURES

    file_id = photos[-1].file_id
    context.user_data.setdefault("photo_file_ids", []).append(file_id)
    await update.message.reply_text(
        "Picture saved. Send more photos, or type /confirm when you are ready."
    )
    return NEWPOST_PICTURES


async def skip_pictures(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.setdefault("photo_file_ids", [])
    await update.message.reply_text(
        "No pictures will be included. Type /confirm to publish or /cancel to abort."
    )
    return NEWPOST_PICTURES


async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    
    chat = update.effective_chat
    chat_id = chat.id
    event_name = context.user_data["name"]
    event_description = context.user_data.get("description", "")
    event_datetime = context.user_data["datetime"]
    event_location = context.user_data["location"]
    photo_file_ids = context.user_data.get("photo_file_ids", [])

    group_address = (
        f"https://t.me/{chat.username}" if chat.username else None
    )

    post_text = (
        f"*{event_name}*\n"
        f"*Description:* {event_description}\n"
        f"*When:* {event_datetime}\n"
        f"*Where:* {event_location}\n"
    )
    if group_address:
        post_text += f"*Group:* {group_address}\n"

    if photo_file_ids:
        media = [
            InputMediaPhoto(media=file_id, caption=post_text if i == 0 else None)
            for i, file_id in enumerate(photo_file_ids)
        ]
        sent_messages = await context.bot.send_media_group(
            chat_id=chat_id,
            media=media,
        )
        sent_message_id = sent_messages[0].message_id
        await context.bot.pin_chat_message(chat_id=chat_id, message_id=sent_message_id)
    else:
        sent_message = await context.bot.send_message(
            chat_id=chat_id,
            text=post_text,
            parse_mode="Markdown",
        )
        sent_message_id = sent_message.message_id
        await context.bot.pin_chat_message(chat_id=chat_id, message_id=sent_message_id)

    approver_ids = get_approver_ids(update)
    request_id = f"{chat_id}:{sent_message_id}"
    approval_status = ""

    channel_id = None
    if APPROVED_EVENT_CHANNEL_ID:
        channel_id = parse_channel_id(APPROVED_EVENT_CHANNEL_ID)

    if approver_ids:
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Approve", callback_data=f"approve:{request_id}"),
                    InlineKeyboardButton("Reject", callback_data=f"reject:{request_id}"),
                ]
            ]
        )

        approval_text = post_text

        failed_approvals = []
        for approver_id in approver_ids:
            try:
                await context.bot.forward_message(
                    chat_id=approver_id,
                    from_chat_id=chat_id,
                    message_id=sent_message_id
                )
                await context.bot.send_message(
                    chat_id=approver_id,
                    text="Approve or reject this event?",
                    reply_markup=keyboard,
                )
            except Exception:
                logger.exception("Failed to send approval DM to %s", approver_id)
                failed_approvals.append(approver_id)

        approval_status = " Approval request was sent to the approver's DM."
        if failed_approvals:
            approval_status += (
                " However, some approver DMs failed. Make sure those users have started a chat with the bot."
            )

        if not APPROVED_EVENT_CHANNEL_ID:
            approval_status += " No approval destination channel is configured yet."
    else:
        approval_status = (
            " No approver IDs are configured, so approval request was not sent."
        )
        
    pending = context.bot_data.setdefault("pending_approvals", {})

    pending[request_id] = {
    "group_chat_id": chat.id,
    "message_id": sent_message_id.message_id,
    "channel_id": channel_id,
}
    context.user_data.clear()
    await update.message.reply_text(
        f"Event posted and pinned successfully.{approval_status}"
    )
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
        await query.edit_message_text(
            "This approval request is no longer available."
        )
        return

    if action == "approve":
        if approval.get("channel_id"):
            await context.bot.forward_message(
                chat_id=approval["channel_id"],
                from_chat_id=approval["group_chat_id"],
                message_id=approval["message_id"]
            )
            await query.edit_message_text("✅ Event approved and forwarded to the channel.")
            await context.bot.send_message(
                chat_id=approval["group_chat_id"],
                text="The event has been approved and published at https://t.me/FruityFur_Events! Check it out there!",
            )
        else:
            await query.edit_message_text(
                "✅ Event approved, but no approval destination channel is configured."
            )
            await context.bot.send_message(
                chat_id=approval["group_chat_id"],
                text="The event has been approved, but the approval channel is not configured.",
            )
    else:
        await query.edit_message_text("❌ Event rejected and will not be sent to the channel.")
        await context.bot.send_message(
            chat_id=approval["group_chat_id"],
            text="The event was rejected by the approver. Contact the bot owner at @thenightweaver for more info.",
        )

    pending.pop(request_id, None)
    print("REQUEST ID:", request_id)
    print("PENDING:", context.bot_data.get("pending_approvals"))


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("Event creation canceled.")
    return ConversationHandler.END


def build_ffnewpost_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("FFNewPost", ffnewpost_start)],
        states={
            NEWPOST_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, newpost_text)],
            NEWPOST_PICTURES: [
                MessageHandler(filters.PHOTO, newpost_pictures),
                CommandHandler("skip", skip_pictures),
                CommandHandler("confirm", confirm),
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


async def ffpost(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    user = update.effective_user
    message = update.message

    if chat.type not in ("group", "supergroup"):
        await update.message.reply_text("/FFPost can only be used in groups.")
        return

    if not await is_user_admin(update, context):
        await update.message.reply_text("Only group administrators can use /FFPost.")
        return

    if not message.reply_to_message:
        await update.message.reply_text("Please reply to the message you want to post for approval.")
        return

    replied = message.reply_to_message
    post_text = replied.text or ""
    photo_file_ids = [photo.file_id for photo in replied.photo] if replied.photo else []

    group_address = f"https://t.me/{chat.username}" if chat.username else None

    if group_address and post_text:
        post_text += f"\n\n*Group:* {group_address}"

    # Pin the message
    await context.bot.pin_chat_message(chat_id=chat.id, message_id=replied.message_id)

    # Send for approval
    approver_ids = get_approver_ids(update)
    request_id = f"{chat.id}:{replied.message_id}"
    approval_status = ""

    channel_id = None
    if APPROVED_EVENT_CHANNEL_ID:
        channel_id = parse_channel_id(APPROVED_EVENT_CHANNEL_ID)

    if approver_ids:
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Approve", callback_data=f"approve:{request_id}"),
                    InlineKeyboardButton("Reject", callback_data=f"reject:{request_id}"),
                ]
            ]
        )

        approval_text = post_text if post_text else "Image event pending approval"

        failed_approvals = []
        for approver_id in approver_ids:
            try:
                await context.bot.forward_message(
                    chat_id=approver_id,
                    from_chat_id=chat.id,
                    message_id=replied.message_id
                )
                await context.bot.send_message(
                    chat_id=approver_id,
                    text="Approve or reject this event?",
                    reply_markup=keyboard,
                )
            except Exception:
                logger.exception("Failed to send approval DM to %s", approver_id)
                failed_approvals.append(approver_id)

        pending = context.bot_data.setdefault("pending_approvals", {})
    pending[request_id] = {
    "group_chat_id": chat.id,
    "message_id": replied.message_id,
    "channel_id": channel_id,
}

    approval_status = " Approval request was sent to the approver's DM."
    if failed_approvals:
            approval_status += " However, some approver DMs failed. Make sure those users have started a chat with the bot."
    else:
        approval_status = " No approver IDs are configured, so approval request was not sent."

    await update.message.reply_text(f"Message pinned and sent for approval.{approval_status}")


def build_ffpost_handler() -> CommandHandler:
    return CommandHandler("FFPost", ffpost)
