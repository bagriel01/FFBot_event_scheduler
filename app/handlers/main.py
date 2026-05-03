import logging
import asyncio
from datetime import datetime as dt
import pytz
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import app
from app.config import BOT_TOKEN, WEBHOOK_URL, PORT
from app.handlers.scheduler import build_ffpost_handler, build_approval_handler
from app.handlers.thismonth import build_ffthismonth_handler
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Boas vindas e obrigado por utilizar o FFBot! Para começar, me adicione no seu grupo e me dê as permissões de ADM (todas). Prometo não fazer nada malicioso uwu.")


async def FFPing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tz = pytz.timezone("America/Sao_Paulo")
    now = dt.now(tz)
    await update.message.reply_text(f"Bot está online, Data: {now.strftime('%d/%m/%Y %H:%M')} (Horário de Brasília). Versão atual do bot é 1.1.3L (Banana-Sorbet)")

async def FFHelp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
       
        "📨 */FFPost*\n"
        "Use essa função para criar o evento.\n\n"
        "Crie um post em seu grupo contendo as informações de evento;\n\n"
        "Responda a mensagem do evento com /FFPost para agendar a publicação do evento pelo bot;\n\n"
        "O bot irá solicitar a data do evento e enviará o post para ser aprovado!\n\n"

        "📅 */FFThisMonth*\n"
        "Use essa função para mostrar os eventos do mês atual publicados pelo bot.\n\n"

        "⛔ */cancel*\n"
        "Cancela a função de criação de evento.\n\n"

        "🏓 */FFPing*\n"
        "Verifica se o bot está online e mostra a versão atual.\n\n"

        "⚠️ Notas: \n"
        "- /FFPost e /FFThisMonth só funcionam em grupos.\n"
        "- Apenas administradores do grupo podem usar as funções.\n"
        "- Certifique-se de que o bot tenha permissão para fixar mensagens\n",)


def main():
    if not BOT_TOKEN:
        raise RuntimeError("Epic Sadface: BOT_TOKEN não está definido. GG")

    if not WEBHOOK_URL:
        raise RuntimeError("Epic Sadface: WEBHOOK_URL não está definido. GG")

    app = ApplicationBuilder().token(BOT_TOKEN).build()


    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("FFPing", FFPing))
    app.add_handler(CommandHandler("FFHelp", FFHelp))
    app.add_handler(build_approval_handler())
    app.add_handler(build_ffpost_handler())
    app.add_handler(build_ffthismonth_handler())

    webhook_path = f"/webhook/{BOT_TOKEN}"
    webhook_url = f"{WEBHOOK_URL}{webhook_path}"

    logger.info(f"Iniciando Webhook em {webhook_url}")


    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=webhook_path,
        webhook_url=webhook_url,
    )


if __name__ == "__main__":
    main()
