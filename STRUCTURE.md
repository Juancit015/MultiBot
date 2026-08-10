# STRUCTURE.md — Mapa del repositorio

Multibot es un bot de Telegram con arquitectura en capas: la entrada (`multibot.py`) valida config y registra handlers; `bot/handlers/` decide qué hacer con cada mensaje; `bot/services/` integra herramientas externas (yt-dlp, FFmpeg, TikWM, Groq, HTTP); `bot/utils/` agrupa ayudantes; `tests/` cubre la suite con mocks.

## Árbol

```
multibot.py                       # Entry point: validación fail-fast, Flask (7860), polling Telegram
Dockerfile                        # python:3.11-slim + ffmpeg, usuario app (uid 1001)
requirements.txt                  # Dependencias runtime (rangos >=, <)
requirements-dev.txt              # pytest >=8,<9 + pytest-asyncio
pytest.ini                        # testpaths=tests, asyncio_mode=auto, marker ffmpeg
.env.example                      # Plantilla de env vars (nunca versionar .env)
.gitignore                        # downloads/, .env, cookies*, sesiones, caches
bot/
├── config.py                     # Env vars, rutas de cookies, LIMITE_MB, regex por plataforma
├── handlers/                     # Capa de entrada: convierte mensajes en acciones
│   ├── media.py                  # Orquestador: enrutado de enlaces y mensaje de error genérico
│   ├── tiktok.py                 # Slides de TikTok (/photo/ → álbum + audio vía TikWM)
│   ├── instagram.py              # Carruseles de Instagram (/p/ → álbum vía instaloader)
│   ├── soundcloud.py             # find <cancion> (scsearch1 → MP3 + carátula)
│   ├── wiki.py                   # /wiki <consulta> (Groq, manejo de cuota/errores)
│   └── generic.py                # Pipeline de video: descarga, audio, límite 2000 MB, envío
├── services/                     # Capa de integración con servicios externos
│   ├── ytdlp.py                  # make_opts (formato/FFmpeg/cookies) + download_with_retry
│   ├── ffmpeg.py                 # merge_audio_into_video, extract_audio_from_video, video_has_audio
│   ├── tikwm.py                  # Cliente API TikWM (slides, fallback de video y de audio)
│   ├── groq.py                   # Cliente Groq + SYSTEM_PROMPT + GroqQuotaError/GroqAPIError
│   └── net.py                    # fetch_bytes y resolve_short_url (HTTP simple)
└── utils/                        # Ayudantes
    ├── text.py                   # get_link, limpiar_url, convertir_url_facebook, build_title, fmt_num
    └── messaging.py              # safe_edit / safe_delete (envíos que no rompen el flujo)

downloads/                        # Media temporal por petición (uuid) — gitignored, solo .gitkeep
cookies.txt                       # Cookies TikTok (yt-dlp) — gitignored
cookies_ig.txt                    # Cookies Instagram (yt-dlp) — gitignored
cookiesFB.txt                     # Cookies Facebook (yt-dlp) — gitignored
ig_session                        # Sesión de Instaloader (carruseles) — gitignored

tests/
├── conftest.py                   # Fixtures globales: aislamiento de downloads/, anti-red, medios ffmpeg
├── mocks/                        # Mocks de librerías externas
│   ├── telegram.py               #   Aplicación/objetos de Telegram simulados
│   ├── ytdlp.py                  #   YoutubeDL simulado (metadata + archivos fake)
│   ├── instaloader.py            #   Instaloader simulado (carruseles)
│   ├── tikwm.py                  #   Respuestas fake de la API TikWM
│   └── groq.py                   #   Cliente Groq simulado (por defecto no disponible)
└── test_commands.py              # Comandos /start, /wiki, find
    test_failfast.py              # Aborto si faltan BOT_TOKEN / GROQ_API_KEY
    test_ffmpeg.py                # video_has_audio con medios reales
    test_pipeline_mock.py         # Pipeline de video con descarga simulada
    test_pipeline_video.py        # Pipeline con videos ffmpeg reales (con/sin audio)
    test_slides_carousel.py       # Slides TikTok + carruseles Instagram
    test_soundcloud.py            # Búsqueda y descarga SoundCloud simulada
    test_utils_text.py            # get_link, limpiar_url, build_title
    test_wiki.py                  # Errores Groq (cuota, API, no disponible)
```

