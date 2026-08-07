import logging
import shutil
import uuid

from telegram import Update
from telegram.ext import ContextTypes

from bot.config import BASE_DIR
from bot.handlers.generic import handle_video
from bot.handlers.instagram import handle_instagram_carousel
from bot.handlers.soundcloud import handle_find
from bot.handlers.tiktok import handle_tiktok_slides
from bot.services.net import resolve_short_url
from bot.utils.messaging import safe_edit
from bot.utils.text import convertir_url_facebook, get_link, limpiar_url

logger = logging.getLogger(__name__)

ERROR_RECUPERACION = (
    "⛔️ No se ha podido recuperar la información de la publicación\n\n"
    "Posibles causas:\n"
    "▫️ Cuenta cerrada (privada)\n"
    "▫️ Error de recuperación de datos\n"
    "▫️ La cuenta tiene restricciones de edad\n"
    "▫️ Link inválido o no reconocido\n"
    "▫️ Stories de Facebook no están soportadas"
)


async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    text = limpiar_url(text)
    reply_id = update.message.message_id

    # ── SoundCloud ────────────────────────────────────────────────────────────
    if text.lower().startswith("find "):
        query = text[5:].strip()
        if not query:
            return
        msg = await update.message.reply_text("Procesando...", reply_to_message_id=reply_id)
        await handle_find(update, msg, query, reply_id)
        return

    platform, url = get_link(text)
    if not platform:
        return

    if platform == 'facebook':
        url = convertir_url_facebook(url)

    msg = await update.message.reply_text("Procesando...", reply_to_message_id=reply_id)
    folder = BASE_DIR / uuid.uuid4().hex
    folder.mkdir(parents=True, exist_ok=True)

    try:
        # ── TikTok ───────────────────────────────────────────────────────────
        if platform == 'tiktok':
            url = await resolve_short_url(url)
            if await handle_tiktok_slides(update, url, msg, reply_id):
                return

        # ── Instagram carrusel ───────────────────────────────────────────────
        if platform == 'instagram' and '/p/' in url:
            if await handle_instagram_carousel(update, url, msg, reply_id):
                return

        # ── Video general ────────────────────────────────────────────────────
        await handle_video(update, context, url, platform, folder, msg, reply_id)

    except Exception as e:
        logger.error(f"handle_media error: {e}")
        await safe_edit(msg, ERROR_RECUPERACION)
    finally:
        shutil.rmtree(folder, ignore_errors=True)