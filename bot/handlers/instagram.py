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
        import instaloader
        shortcode = re.search(r'/p/([^/?]+)', url)
        if shortcode:
            sc = shortcode.group(1)
            L = instaloader.Instaloader()
            try:
                L.load_session_from_file('ig_session')
            except Exception:
                pass
            post = await asyncio.to_thread(
                lambda: instaloader.Post.from_shortcode(L.context, sc)
            )
            if post.typename == 'GraphSidecar':
                urls = [node.display_url for node in post.get_sidecar_nodes()]
                if urls:
                    caption_ig = build_title(
                        likes=post.likes if hasattr(post, 'likes') else None,
                        channel=post.owner_username if hasattr(post, 'owner_username') else None,
                        description=post.caption if post.caption else None,
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