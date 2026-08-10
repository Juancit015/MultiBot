#!/usr/bin/env python3
import logging
import os
import sys
from threading import Thread

from flask import Flask
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.request import HTTPXRequest

from bot.config import BOT_API_BASE_URL, GROQ_API_KEY, TOKEN
from bot.handlers.media import handle_media
from bot.handlers.wiki import cmd_wiki

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hola! Envíame un enlace de TikTok, Instagram o Facebook.\n"
        "Escribe find <cancion> para buscar en SoundCloud.\n"
        "Usa /wiki <consulta> para buscar información."
    )


def _validar_config():
    if not TOKEN:
        sys.exit("Error: falta la variable de entorno BOT_TOKEN")
    if not GROQ_API_KEY:
        sys.exit("Error: falta la variable de entorno GROQ_API_KEY")


def main():
    _validar_config()

    Thread(target=lambda: Flask(__name__).run(host='0.0.0.0', port=7860), daemon=True).start()
    req = HTTPXRequest(connect_timeout=30, read_timeout=300, write_timeout=300, pool_timeout=30, connection_pool_size=8)
    app = Application.builder().token(TOKEN).base_url(BOT_API_BASE_URL).request(req).concurrent_updates(True).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("wiki",  cmd_wiki))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_media))
    print("Bot corriendo...")
    app.run_polling(timeout=60)


if __name__ == '__main__':
    main()
