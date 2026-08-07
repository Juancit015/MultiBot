import asyncio
import logging

import yt_dlp
from telegram import InputMediaPhoto

from bot.config import COOKIES_TT
from bot.services.ffmpeg import video_has_audio
from bot.services.net import fetch_bytes
from bot.services.tikwm import tiktok_slides, tiktok_video_tikwm
from bot.utils.messaging import safe_delete
from bot.utils.text import build_title

logger = logging.getLogger(__name__)


async def handle_tiktok_slides(update, url: str, msg, reply_id: int) -> bool:
    """True si el slideshow fue enviado y el mensaje ya se eliminó."""
    if '/photo/' not in url:
        return False
    imgs, music_url, slide_title = await tiktok_slides(url)
    if not imgs:
        logger.warning("tikwm falló para slideshow, intentando yt-dlp")
        return False
    slide_meta = {}
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'skip_download': True,
                               'cookiefile': str(COOKIES_TT) if COOKIES_TT.exists() else None}) as ydl:
            slide_meta = await asyncio.to_thread(ydl.extract_info, url, download=False) or {}
    except Exception:
        pass
    caption_slide = build_title(
        views=slide_meta.get('view_count'),
        likes=slide_meta.get('like_count'),
        channel=slide_meta.get('channel'),
        uploader=slide_meta.get('uploader'),
        description=slide_meta.get('description') or slide_title,
    )
    contents = [c for c in await asyncio.gather(*[fetch_bytes(i) for i in imgs[:10]]) if c]
    if contents:
        await update.message.reply_media_group(
            [InputMediaPhoto(contents[0], caption=caption_slide)] +
            [InputMediaPhoto(c) for c in contents[1:]],
            reply_to_message_id=reply_id
        )
    if music_url and (music := await fetch_bytes(music_url)):
        await update.message.reply_audio(music, title=caption_slide, reply_to_message_id=reply_id)
    await safe_delete(msg)
    return True


async def ensure_tiktok_audio(folder, url: str) -> None:
    """Si el video TikTok no tiene audio, lo baja de tikwm y borra el sin audio."""
    mp4s_check = list(folder.glob("*.mp4"))
    if not mp4s_check or video_has_audio(mp4s_check[0]):
        return
    logger.warning("Video TikTok sin audio — usando tikwm como fallback")
    tikwm_data = await tiktok_video_tikwm(url)
    if tikwm_data and tikwm_data.get('video_url'):
        video_bytes = await fetch_bytes(tikwm_data['video_url'])
        if video_bytes:
            tikwm_path = folder / "tikwm_video.mp4"
            tikwm_path.write_bytes(video_bytes)
            for old_mp4 in mp4s_check:
                old_mp4.unlink(missing_ok=True)
            logger.info("Video tikwm descargado con audio")