## Dónde se edita cada cosa

| Qué quieres cambiar | Archivo | Referencias clave |
| --- | --- | --- |
| Plataformas y enlaces reconocidos (regex) | `bot/config.py` | `RE_PATTERNS` |
| Límite de subida a Telegram (2000 MB) | `bot/config.py` | `LIMITE_MB` |
| Env vars, rutas de cookies/sesión, defaults de Groq/TikWM | `bot/config.py` | módulo completo |
| Mensaje de error al no recuperar una publicación | `bot/handlers/media.py` | `ERROR_RECUPERACION` |
| Enrutado de un mensaje (find, plataforma, dispatch) | `bot/handlers/media.py` | `handle_media` |
| Slides de TikTok (álbum + música) | `bot/handlers/tiktok.py` | `handle_tiktok_slides` |
| Carruseles de Instagram (álbum de fotos) | `bot/handlers/instagram.py` | `handle_instagram_carousel` |
| Título de los envíos (views, likes, canal, descripción) | `bot/utils/text.py` | `build_title`, `fmt_num` |
| Normalización de URLs pegadas (espacios, prefijos) | `bot/utils/text.py` | `limpiar_url`, `convertir_url_facebook` |
| Formato de descarga (720p MP4 H.264 + MP3 128k) y cookies | `bot/services/ytdlp.py` | `make_opts` |
| Reintentos de descarga y fallback de ffprobe | `bot/services/ytdlp.py` | `download_with_retry` |
| Fusión o extracción de audio con FFmpeg | `bot/services/ffmpeg.py` | `merge_audio_into_video`, `extract_audio_from_video` |
| Fallback de video/audio de TikTok vía TikWM | `bot/services/tikwm.py` | `ensure_tiktok_audio`, `tiktok_video_tikwm` |
| Personalidad y límites de `/wiki` | `bot/services/groq.py` | `SYSTEM_PROMPT`, `ask_groq` |
| Endpoint TikWM de slides | `bot/config.py` + `bot/services/tikwm.py` | `TIKWM_API_URL`, `tiktok_slides` |
| Mensajes de estado ("Procesando...") y su borrado | `bot/utils/messaging.py` | `safe_edit`, `safe_delete` |
| Comandos registrados en el bot | `multibot.py` | `add_handler(...)` |
| Validación fail-fast de env vars | `multibot.py` | `_validar_config()` |
| Fixtures de aislamiento y anti-red de la suite | `tests/conftest.py` | `isolated_base`, `no_live_requests`, `media_fx`, `install_pipeline` |
| Mocks de librerías externas | `tests/mocks/` | `telegram.py`, `ytdlp.py`, `instaloader.py`, `tikwm.py`, `groq.py` |
| Tests por área | `tests/test_*.py` | ver nombres en el árbol |

## Flujo de un mensaje

1. `multibot.py:main()` registra `MessageHandler(filters.TEXT & ~filters.COMMAND, handle_media)` más los command handlers.
2. `bot/handlers/media.py:handle_media` limpia el texto, responde `Procesando...` y decide: `find ` → SoundCloud; URL → busca plataforma en `get_link`; TikTok `/photo/` → slides; Instagram `/p/` → carrusel; resto → pipeline de video (`handle_video`).
3. `bot/handlers/generic.py:handle_video` descarga con `download_with_retry`, garantiza audio (`ensure_tiktok_audio` / `extract_audio_from_video`), fusiona (`merge_audio_into_video`), verifica `LIMITE_MB` y envía video + MP3 con `safe_delete` del mensaje de estado.

## Notas

- `downloads/` se limpia solo: cada petición crea una carpeta por `uuid` y la borra al terminar (`shutil.rmtree` en `media.py` y `soundcloud.py`).
- Los archivos `cookies*.txt` e `ig_session` están en `.gitignore`: si no existen, el bot funciona igual (yt-dlp sin cookies; instaloader sin sesión).
- Los directorios `__pycache__/`, `.pytest_cache/` y `.ruff_cache/` son basura generada, ignorados por git.