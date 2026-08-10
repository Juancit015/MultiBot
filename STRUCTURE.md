# MultiBot — Estructura del repositorio

Mapa técnico del código para mantener y depurar el bot. Arquitectura en capas: `multibot.py` (arranque y registro de handlers) → `bot/handlers/` (lógica por comando/tipo de contenido) → `bot/services/` (integraciones externas: yt-dlp, TikWM, Instaloader, Groq, FFmpeg) → `bot/utils/` (helpers de mensajería y texto). `bot/config.py` centraliza config y constantes.

## Árbol

```
multibot.py                # Entry point: load_dotenv, fail-fast de credenciales,
                           # Flask en :7860, registro de handlers, run_polling
Dockerfile                 # Imagen python:3.11-slim + ffmpeg, user no-root
requirements.txt           # Dependencias de runtime (python-telegram-bot >=22.0,<23.0)
requirements-dev.txt       # pytest y pytest-asyncio
.env.example               # Plantilla de variables de entorno (sin secretos)
pytest.ini                 # Config de pytest (testpaths, asyncio_mode, markers)

bot/
├── config.py              # Env vars, rutas base, límite MB, patrones de URL
├── handlers/              # Lógica de comandos y enrutamiento de mensajes
│   ├── media.py           # Enrutador principal de mensajes de texto
│   ├── tiktok.py          # Slides de TikTok (álbum de fotos)
│   ├── instagram.py       # Carruseles de Instagram (Instaloader)
│   ├── generic.py         # Pipeline genérico de video (yt-dlp + ffmpeg + envío)
│   ├── soundcloud.py      # Comando "find <cancion>"
│   └── wiki.py            # Comando /wiki (Groq)
├── services/              # Integraciones externas
│   ├── ytdlp.py           # make_opts y download_with_retry (yt-dlp)
│   ├── tikwm.py           # Fallback de TikTok (API TikWM)
│   ├── groq.py            # Cliente Groq, prompt del sistema, errores/quota
│   ├── ffmpeg.py          # Detección de audio, fusión y extracción (ffprobe/ffmpeg)
│   └── net.py             # fetch_bytes y resolución de URLs cortas
└── utils/                 # Helpers
    ├── messaging.py       # safe_edit / safe_delete sobre mensajes de estado
    └── text.py            # Normalización de URLs, títulos, limpiar_url

tests/                     # Suite pytest (aislada: sin red real, tmp por test)
├── conftest.py            # Fixtures: BASE_DIR temporal, anti-red, medios ffmpeg
├── mocks/                 # Mocks de telegram, tikwm, yt-dlp, groq, instaloader
└── test_*.py              # Comandos, fail-fast, pipeline, ffmpeg, wiki, soundcloud

downloads/                 # Descargas temporales del bot (gitignored, solo .gitkeep)
cookies*.txt               # Cookies de TikTok/Instagram/Facebook (no versionadas)
ig_session                 # Sesión de Instaloader (no versionada)
```

## Dónde se edita cada cosa

| Qué quieres cambiar | Dónde |
| --- | --- |
| Comandos disponibles (registro de handlers, respuestas a chat) | `multibot.py` |
| Variables de entorno, límite de tamaño (2000 MB), patrones de URL, rutas de cookies | `bot/config.py` |
| Qué plataformas se reconocen y en qué orden se procesa un mensaje | `bot/handlers/media.py` |
| Respuesta del comando `/start` | `multibot.py` (función `start`) |
| Comando `/wiki` (mensajes de error, flujo de consulta) | `bot/handlers/wiki.py` |
| Prompt del modelo, manejo de cuota/errores de Groq | `bot/services/groq.py` |
| Búsqueda y descarga de SoundCloud (`find`) | `bot/handlers/soundcloud.py` |
| Slides de TikTok (álbum de fotos, audio de TikWM) | `bot/handlers/tiktok.py` + `bot/services/tikwm.py` |
| Carruseles de Instagram (`/p/...`) | `bot/handlers/instagram.py` |
| Pipeline de descarga de video: opciones de yt-dlp, reintentos, fusión de audio, título, envío | `bot/services/ytdlp.py` + `bot/handlers/generic.py` |
| Lógica de FFmpeg (detección de audio, merge, extracción MP3) | `bot/services/ffmpeg.py` |
| Mensajes de estado "Procesando...", errores de recuperación | `bot/utils/messaging.py`, `bot/handlers/media.py` |
| Normalización de enlaces, títulos con vistas/likes, conversión de URL de Facebook | `bot/utils/text.py` |
| Tests y mocks de las integraciones externas | `tests/` (mocks en `tests/mocks/`) |
| Imagen de despliegue (Python, ffmpeg, usuario no-root) | `Dockerfile` |

## Notas

- **Cookies y sesión:** `cookies*.txt` e `ig_session` se leen si existen en la raíz y se usan como cookies de yt-dlp / sesión de Instaloader. No están versionadas; sin ellas el bot intenta descargas anónimas.
- **Descargas:** `bot/config.py` crea `downloads/` automáticamente; cada mensaje usa una subcarpeta `uuid4` que se elimina al terminar.
- **La suite de tests** redirige `BASE_DIR` a un `tmp_path` y bloquea la red real (`tests/conftest.py`), así que nada escapa al sistema ni a Telegram.