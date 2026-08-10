# STRUCTURE.md — Mapa del repositorio

Arquitectura en capas del bot MultiBot. Cada ruta mencionada existe en el working tree actual del repo.

```
MultiBot/
├── multibot.py                  # Entry point: load_dotenv, validación fail-fast, Flask 7860, handlers, polling
├── requirements.txt             # Dependencias de producción (rangos compatibles, no pins)
├── requirements-dev.txt         # Dependencias de desarrollo (pytest, pytest-asyncio)
├── Dockerfile                   # python:3.11-slim + ffmpeg, usuario no root, CMD multibot.py
├── pytest.ini                   # testpaths=tests, asyncio_mode=auto, marker ffmpeg
├── .env.example                 # Plantilla de variables de entorno (copiar a .env)
├── .gitignore / .dockerignore   # Exclusión de .env, cookies, sesiones, caches, downloads
├── bot/
│   ├── config.py                # Env vars, rutas de cookies/descargas, regex por plataforma
│   ├── handlers/                # Capa de presentación: traduce mensajes de Telegram en acciones
│   │   ├── media.py             # Router principal: qué hacer según plataforma/link
│   │   ├── generic.py           # Pipeline de video: descarga, audio, límite 2 GB
│   │   ├── tiktok.py            # Slideshows /photo/ (tikwm + yt-dlp metadata)
│   │   ├── instagram.py         # Carruseles /p/ con Instaloader (sesión IG_SESSION)
│   │   ├── soundcloud.py        # find <cancion>: scsearch1 + MP3 con thumbnail
│   │   └── wiki.py              # /wiki: consulta enciclopédica a Groq
│   ├── services/                # Capa de dominio: integraciones y procesamiento
│   │   ├── ytdlp.py             # make_opts por plataforma/modo, descarga con reintentos
│   │   ├── ffmpeg.py            # ffprobe/ffmpeg: detectar audio, incrustar, extraer MP3
│   │   ├── tikwm.py             # API TikWM: slides/TikTok y fallback de audio/video
│   │   ├── groq.py              # Cliente Groq, SYSTEM_PROMPT, reintentos, excepciones propias
│   │   └── net.py               # fetch_bytes y resolución de URLs cortas (requests)
│   └── utils/                   # Helpers sin dependencias del dominio
│       ├── text.py              # Regex de limpieza, títulos con views/likes, conversión FB
│       └── messaging.py         # safe_edit / safe_delete (no revientan si Telegram falla)
├── tests/
│   ├── conftest.py              # Fixtures globales: BASE_DIR aislado, anti-red, medios ffmpeg
│   ├── mocks/                   # Fake de telegram, ytdlp, instaloader, tikwm, groq
│   └── test_*.py                # 9 suites: failfast, ffmpeg, pipeline, slides, soundcloud, wiki…
├── downloads/                   # Carpeta temporal de medias (borrada tras cada envío, solo .gitkeep)
├── cookies.txt                  # Cookies TikTok (yt-dlp, config COOKIES_TT)
├── cookies_ig.txt               # Cookies Instagram (yt-dlp, config COOKIES_IG)
├── cookiesFB.txt                # Cookies Facebook (yt-dlp, config COOKIES_FB)
├── cookies_yt.txt               # Sin referencia en el código actual
├── ig_session                   # Sesión de Instaloader (config IG_SESSION)
└── README.md / CHANGELOG.md / STRUCTURE.md   # Documentación
```

## Dónde se edita cada cosa

| Que quieres cambiar | Archivo | Detalle |
| --- | --- | --- |
| Carga de `.env` | `multibot.py` | `load_dotenv()` al arrancar, antes de `from bot.config import ...` |
| Mensaje de bienvenida (`/start`) | `multibot.py` | `start()` |
| Credenciales y validación de arranque | `multibot.py` / `bot/config.py` | `main()` → `_validar_config()`; env vars en `config.py` |
| Puerto y healthcheck Flask | `multibot.py` | `Flask(__name__).run(host='0.0.0.0', port=7860)` |
| Tokens/tiempos de la API de Telegram | `multibot.py` | `HTTPXRequest(...)` y `app.run_polling(timeout=60)` |
| Regex para detectar plataformas | `bot/config.py` | `RE_PATTERNS` (`tiktok`, `instagram`, `facebook`) |
| Límite de tamaño de video | `bot/config.py` | `LIMITE_MB = 2000` |
| Rutas de cookies y sesión IG | `bot/config.py` | `COOKIES_TT`, `COOKIES_IG`, `COOKIES_FB`, `IG_SESSION` |
| Router de mensajes (qué plataforma atiende) | `bot/handlers/media.py` | `handle_media()`: `find ` → SoundCloud; TikTok → slides; IG `/p/` → carrusel; resto → video |
| Pipeline de video (títulos, audio, envío) | `bot/handlers/generic.py` | `handle_video()`, `send_video_fallback()`, `send_audio_fallback()` |
| Slideshows de TikTok | `bot/handlers/tiktok.py` | `handle_tiktok_slides()` (TikWM + metadata yt-dlp) |
| Carruseles de Instagram | `bot/handlers/instagram.py` | `handle_instagram_carousel()` (Instaloader, chunks de 10) |
| Descarga `find <cancion>` de SoundCloud | `bot/handlers/soundcloud.py` | `handle_find()` (`scsearch1:`) |
| Comando `/wiki` | `bot/handlers/wiki.py` | `cmd_wiki()` (Groq, edición del mensaje en vivo) |
| Formato de descarga (video/MP3, cookies) | `bot/services/ytdlp.py` | `make_opts()` y `download_with_retry()` |
| Incrustar/extraer audio con ffmpeg | `bot/services/ffmpeg.py` | `merge_audio_into_video()`, `extract_audio_from_video()`, `video_has_audio()` |
| Fallbacks de TikTok vía TikWM | `bot/services/tikwm.py` | `tiktok_slides()`, `tiktok_video_tikwm()`, `ensure_tiktok_audio()` |
| Personalidad y reglas de Groq | `bot/services/groq.py` | `SYSTEM_PROMPT`, `ask_groq()`, `GroqQuotaError`/`GroqAPIError` |
| Descargas HTTP auxiliares | `bot/services/net.py` | `fetch_bytes()`, `resolve_short_url()` |
| Títulos con views/likes, URLs de Facebook | `bot/utils/text.py` | `build_title()`, `convertir_url_facebook()`, `limpiar_url()` |
| Fixtures de la suite de tests | `tests/conftest.py` | Aislamiento de `BASE_DIR`, bloqueo de red real, medios ffmpeg |
| Mocks de dependencias externas | `tests/mocks/` | `telegram.py`, `ytdlp.py`, `instaloader.py`, `tikwm.py`, `groq.py` |