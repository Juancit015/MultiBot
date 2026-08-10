# Estructura del repositorio

Mapa técnico de MultiBot para quien va a mantener o extender el bot. Todo archivo mencionado existe en el working tree actual (SSOT: `ls`/`find`, no historial).

```
MultiBot/
├── multibot.py                 # Entry point: carga .env, fail-fast de credenciales,
│                               # registra handlers, arranca Flask (0.0.0.0:7860) y el polling de Telegram
├── bot/                        # Paquete de lógica del bot
│   ├── config.py               # Configuración: variables de entorno, defaults, cookies, límites y RE_PATTERNS
│   ├── handlers/               # Handlers de Telegram
│   │   ├── generic.py          # Pipeline de video genérico (descarga → audio → merge → envío)
│   │   ├── instagram.py        # Carrusel de Instagram (/p/...)
│   │   ├── media.py            # Enrutador principal de mensajes (plataforma → handler)
│   │   ├── soundcloud.py       # Buscador "find <cancion>" en SoundCloud
│   │   ├── tiktok.py           # Slides de TikTok (/photo/...)
│   │   └── wiki.py             # Comando /wiki (Groq)
│   ├── services/               # Integraciones externas y herramientas de sistema
│   │   ├── ffmpeg.py           # ffprobe (detección de audio) + extract/merge con FFmpeg
│   │   ├── groq.py             # Cliente Groq (prompt del sistema, reintentos, errores de cuota)
│   │   ├── net.py              # fetch_bytes y resolución de short URLs
│   │   ├── tikwm.py            # API TikWM (slides y fallback de audio de TikTok)
│   │   └── ytdlp.py            # Opciones de yt-dlp, cookies por plataforma, descarga con reintentos
│   └── utils/                  # Utilidades
│       ├── messaging.py        # safe_edit / safe_delete (nunca rompen el flujo)
│       └── text.py             # Detección de URLs, limpieza, títulos formateados
├── tests/                      # Suite pytest (27 tests)
│   ├── conftest.py             # Fixtures: BASE_DIR aislado, anti-red, medios generados con FFmpeg
│   ├── mocks/                  # Fakes por dependencia (telegram, yt_dlp, groq, instaloader, tikwm)
│   └── test_*.py               # Un archivo por área (wiki, pipeline, ffmpeg, soundcloud, slides...)
├── downloads/                  # Carpeta de descargas temporales (BASE_DIR, se crea sola)
├── cookies*.txt                # Cookies por plataforma (tiktok/instagram/facebook)
├── ig_session                  # Sesión de Instaloader (opcional)
├── .env.example                # Plantilla de variables de entorno (copia a .env)
├── requirements.txt            # Dependencias de runtime
├── requirements-dev.txt        # Dependencias de desarrollo (pytest)
├── pytest.ini                  # Configuración de pytest (testpaths, asyncio_mode, mark ffmpeg)
├── Dockerfile                  # Imagen python:3.11-slim + ffmpeg + usuario no root
├── .dockerignore               # Excluye credenciales, descargas, .venv y *.md del build
└── .gitignore
```

## Dónde se edita cada cosa

| Quiero cambiar... | Archivo |
| --- | --- |
| Mensaje de bienvenida de `/start` | `multibot.py` (función `start`) |
| Qué comandos/handlers se registran | `multibot.py` (`main`, `add_handler`) |
| Patrones de detección de URLs (plataformas validas) | `bot/config.py` (`RE_PATTERNS`) |
| Límite de tamaño de video (2000 MB) | `bot/config.py` (`LIMITE_MB`) |
| Defaults de variables de entorno | `bot/config.py` (líneas 4–18) y `.env.example` |
| Enrutamiento de un enlace a su pipeline | `bot/handlers/media.py` (`handle_media`) |
| Flujo completo video: descargar → título → merge audio → enviar | `bot/handlers/generic.py` (`handle_video`) |
| Mensajes de error de recuperación | `bot/handlers/media.py` (`ERROR_RECUPERACION`) |
| Carrusel de Instagram | `bot/handlers/instagram.py` |
| Slides de TikTok | `bot/handlers/tiktok.py` + `bot/services/tikwm.py` (`tiktok_slides`) |
| Búsqueda SoundCloud (`find`) | `bot/handlers/soundcloud.py` |
| Comando `/wiki` | `bot/handlers/wiki.py` |
| Prompt y modelo de Groq | `bot/services/groq.py` (`SYSTEM_PROMPT`) |
| Formato de videos de yt-dlp (calidad, codecs, postprocesos) | `bot/services/ytdlp.py` (`make_opts`) |
| Cookies por plataforma | `bot/config.py` (`COOKIES_TT/IG/FB`) — archivos `cookies*.txt` en la raiz |
| Detección/extracción de audio con FFmpeg | `bot/services/ffmpeg.py` |
| Edición de mensajes sin romper el flujo | `bot/utils/messaging.py` |
| Limpieza de URLs, títulos (`views | likes | canal`) | `bot/utils/text.py` |
| Suite de tests | `tests/` — mocks reutilizables en `tests/mocks/`, fixtures globales en `tests/conftest.py` |

## Notas

- `downloads/` no se versiona (solo `.gitkeep`); el bot crea ahí una carpeta por petición y la elimina al terminar.
- `cookies*.txt`, `ig_session` y `.env` no se versionan (`.gitignore`). `cookies_yt.txt` existe en el working tree pero **no se usa** en código: solo `cookies.txt` (TikTok), `cookies_ig.txt` (Instagram) y `cookiesFB.txt` (Facebook).
- Tests con `pytest`; los que generan medios se saltan si `ffmpeg/ffprobe` no estan en el PATH (`pytest.ini`, mark `ffmpeg`).