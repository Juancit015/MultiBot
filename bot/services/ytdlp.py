import asyncio
import logging
from pathlib import Path

import yt_dlp

from bot.config import COOKIES_FB, COOKIES_IG, COOKIES_TT

logger = logging.getLogger(__name__)


def make_opts(folder: Path, mode: str = "video", platform: str = "") -> dict:
    folder.mkdir(parents=True, exist_ok=True)
    opts = {
        'quiet': True, 'no_warnings': True, 'nocheckcertificate': True,
        'retries': 5, 'fragment_retries': 5,
        'socket_timeout': 120 if mode == "audio" else 60,
        'outtmpl': str(folder / '%(id)s.%(ext)s'), 'updatetime': False,
        'restrictfilenames': True,
        'trim_file_name': 50,
    }
    if platform == 'instagram' and COOKIES_IG.exists():
        opts['cookiefile'] = str(COOKIES_IG)
    elif platform == 'tiktok' and COOKIES_TT.exists():
        opts['cookiefile'] = str(COOKIES_TT)
    elif platform == 'facebook' and COOKIES_FB.exists():
        opts['cookiefile'] = str(COOKIES_FB)

    if mode == "video":
        opts.update({
            'format': 'bestvideo[height<=720][ext=mp4][vcodec^=avc]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best',
            'merge_output_format': 'mp4',
            'postprocessors': [
                {'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'},
                {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3',
                 'preferredquality': '128', 'nopostoverwrites': True},
            ],
            'postprocessor_args': {
                'FFmpegVideoConvertor': ['-vcodec', 'libx264', '-acodec', 'aac', '-strict', 'experimental'],
            },
            'keepvideo': True,
        })
    else:
        opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '128'}],
        })
    return opts


async def download_with_retry(url: str, opts: dict, max_retries: int = 3) -> dict:
    last_error = None
    is_soundcloud = 'soundcloud.com' in url
    actual_retries = 5 if is_soundcloud else max_retries

    # Cachear metadata antes de descargar
    meta_cache = {}
    try:
        info_opts = {**opts, 'skip_download': True}
        with yt_dlp.YoutubeDL(info_opts) as ydl:
            meta_cache = await asyncio.to_thread(ydl.extract_info, url, download=False) or {}
    except Exception:
        pass

    for attempt in range(1, actual_retries + 1):
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                return await asyncio.to_thread(ydl.extract_info, url, download=True)
        except Exception as e:
            last_error = e
            err = str(e)
            logger.warning(f"Intento {attempt}/{actual_retries} fallido: {err[:120]}")
            # ffprobe falla pero el video YA se descargó — usar metadata cacheada
            if 'unable to obtain file audio codec' in err or 'Postprocessing' in err:
                logger.warning("Error ffprobe — video descargado, usando metadata cacheada")
                return meta_cache
            if ('does not look like a Netscape' in err or 'cookies' in err.lower()) and 'cookiefile' in opts:
                opts = {k: v for k, v in opts.items() if k != 'cookiefile'}
                continue
            if attempt < actual_retries:
                wait_time = 3 * attempt if is_soundcloud else 2 * attempt
                await asyncio.sleep(wait_time)
    raise last_error