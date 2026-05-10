import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler, ChatMemberHandler
from app.config import BOT_TOKEN
from app.handlers.scheduler import build_ffpost_handler, build_approval_handler
from app.handlers.thismonth import build_ffthismonth_handler
from app.handlers.purge import build_purge_handler
from app.handlers.ffremove import build_ffremove_handler
from app.handlers.main import start, FFPing, FFHelp, handle_bot_added_to_group

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("FFPing", FFPing))
    app.add_handler(CommandHandler("FFHelp", FFHelp))
    app.add_handler(build_approval_handler())
    app.add_handler(build_ffpost_handler())
    app.add_handler(build_ffthismonth_handler())
    app.add_handler(build_purge_handler())
    for handler in build_ffremove_handler():
        app.add_handler(handler)
    app.add_handler(ChatMemberHandler(handle_bot_added_to_group, ChatMemberHandler.MY_CHAT_MEMBER))

    async with app:
        await app.start()
        await app.updater.start_polling()
        await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())