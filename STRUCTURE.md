# STRUCTURE.md — MultiBot

Mapa técnico del repositorio: dónde vive cada comportamiento y dónde se edita. Todo lo listado existe en el working tree actual.

## Árbol

```
MultiBot/
├── multibot.py                  # Entry point: fail-fast de entorno, polling y Flask :7860
├── bot/
│   ├── config.py                # Env vars + defaults, patrones URL, rutas de cookies, LIMITE_MB
│   ├── handlers/                # Lógica por tipo de contenido y comando
│   │   ├── media.py             # Orquestador de enlaces (TikTok/IG/FB): detecta plataforma, despacha, errores
│   │   ├── generic.py           # Pipeline de video: descarga, merge de audio, envío video + MP3
│   │   ├── tiktok.py            # Slideshows /photo/ (TikWM + metadatos yt-dlp)
│   │   ├── instagram.py         # Carruseles /p/ vía Instaloader (sesión IG_SESSION)
│   │   ├── soundcloud.py        # Comando find <cancion> → MP3 de scsearch1
│   │   └── wiki.py              # Comando /wiki <consulta> → Groq (con ayuda sin args)
│   ├── services/                # Integraciones externas
│   │   ├── ytdlp.py             # make_opts (formato ≤720p, cookies por plataforma) y descargas con retry
│   │   ├── ffmpeg.py            # merge_audio_into_video, extract_audio_from_video, video_has_audio
│   │   ├── tikwm.py             # API TikWM: slides, video fallback, ensure_tiktok_audio
│   │   ├── groq.py              # Cliente Groq, SYSTEM_PROMPT, GroqQuotaError/GroqAPIError
│   │   └── net.py               # fetch_bytes y resolve_short_url (vm./vt.) via requests
│   └── utils/
│       ├── text.py              # get_link, limpiar_url, convertir_url_facebook, build_title, fmt_num
│       └── messaging.py         # safe_edit / safe_delete (sin excepciones al caller)
├── tests/
│   ├── conftest.py              # Fixtures: BASE_DIR a tmp, bloqueo anti-red, medios reales con ffmpeg
│   ├── mocks/                   # Fakes sin red ni I/O
│   │   ├── telegram.py          # FakeMessage / FakeContext
│   │   ├── groq.py              # FakeClient de chat completions (errores y respuestas)
│   │   ├── ytdlp.py             # FakeYdlMeta / FakeYdlAudio
│   │   ├── instaloader.py       # Módulo instaloader simulado
│   │   └── tikwm.py             # Respuestas TikWM simuladas
│   └── test_*.py                # commands, failfast, ffmpeg, pipeline mock/video, slides, SC, wiki, utils
├── requirements.txt             # Dependencias de runtime (rangos)
├── requirements-dev.txt         # pytest + pytest-asyncio
├── Dockerfile                   # python:3.11-slim + ffmpeg, usuario no-root, CMD multibot.py
├── .env.example                 # Plantilla de variables (obligatorias y opcionales)
├── cookies.txt / cookies_ig.txt / cookiesFB.txt  # Opcionales: cookies por plataforma (gitignored)
├── ig_session                   # Sesión Instaloader (opcional, gitignored)
└── downloads/                   # Salida de descargas por uuid (gitignored, solo .gitkeep)
```

## Dónde se edita cada cosa

| Qué quieres cambiar | Dónde |
| --- | --- |
| Registrar un nuevo comando o handler | Crear `bot/handlers/<algo>.py`, importarlo y añadir `add_handler` en `multibot.py` |
| Patrones de detección de plataformas | `bot/config.py` → `RE_PATTERNS` (regex de TikTok/IG/Facebook) |
| Limpieza/normalización de enlaces pegados | `bot/utils/text.py` → `limpiar_url`, `convertir_url_facebook` |
| Formato de descarga (resolución, codecs, retries) | `bot/services/ytdlp.py` → `make_opts` y `download_with_retry` |
| Cookies por plataforma (rutas) | `bot/config.py` → `COOKIES_TT`, `COOKIES_IG`, `COOKIES_FB` |
| Límite de tamaño de video | `bot/config.py` → `LIMITE_MB` (2000) y el aviso en `bot/handlers/generic.py` |
| Título/caption de envíos | `bot/utils/text.py` → `build_title` / `fmt_num` |
| Flujo slides de TikTok | `bot/handlers/tiktok.py` + `bot/services/tikwm.py` |
| Flujo carruseles de Instagram | `bot/handlers/instagram.py` (sesión: `IG_SESSION` en config) |
| Búsqueda de SoundCloud (`find`) | `bot/handlers/soundcloud.py` |
| Prompt y errores de Groq | `bot/services/groq.py` → `SYSTEM_PROMPT`, `GroqQuotaError`, `GroqAPIError` |
| Mensajes de error al usuario | `bot/handlers/media.py` → `ERROR_RECUPERACION`; demás mensajes inline en cada handler |
| Defaults/env vars | `bot/config.py` (reflejar también en `.env.example`) |
| Envíos seguros al chat | `bot/utils/messaging.py` → `safe_edit`, `safe_delete` |
| Aislamiento de tests (fixtures, anti-red) | `tests/conftest.py` |
| Fakes de una dependencia | `tests/mocks/<dependencia>.py` |
| Tests de un módulo | `tests/test_*.py` (uno por área: wiki, soundcloud, ffmpeg, pipeline, utils…) |
| Imagen Docker / runtime | `Dockerfile` (base `python:3.11-slim`, ffmpeg, usuario `app`) |