#!/usr/bin/env python3
import os, re, uuid, shutil, logging, asyncio
from pathlib import Path
from threading import Thread

import requests
from groq import Groq
from flask import Flask
from telegram import Update, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.request import HTTPXRequest
import yt_dlp

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN        = os.environ.get("BOT_TOKEN", "***CLEARED***")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "***CLEARED***")
BASE_DIR     = Path("downloads")
BASE_DIR.mkdir(exist_ok=True)
COOKIES_TT = Path(__file__).parent / "cookies.txt"
COOKIES_IG = Path(__file__).parent / "cookies_ig.txt"
COOKIES_FB = Path(__file__).parent / "cookiesFB.txt"
LIMITE_MB  = 50 #Soportado por la api oficial de Telegram

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

8. SIN saludos, despedidas ni preguntas de seguimiento. Solo la respuesta.

9. SIN formato markdown como **negrita** o _cursiva_. Solo texto plano con emojis.

10. NO respondas preguntas sobre ti mismo como qué IA eres, en qué te basas, quién te creó o cómo funcionas. Responde EXACTAMENTE: ⚠️ Este comando es solo para consultas informativas.

11. NO respondas sobre comandos de terminal, IPs, pings, código, configuraciones de red ni técnicas informáticas prácticas. Solo información enciclopédica sobre conceptos, no instrucciones de uso."""

RE_PATTERNS = {
    'tiktok':    r'https?://(?:www\.|vm\.|vt\.)?tiktok\.com/[^\s]+',
    'instagram': r'https?://(?:www\.)?instagram\.com/(?:p|reel|tv|stories)/[^\s]+',
    'facebook':  r'https?://(?:www\.|m\.|web\.|fb\.)(?:facebook\.com|watch)/[^\s]+|https?://www\.facebook\.com/share/[^\s]+',
    'soundcloud': r'https?://(?:www\.)?soundcloud\.com/[^\s]+',
    'youtube':   r'https?://(?:www\.|m\.)?(?:youtube\.com|youtu\.be)/[^\s]+',
}


def get_link(text: str):
    for platform, pattern in RE_PATTERNS.items():
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return platform, m.group(0)
    return None, None


def convertir_url_facebook(url: str) -> str:
    if '/reel/' in url:
        video_id = re.search(r'/reel/(\d+)', url)
        if video_id:
            nueva_url = f"https://www.facebook.com/watch/?v={video_id.group(1)}"
            logger.info(f"URL Facebook convertida: {url} -> {nueva_url}")
            return nueva_url
    return url


def limpiar_url(text: str) -> str:
    text = re.sub(r'(https?://\S+)', lambda m: m.group(1).replace(' ', ''), text)
    text = re.sub(r'(instagram\.com)[A-Za-z]+(reel|stories|p|tv)', r'\1/\2', text, flags=re.IGNORECASE)
    text = re.sub(r'(tiktok\.com)[A-Za-z]+(@|video|photo)', r'\1/\2', text, flags=re.IGNORECASE)
    text = re.sub(r'(facebook\.com)[A-Za-z]+(share|watch|video)', r'\1/\2', text, flags=re.IGNORECASE)
    text = re.sub(r'(\.com)/+', r'\1/', text)
    return text


def make_opts(folder: Path, mode: str = "video", platform: str = "") -> dict:
    folder.mkdir(parents=True, exist_ok=True)
    # SoundCloud y audio necesitan más tiempo
    socket_timeout = 120 if platform in ('soundcloud',) or mode == "audio" else 60
    opts = {
        'quiet': True, 'no_warnings': True, 'nocheckcertificate': True,
        'retries': 5, 'fragment_retries': 5, 'socket_timeout': socket_timeout,
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
            'format': 'bestvideo[height<=720][ext=mp4][vcodec^=avc]+bestaudio[ext=m4a]/bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best',
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


def fmt_num(n):
    if not n: return None
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 1_000: return f"{n/1_000:.0f}K"
    return str(n)


def build_title(views=None, likes=None, channel=None, uploader=None, description=None, title=None):
    parts = []
    if fmt_num(views):  parts.append(f"{fmt_num(views)} views")
    if fmt_num(likes):  parts.append(f"{fmt_num(likes)} likes")
    canal = channel or uploader or ""
    if canal:           parts.append(canal)
    desc = (description or title or "")[:150]
    if desc:            parts.append(desc)
    return " | ".join(parts) if parts else "Video"


async def fetch_bytes(url: str) -> bytes | None:
    try:
        return await asyncio.to_thread(lambda: requests.get(url, timeout=30).content)
    except Exception as e:
        logger.warning(f"fetch_bytes error: {e}")


async def tiktok_slides(url: str):
    try:
        r = await asyncio.to_thread(
            lambda: requests.post("https://www.tikwm.com/api/", data={'url': url, 'hd': 1}, timeout=20).json()
        )
        if r.get('code') == 0:
            d = r['data']
            return d.get('images', []), d.get('music'), d.get('title', 'Slideshow')
    except Exception as e:
        logger.warning(f"TikWM error: {e}")
    return None, None, None


async def resolve_short_url(url: str) -> str:
    try:
        return await asyncio.to_thread(lambda: requests.head(url, timeout=10, allow_redirects=True).url)
    except Exception as e:
        logger.warning(f"resolve_short_url error: {e}")
        return url


async def download_with_retry(url: str, opts: dict, max_retries: int = 3) -> dict:
    last_error = None
    # SoundCloud necesita más reintentos por los timeouts
    is_soundcloud = 'soundcloud.com' in url
    actual_retries = 5 if is_soundcloud else max_retries
    for attempt in range(1, actual_retries + 1):
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                return await asyncio.to_thread(ydl.extract_info, url, download=True)
        except Exception as e:
            last_error = e
            err = str(e)
            logger.warning(f"Intento {attempt}/{actual_retries} fallido: {err[:120]}")
            if ('does not look like a Netscape' in err or 'cookies' in err.lower()) and 'cookiefile' in opts:
                opts = {k: v for k, v in opts.items() if k != 'cookiefile'}
                continue
            if attempt < actual_retries:
                wait_time = 3 * attempt if is_soundcloud else 2 * attempt
                await asyncio.sleep(wait_time)
    raise last_error


async def safe_delete(msg):
    try:
        await msg.delete()
    except Exception:
        pass


async def safe_edit(msg, text):
    try:
        await msg.edit_text(text)
    except Exception:
        pass


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hola! Envíame un enlace de TikTok, Instagram, Facebook, YouTube o SoundCloud.\n"
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
            await safe_edit(msg,
                "⏳ Demasiadas consultas en este momento.\n"
                "Intenta de nuevo en 30 segundos."
            )
        else:
            await safe_edit(msg, "❌ No se pudo procesar la consulta. Intenta de nuevo.")


async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    text = limpiar_url(text)
    reply_id = update.message.message_id

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
    elif platform == 'soundcloud':
        # Resolver URL corta si es necesario
        url = await resolve_short_url(url)

    msg = await update.message.reply_text("Procesando...", reply_to_message_id=reply_id)
    folder = BASE_DIR / uuid.uuid4().hex
    folder.mkdir(parents=True, exist_ok=True)

    try:
        if platform == 'tiktok':
            if '/photo/' not in url:
                url = await resolve_short_url(url)
            if '/photo/' in url:
                imgs, music_url, slide_title = await tiktok_slides(url)
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
                if imgs:
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

        if platform == 'soundcloud':
            logger.info(f"Descargando SoundCloud: {url}")
            try:
                # Descargar el audio con metadata
                opts = make_opts(folder, mode="audio", platform=platform)
                meta = await download_with_retry(url, opts)
                
                mp3s = list(folder.glob("*.mp3"))
                if not mp3s:
                    await safe_edit(msg, "❌ No se pudo descargar el audio de SoundCloud.")
                    return
                
                title = meta.get('title', 'Track')
                artist = meta.get('uploader', 'Unknown Artist')
                thumbnail_url = meta.get('thumbnail')
                
                # Enviar portada si existe
                if thumbnail_url:
                    thumb_bytes = await fetch_bytes(thumbnail_url)
                    if thumb_bytes:
                        caption = f"🎵 {title}\n👤 {artist}"
                        await update.message.reply_photo(
                            thumb_bytes,
                            caption=caption,
                            reply_to_message_id=reply_id
                        )
                
                # Enviar audio
                with open(mp3s[0], 'rb') as f:
                    await update.message.reply_audio(
                        f,
                        title=title,
                        performer=artist,
                        reply_to_message_id=reply_id,
                        read_timeout=120,
                        write_timeout=120
                    )
                
                await safe_delete(msg)
                return
                
            except Exception as e:
                logger.error(f"SoundCloud download error: {e}")
                await safe_edit(msg, "❌ Error al descargar de SoundCloud. Intenta de nuevo.")
                return
        
        logger.info(f"Descargando {platform}: {url}")
        meta = await download_with_retry(url, make_opts(folder, mode="video", platform=platform))
        uploader    = meta.get('uploader') or meta.get('channel') or ''
        description = meta.get('description', '').strip()
        video_title = meta.get('title', 'Video')

        es_story_ig = (platform == 'instagram' and '/stories/' in url)
        es_story_tt = (platform == 'tiktok' and ('story_type=1' in url or 'story_uid' in url))

        if es_story_ig or es_story_tt:
            title = f"Story by @{uploader}" if uploader else "Story"
        elif platform == 'youtube':
            title = f"✅ {video_title}"
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
                title=video_title,
            )

        mp4s = list(folder.glob("*.mp4"))
        mp3s = list(folder.glob("*.mp3"))

        if not mp4s:
            await safe_edit(msg, "No se encontró el archivo de video.")
            return

        size_mb = mp4s[0].stat().st_size / (1024 * 1024)
        if size_mb > LIMITE_MB:
            duration_s = meta.get('duration')
            dur_str = f"{int(duration_s//60)}:{int(duration_s%60):02d}" if duration_s else "?"
            await safe_edit(msg,
                f"Video demasiado grande para Telegram.\n"
                f"Tamaño: {size_mb:.1f} MB | Duración: {dur_str}"
            )
            return

        timeout_s = max(60, int(size_mb * 3))

        try:
            with open(mp4s[0], 'rb') as f:
                await update.message.reply_video(
                    f, caption=title,
                    reply_to_message_id=reply_id,
                    read_timeout=timeout_s,
                    write_timeout=timeout_s
                )
        except Exception:
            with open(mp4s[0], 'rb') as f:
                await context.bot.send_video(
                    chat_id=update.effective_chat.id,
                    video=f, caption=title,
                    read_timeout=timeout_s,
                    write_timeout=timeout_s
                )

        if mp3s and platform != 'youtube':
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
    req = HTTPXRequest(connection_pool_size=8, read_timeout=60, write_timeout=60, connect_timeout=30, pool_timeout=30)
    app = Application.builder().token(TOKEN).request(req).concurrent_updates(True).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("wiki",  cmd_wiki))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_media))
    print("Bot corriendo...")
    app.run_polling(timeout=60)


if __name__ == '__main__':
    main()
