#!/usr/bin/env python3
import asyncio
import logging
import os
import re
import shutil
import uuid
from threading import Thread

import requests
import yt_dlp
from flask import Flask
from groq import Groq
from telegram import InputMediaPhoto, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.request import HTTPXRequest

from bot.config import (
    BASE_DIR,
    COOKIES_TT,
    GROQ_API_KEY,
    LIMITE_MB,
    TOKEN,
)
from bot.services.ffmpeg import (
    extract_audio_from_video,
    merge_audio_into_video,
    video_has_audio,
)
from bot.services.tikwm import tiktok_slides, tiktok_video_tikwm
from bot.services.ytdlp import download_with_retry, make_opts
from bot.utils.messaging import safe_delete, safe_edit
from bot.utils.text import build_title, convertir_url_facebook, get_link, limpiar_url

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

SYSTEM_PROMPT = """Eres un asistente de consultas informativas y enciclopédicas. Sigues estas normas AL PIE DE LA LETRA:

1. SOLO respondes preguntas sobre: personas, lugares, eventos históricos, tecnología, ciencia, conceptos, organizaciones, productos, fenómenos naturales y temas enciclopédicos.

2. RESPUESTAS CORTAS: máximo 4 líneas. Sin introducciones como "claro", "por supuesto", "con gusto". Ve directo al punto.

3. FORMATO FIJO — siempre responde exactamente así:
📌 [Tema]
[Respuesta en 2-3 líneas con los datos más importantes]

4. SI piden: código, bots, poemas, canciones, traducciones, recetas, consejos personales, tareas, redacciones o cualquier cosa que NO sea información enciclopédica — responde EXACTAMENTE esto:
⚠️ Este comando es solo para consultas informativas. Usa el chat normal para otras cosas.

5. SIN opiniones sobre política, religión, personas vivas controversiales. Solo hechos verificables.

6. IDIOMA: responde SIEMPRE en español sin importar el idioma de la pregunta.

7. SIN inventar: si no tienes información precisa responde: ❌ No tengo información precisa sobre ese tema.

8. SIN saludos, despedidas ni preguntas de seguimiento. Solo la respuesta y ya.

9. SIN formato markdown como **negrita** o _cursiva_. Solo texto plano con emojis.

10. NO respondas preguntas sobre ti mismo como qué IA eres, en qué te basas, quién te creó o cómo funcionas. Responde EXACTAMENTE: ⚠️ Este comando es solo para consultas informativas.

11. NO respondas sobre comandos de terminal, IPs, pings, código, configuraciones de red ni técnicas informáticas prácticas. Solo información enciclopédica sobre conceptos, no instrucciones de uso."""

async def fetch_bytes(url: str) -> bytes | None:
    try:
        return await asyncio.to_thread(lambda: requests.get(url, timeout=15).content)
    except Exception as e:
        logger.warning(f"fetch_bytes error: {e}")


async def resolve_short_url(url: str) -> str:
    try:
        return await asyncio.to_thread(lambda: requests.head(url, timeout=10, allow_redirects=True).url)
    except Exception as e:
        logger.warning(f"resolve_short_url error: {e}")
        return url


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hola! Envíame un enlace de TikTok, Instagram o Facebook.\n"
        "Escribe find <cancion> para buscar en SoundCloud.\n"
        "Usa /wiki <consulta> para buscar información."
    )


