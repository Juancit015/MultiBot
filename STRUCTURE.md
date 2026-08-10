# STRUCTURE.md — Mapa del repositorio

Guía técnica para mantener y extender MultiBot. Todo lo listado existe en el repositorio (verificado contra el árbol actual).

```
.
├── multibot.py               Entry point: valida env, registra handlers y arranca polling
├── bot/                      Paquete principal
│   ├── config.py             Configuración central (env vars, rutas, regex de plataformas)
│   ├── handlers/             Orquestación por dominio
│   │   ├── media.py          Router principal: detecta plataforma y deriva cada enlace
│   │   ├── generic.py        Pipeline de video genérico (título, merge de audio, límite)
│   │   ├── tiktok.py         Slideshows TikTok (gallery de fotos vía TikWM)
│   │   ├── instagram.py      Carruseles de Instagram (Instaloader)
│   │   ├── soundcloud.py     Búsqueda `find <cancion>` (yt-dlp)
│   │   └── wiki.py           Handler de `/wiki` (Groq)
│   ├── services/             Lógica de infraestructura aislada
│   │   ├── ytdlp.py          make_opts + descarga con reintentos (cookies por plataforma)
│   │   ├── ffmpeg.py         Probe de audio, extracción y merge vía ffmpeg/ffprobe
│   │   ├── tikwm.py          Cliente de la API TikWM (slides y fallback de audio TikTok)
│   │   ├── groq.py           Cliente Groq, prompt del sistema y clasificación de errores
│   │   └── net.py            fetch_bytes / resolución de URLs acortadas
│   └── utils/
│       ├── text.py           Regex de plataformas, limpieza y construcción de títulos
│       └── messaging.py      safe_edit / safe_delete defensivos
├── tests/                    Suite pytest (27 tests, aislada de APIs externas)
│   ├── conftest.py           Fixtures: medios ffmpeg en tmp, redirección de BASE_DIR, anti-red
│   ├── mocks/                Simulacros por servicio (Telegram, Groq, TikWM, Instaloader, yt-dlp)
│   └── test_*.py             Un módulo por área (texto, comandos, fail-fast, pipelines, wiki…)
├── pytest.ini                Config pytest (asyncio_mode=auto, marker ffmpeg)
├── requirements.txt          Dependencias de producción (rangos)
├── requirements-dev.txt      pytest + pytest-asyncio
├── Dockerfile                Imagen python:3.11-slim, ffmpeg, usuario no-root `app`
├── .env.example              Plantilla de variables de entorno
├── downloads/                Carpetas de trabajo por descarga (uuid, eliminadas al finalizar)
└── CHANGELOG.md / README.md  Historial de cambios y presentación del proyecto
```

## Dónde se edita cada cosa

| Si querés cambiar… | Editalo en |
|---|---|
| Plataformas soportadas / regex de URLs | `bot/config.py` (`RE_PATTERNS`) y `bot/utils/text.py` |
| Detección y derivación de enlaces | `bot/handlers/media.py` |
| Título de vídeos y formato de métricas | `bot/utils/text.py` (`build_title`, `fmt_num`) |
| Comportamiento de descarga (formato, reintentos, cookies) | `bot/services/ytdlp.py` |
| Flujo de audio (probe, extraer, merge) | `bot/services/ffmpeg.py` + `bot/handlers/generic.py` |
| Slides TikTok y fallback de audio | `bot/handlers/tiktok.py` + `bot/services/tikwm.py` |
| Carruseles de Instagram | `bot/handlers/instagram.py` |
| `/wiki` (prompt, modelo, errores de Groq) | `bot/handlers/wiki.py` + `bot/services/groq.py` |
| Mensaje de bienvenida de `/start` | `multibot.py` |
| Límite de tamaño de video | `bot/config.py` (`LIMITE_MB`) |
| Tests de una plataforma | `tests/test_*.py` + `tests/mocks/` (mock por servicio) |
| Fixtures y aislamiento de la suite | `tests/conftest.py` |

## Notas técnicas

- **Handler → Service**: los handlers nunca hablan con APIs externas directamente; pasan por `bot/services/`. Los imports de servicios dentro de handlers son por nombre (`from bot.services.ffmpeg import …`), por eso la suite parchea atributos en los módulos de handlers, no en los de servicios.
- **Config al importar**: `bot/config.py` lee variables de entorno en tiempo de import (sin `.env` loader). El bot aborta si faltan `BOT_TOKEN`/`GROQ_API_KEY` (`_validar_config` en `multibot.py`).
- **Ciclo de descargas**: `handle_media` crea `downloads/<uuid>`, lo entrega al pipeline y lo elimina en `finally` (los envíos ocurren antes del borrado).
- **Tests**: los marcados `ffmpeg` requieren `ffmpeg`/`ffprobe` en el PATH; los demás son 100 % mocks. Ninguna prueba toca red ni credenciales (guard anti-red en `conftest.py`).
- **Formato de commits**: mensajes en español, un cambio por commit, sin secretos (`git status` antes de cualquier `git add -A`).