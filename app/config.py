import os
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("WEBHOOK_URL")
BOT_TOKEN = os.getenv("BOT_TOKEN")

APPROVED_EVENT_CHANNEL_ID = os.getenv("APPROVED_EVENT_CHANNEL_ID")

ADMIN_USER_IDS = [
    int(user_id.strip())
    for user_id in os.getenv("ADMIN_USER_IDS", "").split(",")
    if user_id.strip().isdigit()
]
PORT = os.getenv("PORT")