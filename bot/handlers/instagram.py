import asyncio
import logging
import re

from telegram import InputMediaPhoto

from bot.services.net import fetch_bytes
from bot.utils.messaging import safe_delete, safe_edit
from bot.utils.text import build_title

logger = logging.getLogger(__name__)


async def handle_instagram_carousel(update, url: str, msg, reply_id: int) -> bool:
    """True si el carrusel fue enviado (o el error informado), False si cae al pipeline de video."""
    try:
        from bot.services.instagram import carousel_sidecar
        shortcode = re.search(r'/p/([^/?]+)', url)
        if shortcode:
            data = await carousel_sidecar(shortcode.group(1))
            if data:
                urls = data["urls"]
                caption_ig = build_title(
                    likes=data["likes"],
                    channel=data["owner"],
                    description=data["caption"],
                )
                all_contents = [c for c in await asyncio.gather(
                        *[fetch_bytes(u) for u in urls]
                    ) if c]
                if all_contents:
                    chunks = [all_contents[i:i+10] for i in range(0, len(all_contents), 10)]
                    for idx_chunk, chunk in enumerate(chunks):
                        cap_chunk = caption_ig if idx_chunk == 0 else ""
                        await update.message.reply_media_group(
                            [InputMediaPhoto(chunk[0], caption=cap_chunk)] +
                            [InputMediaPhoto(c) for c in chunk[1:]],
                            reply_to_message_id=reply_id
                        )
                await safe_delete(msg)
                return True
        return False
    except Exception as e:
        logger.warning(f"Instaloader carrusel error: {e}")
        await safe_edit(msg, "No se pudo descargar el carrusel. Intenta en unos minutos.")
        return True