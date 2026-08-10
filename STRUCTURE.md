# STRUCTURE.md

Mapa técnico del repositorio: dónde vive cada pieza del bot y dónde se edita. Para mantener o depurar el proyecto.

## Árbol

```
.
├── multibot.py              # Entry point: validación de config, polling, Flask 7860
├── bot/
│   ├── config.py            # Env vars, rutas (downloads/, cookies), patrones URL
│   ├── handlers/
│   │   ├── media.py         # Dispatch principal: detecta link, elige plataforma
│   │   ├── generic.py       # Límites de tamaño y envío genérico de video
│   │   ├── tiktok.py        # Slides de TikTok (TikWM + yt-dlp)
│   │   ├── instagram.py     # Carruseles de Instagram (instaloader)
│   │   ├── soundcloud.py    # Comando find <cancion>
│   │   └── wiki.py          # Comando /wiki (Groq)
│   ├── services/
│   │   ├── ytdlp.py         # Descargas y metadata por yt-dlp (cookiefile por plataforma)
│   │   ├── ffmpeg.py        # ffprobe/ffmpeg por PATH: detecta audio y compone media
│   │   ├── tikwm.py         # Slides de TikTok y fallbacks vía API TikWM
│   │   ├── groq.py          # Cliente Groq para /wiki
│   │   └── net.py           # Helpers HTTP (fetch_bytes, resolve_short_url)
│   └── utils/
│       ├── messaging.py     # Envío/edición segura de mensajes a Telegram
│       └── text.py          # Detección de URLs y utilidades de texto
├── tests/                   # Suite pytest (27 tests)
│   ├── mocks/               # Fakes de telegram, ytdlp, tikwm, groq, instaloader
│   ├── test_commands.py ..  # Tests por área (ver más abajo)
│   └── conftest.py          # Fixtures y entorno de tests
├── downloads/               # Salida de descargas (gitignored)
├── cookies*.txt             # Sesiones de cookies (gitignored)
├── ig_session               # Sesión de Instagram (gitignored)
├── requirements.txt         # Deps runtime
├── requirements-dev.txt     # Deps de desarrollo (pytest)
├── Dockerfile               # python:3.11-slim + ffmpeg, usuario no-root (uid 1001)
├── .env.example             # Plantilla de variables de entorno
└── pytest.ini               # Config de pytest (testpaths, marcador ffmpeg)
```

## Dónde se edita cada parte

| Qué quieres cambiar | Dónde |
| --- | --- |
| Nuevo comando (p. ej. `/help`) | `bot/handlers/` + registro en `multibot.py` (`add_handler`) |
| Soporte de una nueva plataforma | Nuevo handler en `bot/handlers/` + detección en `handlers/media.py` |
| Reglas de detección de URLs | `RE_PATTERNS` en `bot/config.py` |
| Procesado de audio/video (detectar, extraer, componer) | `bot/services/ffmpeg.py` |
| Fallbacks de TikTok / slides | `bot/services/tikwm.py` |
| Modelo o parámetros de `/wiki` | `GROQ_MODEL`, `GROQ_TEMPERATURE`, `GROQ_MAX_TOKENS` en `.env`/`bot/config.py` |
| Límite de tamaño de envío | `LIMITE_MB` en `bot/config.py` |
| Formatos/autenticación de descarga | `bot/services/ytdlp.py` (`make_opts`); los cookies se leen de la raíz del repo según `bot/config.py` |
| Mensajes de arranque y ayuda | `start` en `multibot.py` |
| Suites de tests | `tests/` (mocks en `tests/mocks/`, marcador `ffmpeg` en `pytest.ini`) |

## Recursos y sesiones

- Cookies por plataforma en la raíz, leídos por `bot/config.py`: `cookies.txt` (TikTok), `cookies_ig.txt` (Instagram), `cookiesFB.txt` (Facebook). No versionados.
- `cookies_yt.txt` existe en el repo pero **no es referenciado por el código**; no tiene efecto.
- Sesión de Instagram: `ig_session` (env `IG_SESSION`), usada por `bot/handlers/instagram.py` vía Instaloader.
- `downloads/` es la carpeta de salida (`BASE_DIR` en `bot/config.py`); el bot la crea al arrancar.