import asyncio
import logging

import requests

from bot.config import TIKWM_API_URL
from bot.services.ffmpeg import video_has_audio
from bot.services.net import fetch_bytes

logger = logging.getLogger(__name__)


async def tiktok_slides(url: str):
    try:
        r = await asyncio.to_thread(
            lambda: requests.post(TIKWM_API_URL, data={'url': url, 'hd': 1}, timeout=20).json()
        )
        if r.get('code') == 0:
            d = r['data']
            images = d.get('images', [])
            if images:
                return images, d.get('music'), d.get('title', 'Slideshow')
    except Exception as e:
        logger.warning(f"TikWM error: {e}")
    return None, None, None


async def tiktok_video_tikwm(url: str) -> dict | None:
    """Descarga video de TikTok via tikwm como fallback cuando yt-dlp falla o no tiene audio."""
    try:
        r = await asyncio.to_thread(
            lambda: requests.post(TIKWM_API_URL, data={'url': url, 'hd': 1}, timeout=20).json()
        )
        if r.get('code') == 0:
            d = r['data']
            return {
                'video_url': d.get('play') or d.get('wmplay'),
                'music_url': d.get('music'),
                'title':     d.get('title', ''),
                'author':    d.get('author', {}).get('unique_id', ''),
                'views':     d.get('play_count'),
                'likes':     d.get('digg_count'),
            }
    except Exception as e:
        logger.warning(f"TikWM video error: {e}")
    return None


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
