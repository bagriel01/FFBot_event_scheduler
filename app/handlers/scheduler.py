import logging
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
EVENT_NAME, EVENT_DESCRIPTION, EVENT_DATETIME, EVENT_LOCATION, EVENT_PICTURES = range(5)


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

async def ffpost_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat = update.effective_chat

    if chat.type not in ("group", "supergroup"):
        await update.message.reply_text("/FFPost can only be used in groups.")
        return ConversationHandler.END

    if not await is_user_admin(update, context):
        await update.message.reply_text(
            "Only group administrators can create event posts."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Great! Reply to this message to set the event Header."
    )
    return EVENT_NAME


async def event_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["event_name"] = update.message.text.strip()
    await update.message.reply_text(
        "Reply to this message to set the event Description."
    )
    return EVENT_DESCRIPTION


async def event_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["event_description"] = update.message.text.strip()
    await update.message.reply_text(
        "Reply to this message to set the event date and time (example: 2026-05-01 18:30)."
    )
    return EVENT_DATETIME


async def event_datetime(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["event_datetime"] = update.message.text.strip()
    await update.message.reply_text(
        "Reply to this message to set the event location as a Google Maps link or address."
    )
    return EVENT_LOCATION


async def event_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["event_location"] = update.message.text.strip()
    context.user_data["photo_file_ids"] = []

    await update.message.reply_text(
        "Reply to this message with one or more pictures to illustrate the event, or type /skip if you want to continue without pictures."
    )
    return EVENT_PICTURES


async def event_pictures(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    photos = update.message.photo
    if not photos:
        await update.message.reply_text(
            "Please send a photo or type /skip to continue without pictures."
        )
        return EVENT_PICTURES

    file_id = photos[-1].file_id
    context.user_data.setdefault("photo_file_ids", []).append(file_id)
    await update.message.reply_text(
        "Picture saved. Send more photos, or type /confirm when you are ready."
    )
    return EVENT_PICTURES


async def skip_pictures(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.setdefault("photo_file_ids", [])
    await update.message.reply_text(
        "No pictures will be included. Type /confirm to publish or /cancel to abort."
    )
    return EVENT_PICTURES


async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat = update.effective_chat
    chat_id = chat.id
    event_name = context.user_data["event_name"]
    event_description = context.user_data.get("event_description", "")
    event_datetime = context.user_data["event_datetime"]
    event_location = context.user_data["event_location"]
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
    def parse_channel_id(value: str):
        value = value.strip()
        if value.startswith("-") and value[1:].isdigit():
            return int(value)
        if value.isdigit():
            return int(value)
        return value

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

        approval_text = (
            "New event pending your approval:\n\n"
            f"{post_text}\n\n"
            "Tap Approve to publish it to the channel or Reject to discard it."
        )

        failed_approvals = []
        for approver_id in approver_ids:
            try:
                await context.bot.send_message(
                    chat_id=approver_id,
                    text=approval_text,
                    reply_markup=keyboard,
                    parse_mode="Markdown",
                )
            except Exception:
                logger.exception("Failed to send approval DM to %s", approver_id)
                failed_approvals.append(approver_id)

        pending = context.bot_data.setdefault("pending_approvals", {})
        pending[request_id] = {
            "post_text": post_text,
            "photo_file_ids": photo_file_ids,
            "channel_id": channel_id,
            "group_chat_id": chat_id,
        }

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
            if approval.get("photo_file_ids"):
                media = [
                    InputMediaPhoto(
                        media=file_id,
                        caption=approval["post_text"] if i == 0 else None,
                    )
                    for i, file_id in enumerate(approval["photo_file_ids"])
                ]
                await context.bot.send_media_group(
                    chat_id=approval["channel_id"],
                    media=media,
                )
            else:
                await context.bot.send_message(
                    chat_id=approval["channel_id"],
                    text=f"*Approved event:*\n\n{approval['post_text']}",
                    parse_mode="Markdown",
                )
            await query.edit_message_text("✅ Event approved and sent to the channel.")
            await context.bot.send_message(
                chat_id=approval["group_chat_id"],
                text="The event has been approved and published to https://t.me/FruityFur_Events",
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
            text="The event was rejected by the approver and was not sent to the channel.",
        )

    pending.pop(request_id, None)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("Event creation canceled.")
    return ConversationHandler.END


def build_ffpost_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("FFPost", ffpost_start)],
        states={
            EVENT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, event_name)],
            EVENT_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, event_description)],
            EVENT_DATETIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, event_datetime)],
            EVENT_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, event_location)],
            EVENT_PICTURES: [
                MessageHandler(filters.PHOTO, event_pictures),
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
