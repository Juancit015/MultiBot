import asyncio
import logging

from bot.config import LIMITE_MB
from bot.services.ffmpeg import extract_audio_from_video, merge_audio_into_video
from bot.services.tikwm import ensure_tiktok_audio
from bot.services.ytdlp import download_with_retry, make_opts
from bot.utils.messaging import safe_delete, safe_edit
from bot.utils.text import build_title

logger = logging.getLogger(__name__)


async def send_video_fallback(update, context, video_path, title, reply_id, timeout_s):
    try:
        with open(video_path, 'rb') as f:
            await update.message.reply_video(
                f, caption=title,
                reply_to_message_id=reply_id,
                read_timeout=timeout_s,
                write_timeout=timeout_s
            )
    except Exception:
        with open(video_path, 'rb') as f:
            await context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=f, caption=title,
                read_timeout=timeout_s,
                write_timeout=timeout_s
            )


async def send_audio_fallback(update, context, audio_path, title, reply_id):
    try:
        with open(audio_path, 'rb') as f:
            await update.message.reply_audio(
                f, title=f"{title} (Audio)",
                reply_to_message_id=reply_id,
                read_timeout=120, write_timeout=120
            )
    except Exception:
        with open(audio_path, 'rb') as f:
            await context.bot.send_audio(
                chat_id=update.effective_chat.id,
                audio=f, title=f"{title} (Audio)",
                read_timeout=120, write_timeout=120
            )


async def handle_video(update, context, url: str, platform: str, folder, msg, reply_id: int):
    logger.info(f"Descargando {platform}: {url}")
    meta = await download_with_retry(url, make_opts(folder, mode="video", platform=platform))

    if platform == 'tiktok':
        await ensure_tiktok_audio(folder, url)

    uploader    = meta.get('uploader') or meta.get('channel') or ''
    description = meta.get('description', '').strip()

    es_story_ig = (platform == 'instagram' and '/stories/' in url)
    es_story_tt = (platform == 'tiktok' and ('story_type=1' in url or 'story_uid' in url))

    if es_story_ig or es_story_tt:
        title = f"Story by @{uploader}" if uploader else "Story"
    elif platform in ('instagram', 'tiktok'):
        title = build_title(
            views=meta.get('view_count'),
            likes=meta.get('like_count'),
            channel=meta.get('channel'),
            uploader=uploader,
            description=description,
        )
    else:
        title = build_title(
            views=meta.get('view_count'),
            likes=meta.get('like_count'),
            channel=meta.get('channel'),
            uploader=uploader,
            description=description,
            title=meta.get('title'),
        )

    mp4s = list(folder.glob("*.mp4"))
    mp3s = list(folder.glob("*.mp3"))

    if not mp4s:
        await safe_edit(msg, "No se encontró el archivo de video.")
        return

    video_path = mp4s[0]

    # Si no hay MP3 (ffprobe falló), extraer audio con FFmpeg directamente
    if not mp3s:
        logger.info("Sin MP3 — extrayendo audio con FFmpeg...")
        extracted = await asyncio.to_thread(extract_audio_from_video, video_path)
        if extracted:
            mp3s = [extracted]

    # Incrustar audio en video si hay MP3
    if mp3s:
        merged = await asyncio.to_thread(merge_audio_into_video, video_path, mp3s[0])
        if merged:
            video_path = merged
            logger.info("Video con audio incrustado listo")

    size_mb = video_path.stat().st_size / (1024 * 1024)
    if size_mb > LIMITE_MB:
        duration_s = meta.get('duration')
        dur_str = f"{int(duration_s//60)}:{int(duration_s%60):02d}" if duration_s else "?"
        await safe_edit(msg,
            f"Video demasiado grande para Telegram.\n"
            f"Tamaño: {size_mb:.1f} MB | Duración: {dur_str}"
        )
        return

    timeout_s = max(120, int(size_mb * 10))

    await send_video_fallback(update, context, video_path, title, reply_id, timeout_s)

    # Enviar MP3 por separado
    if mp3s:
        await send_audio_fallback(update, context, mp3s[0], title, reply_id)

    await safe_delete(msg)