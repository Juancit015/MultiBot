import asyncio
import logging
import shutil
import uuid

from bot.config import BASE_DIR
from bot.services.ytdlp import sc_search
from bot.utils.messaging import safe_delete, safe_edit

logger = logging.getLogger(__name__)


async def handle_find(update, msg, query: str, reply_id: int):
    folder = BASE_DIR / uuid.uuid4().hex
    folder.mkdir(parents=True, exist_ok=True)
    try:
        info = await sc_search(query, folder)
        mp3s = list(folder.glob("*.mp3"))
        if not mp3s:
            await safe_edit(msg, "No se pudo descargar el audio.")
            return
        if thumb := info.get('thumbnail'):
            await update.message.reply_photo(
                thumb,
                caption=f"🎵 {info.get('title','Audio')}\n👤 {info.get('uploader','?')}",
                reply_to_message_id=reply_id
            )
        with open(mp3s[0], 'rb') as f:
            await update.message.reply_audio(
                f,
                title=info.get('title', 'Audio'),
                performer=info.get('uploader', '?'),
                reply_to_message_id=reply_id
            )
        await safe_delete(msg)
    except Exception as e:
        logger.error(f"SoundCloud error: {e}")
        await safe_edit(msg, "❌ Sin resultados.")
    finally:
        shutil.rmtree(folder, ignore_errors=True)