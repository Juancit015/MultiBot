import asyncio
import logging

import requests

logger = logging.getLogger(__name__)


async def tiktok_slides(url: str):
    try:
        r = await asyncio.to_thread(
            lambda: requests.post("https://www.tikwm.com/api/", data={'url': url, 'hd': 1}, timeout=20).json()
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
            lambda: requests.post("https://www.tikwm.com/api/", data={'url': url, 'hd': 1}, timeout=20).json()
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