async def cmd_wiki(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not groq_client:
        await update.message.reply_text("❌ Servicio de consultas no disponible.")
        return

    consulta = " ".join(context.args).strip() if context.args else ""
    if not consulta:
        await update.message.reply_text(
            "📖 Uso: /wiki <consulta>\n"
            "Ejemplo: /wiki que es Linux\n"
            "Ejemplo: /wiki quien creo YouTube"
        )
        return

    msg = await update.message.reply_text("🔍 Consultando...")

    try:
        def llamar_groq():
            completion = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": consulta}
                ],
                temperature=0.3,
                max_completion_tokens=500,
                stream=False,
            )
            return completion.choices[0].message.content

        respuesta = await asyncio.to_thread(llamar_groq)
        await safe_edit(msg, respuesta[:4000])
        logger.info(f"Wiki consultado: {consulta[:50]}")

    except Exception as e:
        err = str(e)
        logger.error(f"Groq error: {e}")
        if "429" in err or "quota" in err.lower() or "rate" in err.lower():
            await safe_edit(msg, "⏳ Demasiadas consultas. Intenta en 30 segundos.")
        else:
            await safe_edit(msg, "❌ No se pudo procesar la consulta. Intenta de nuevo.")


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
        folder = BASE_DIR / uuid.uuid4().hex
        folder.mkdir(parents=True, exist_ok=True)
        try:
            with yt_dlp.YoutubeDL(make_opts(folder, mode="audio")) as ydl:
                info = await asyncio.to_thread(ydl.extract_info, f"scsearch1:{query}", download=True)
                if 'entries' in info:
                    info = info['entries'][0]
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
            if '/photo/' in url:
                imgs, music_url, slide_title = await tiktok_slides(url)
                if imgs:
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
                    return
                else:
                    logger.warning("tikwm falló para slideshow, intentando yt-dlp")

        # ── Instagram carrusel ───────────────────────────────────────────────
        if platform == 'instagram' and '/p/' in url:
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
                            return
            except Exception as e:
                logger.warning(f"Instaloader carrusel error: {e}")
                await safe_edit(msg, "No se pudo descargar el carrusel. Intenta en unos minutos.")
                return

        # ── Video general ────────────────────────────────────────────────────
        logger.info(f"Descargando {platform}: {url}")
        meta = await download_with_retry(url, make_opts(folder, mode="video", platform=platform))

        # Si es TikTok y el video no tiene audio, usar tikwm como fallback
        if platform == 'tiktok':
            mp4s_check = list(folder.glob("*.mp4"))
            if mp4s_check:
                # Verificar si el video tiene audio
                if not video_has_audio(mp4s_check[0]):
                    logger.warning("Video TikTok sin audio — usando tikwm como fallback")
                    tikwm_data = await tiktok_video_tikwm(url)
                    if tikwm_data and tikwm_data.get('video_url'):
                        video_bytes = await fetch_bytes(tikwm_data['video_url'])
                        if video_bytes:
                            # Guardar video de tikwm
                            tikwm_path = folder / "tikwm_video.mp4"
                            tikwm_path.write_bytes(video_bytes)
                            # Limpiar videos anteriores sin audio
                            for old_mp4 in mp4s_check:
                                old_mp4.unlink(missing_ok=True)
                            logger.info("Video tikwm descargado con audio")
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

        # Enviar MP3 por separado
        if mp3s:
            try:
                with open(mp3s[0], 'rb') as f:
                    await update.message.reply_audio(
                        f, title=f"{title} (Audio)",
                        reply_to_message_id=reply_id,
                        read_timeout=120, write_timeout=120
                    )
            except Exception:
                with open(mp3s[0], 'rb') as f:
                    await context.bot.send_audio(
                        chat_id=update.effective_chat.id,
                        audio=f, title=f"{title} (Audio)",
                        read_timeout=120, write_timeout=120
                    )

        await safe_delete(msg)

    except Exception as e:
        logger.error(f"handle_media error: {e}")
        await safe_edit(msg,
            "⛔️ No se ha podido recuperar la información de la publicación\n\n"
            "Posibles causas:\n"
            "▫️ Cuenta cerrada (privada)\n"
            "▫️ Error de recuperación de datos\n"
            "▫️ La cuenta tiene restricciones de edad\n"
            "▫️ Link inválido o no reconocido\n"
            "▫️ Stories de Facebook no están soportadas"
        )
    finally:
        shutil.rmtree(folder, ignore_errors=True)


def main():
    logger.info("Actualizando yt-dlp...")
    os.system("pip install -U yt-dlp --quiet")
    logger.info("yt-dlp actualizado.")

    Thread(target=lambda: Flask(__name__).run(host='0.0.0.0', port=7860), daemon=True).start()
    req = HTTPXRequest(connection_pool_size=8, read_timeout=300, write_timeout=300, connect_timeout=30, pool_timeout=30)
    app = Application.builder().token(TOKEN).base_url("https://multi-api-production.up.railway.app/bot").request(req).concurrent_updates(True).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("wiki",  cmd_wiki))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_media))
    print("Bot corriendo...")
    app.run_polling(timeout=60)


if __name__ == '__main__':
    main()
