# MultiBot

Bot de Telegram en Python que descarga y reenvía contenido de TikTok, Instagram, Facebook y SoundCloud, y responde consultas informativas mediante `/wiki` usando Groq.

Diseñado para ejecutarse en un entorno con Python 3.11 (Docker) y consumir credenciales exclusivamente desde variables de entorno.

## Estado actual

> Estado documentado sobre el working tree actual. El historial fue saneado (53 commits): los archivos de cookies/sesiones y las credenciales dejaron de trackearse y se purgaron del historial. El repositorio no contiene secretos ni credenciales reales.

- HEAD `d357259` (historial saneado) con mejoras posteriores sin commitear en el working tree: hardening del `Dockerfile`, `requirements.txt` con rangos, suite de tests pytest (27 tests) y esta documentación.
- Credenciales rotadas: `BOT_TOKEN`, `GROQ_API_KEY` y cookies/sesiones **no** están en el repositorio (ver [Seguridad](#consideraciones-de-seguridad)).

## Funcionalidades implementadas

| Plataforma | Soporte |
|---|---|
| TikTok | Videos y slideshows (gallery de fotos) con audio |
| Instagram | Posts enlazados, carruseles (varias fotos), stories, reels, IGTV |
| Facebook | Videos (incluida conversión de `/reel/` a `watch?v=`) |
| SoundCloud | Búsqueda `find <cancion>` y descarga de audio |

Además:

- `/wiki <consulta>` — responde preguntas informativas vía Groq (modelo `llama-3.3-70b-versatile` configurable).
- `/start` — mensaje de bienvenida con instrucciones.
- Detección automática de plataforma a partir del enlace.
- Límite de tamaño de video (`LIMITE_MB`) y reintentos de descarga (yt-dlp).

## Arquitectura

```
Config → Handlers → Services → (yt-dlp / ffmpeg / tikwm / groq / requests) → respuesta al chat
```

```
multibot.py                Entry point: valida env, configura el bot y arranca polling
bot/
  config.py                Centraliza toda la configuración (env vars, rutas, regex)
  handlers/                Orquestación por dominio (media, wiki, por plataforma)
  services/                Lógica aislada de infraestructura (yt-dlp, ffmpeg, tikwm, groq, red)
  utils/                   Utilidades transversales (mensajes, formateo de texto)
tests/                     Suite de tests pytest (mocks de Telegram/Groq/tikwm/instaloader)
```

Flujo de arranque (`multibot.py`):

1. `_validar_config()` comprueba `BOT_TOKEN` y `GROQ_API_KEY` (aborta si faltan).
2. Se registran los handlers en `Application` (python-telegram-bot).
3. Se inicia un servidor Flask auxiliar en `0.0.0.0:7860` (daemon) para health-checks del host.
4. `app.run_polling()` escucha actualizaciones de Telegram.

## Requisitos

- Python **3.11** (imagen Docker) o compatible.
- `ffmpeg` y `ffprobe` en el PATH (merge de audio y detección de pistas). Instalación en Debian/Ubuntu: `apt-get install -y ffmpeg`.
- Token de bot creado con [@BotFather](https://t.me/BotFather).
- Clave de la [API de Groq](https://console.groq.com/) (formato `gsk_...`).
- Opcional: archivos de cookies y sesión de Instagram para contenido restringido (ver [Limitaciones](#limitaciones-de-cookies-y-sesiones)).
- Para ejecutar la suite de tests: `pytest` + `pytest-asyncio` (ver [Testing](#testing)) y `ffmpeg`/`ffprobe` para los tests marcados `ffmpeg`.

## Instalación local

```bash
git clone https://github.com/pybot54-crypto/MultiBot.git
cd MultiBot

python3.11 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

> Algunas plataformas requieren una versión reciente de `yt-dlp`. Si hay errores de extracción, actualízalo manualmente:

```bash
pip install -U yt-dlp
```

## Configuración

Copia el archivo de ejemplo y rellena los valores:

```bash
cp .env.example .env
# edita .env con tus valores
```

> **Importante**: `.env` está en `.gitignore` — nunca debe versionarse.

### Obligatorias (el bot aborta si faltan)

| Variable | Descripción |
|---|---|
| `BOT_TOKEN` | Token del bot de Telegram creado con @BotFather |
| `GROQ_API_KEY` | API key de Groq (formato `gsk_...`) |

### Opcionales (valor por defecto en `bot/config.py`)

| Variable | Default | Descripción |
|---|---|---|
| `TIKWM_API_URL` | `https://www.tikwm.com/api/` | Endpoint API TikWM (slides de TikTok, fallbacks) |
| `BOT_API_BASE_URL` | `https://multi-api-production.up.railway.app/bot` | Base URL de la API de Telegram (útil tras un proxy de Telegram) |
| `IG_SESSION` | `ig_session` | Ruta del archivo de sesión de Instagram (Instaloader) |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Modelo Groq para `/wiki` |
| `GROQ_TEMPERATURE` | `0.3` | Temperatura de la respuesta |
| `GROQ_MAX_TOKENS` | `500` | Límite de tokens de respuesta |

## Uso

```bash
source .venv/bin/activate
python multibot.py
```

En Telegram:

1. Abre tu bot y pídele que inicie (o escribe `/start`).
2. Pega un enlace de TikTok, Instagram o Facebook → el bot descarga y envía el video/imágenes.
3. Escribe `find <cancion>` → busca y envía el audio de SoundCloud.
4. Usa `/wiki <tema>` para obtener una respuesta informativa.
5. `/start` muestra el mensaje de bienvenida.

## Testing

Suite de regresión de **27 tests pytest**, aislada de credenciales, Telegram, Groq y APIs externas (mocks de Telegram, Groq, TikWM, Instaloader y yt-dlp en `tests/mocks/`).

```bash
# Dependencias de desarrollo
pip install -r requirements-dev.txt

# Suite completa
pytest

# Solo los tests que requieren FFmpeg real
pytest -m ffmpeg
```

Notas:

- Los tests marcados `ffmpeg` (5) ejercitan `bot/services/ffmpeg.py` de verdad (probe de audio, extracción y merge) y se **omiten** si `ffmpeg`/`ffprobe` no están en el PATH.
- Los medios de prueba se generan en tiempo de ejecución (lavfi) en `/tmp` — no se versionan binarios.
- Ejecución dentro del contenedor de la imagen:

```bash
docker run --rm -v $PWD:/app -w /app multibot sh -c "pip install -q -r requirements-dev.txt && pytest"
```

## Docker

### Build y ejecución

```bash
docker build -t multibot .
docker run --rm \
  -e BOT_TOKEN="tu_token" \
  -e GROQ_API_KEY="tu_gsk_key" \
  multibot
```

- Imagen base `python:3.11-slim`; instala `ffmpeg` y las dependencias de `requirements.txt`.
- Ejecuta como usuario no-root `app` (uid/gid 1001); solo `/app/downloads` es escribible.
- Las variables de entorno se pasan **en runtime**; nunca hay que incorporarlas a la imagen.

## Estructura de directorios

```
.
├── bot/
│   ├── __init__.py
│   ├── config.py            Configuración central (env, rutas, regex)
│   ├── handlers/
│   │   ├── generic.py       Pipeline de video genérico
│   │   ├── instagram.py     Carruseles + instaloader
│   │   ├── tiktok.py        Slideshows (gallery de fotos)
│   │   ├── soundcloud.py    Búsqueda `find <cancion>`
│   │   ├── media.py         Router principal
│   │   └── wiki.py          Handler de `/wiki`
│   ├── services/
│   │   ├── ffmpeg.py        Fusiona y extrae audio
│   │   ├── groq.py          Cliente Groq y manejo de fallos
│   │   ├── net.py           fetch / resolución de URLs acortadas
│   │   ├── tikwm.py         API TikWM
│   │   └── ytdlp.py         Descarga con reintentos
│   └── utils/
│       ├── messaging.py     safe_edit / safe_delete
│       └── text.py          Regex, URLs, construcción de títulos
├── tests/
│   ├── mocks/               Telegram, Groq, TikWM, Instaloader, yt-dlp simulados
│   ├── conftest.py          Fixtures (medios ffmpeg, aislamiento BASE_DIR, anti-red)
│   └── test_*.py            27 tests de regresión
├── downloads/               Carpeta de trabajo (ignorada por git)
├── multibot.py              Entry point
├── pytest.ini               Configuración de pytest (asyncio_mode, marker ffmpeg)
├── requirements.txt         Dependencias de producción
├── requirements-dev.txt     Dependencias de desarrollo (pytest)
└── Dockerfile
```

## Limitaciones de cookies y sesiones

- **Descargas públicas** funcionan sin credenciales mediante `yt-dlp`.
- Para **contenido restringido** (cuentas privadas o límites) se usan archivos de cookies en **formato Netscape**:
  - `cookies.txt` (TikTok)
  - `cookies_ig.txt` (Instagram)
  - `cookiesFB.txt` (Facebook)
- Los **carruseles de Instagram** usan **Instaloader** con una sesión: archivo `ig_session` (variable `IG_SESSION`).
- Estos archivos **no están en el repositorio**: se eliminó su tracking y se purgaron del historial, y están en `.gitignore` como bloque. El bot los busca en la raíz del proyecto en runtime; si no existen, intenta descargar sin ellos (y puede fallar ante cuentas privadas/restricciones de la plataforma).
- Obtener estos archivos implica iniciar sesión manualmente y exportar cookies a formato Netscape; es un proceso externo al proyecto y sujeto a los términos de servicio de cada plataforma.

## Consideraciones de seguridad

- **Sin secretos en el repositorio**: las credenciales solo viven en variables de entorno.
- **Fail-fast**: el bot aborta si faltan `BOT_TOKEN` o `GROQ_API_KEY`.
- Archivos sensibles en `.gitignore`: `cookies*.txt`, `ig_session`, `instagram_session`, `fb_session`, `*.session`, `.env`, `.env.*` (con excepción para `.env.example`).
- **Historial saneado**: se usó Git filter-repo; los secretos ya no existen en ningún commit, y la recomendación es no volver a subir archivos sensibles (revisar `git status` antes de commitear).
- Los logs no imprimen credenciales.
- El contenedor ejecuta como usuario **no-root** (`app`), minimizando el impacto de un hipotético compromiso.
- `yt-dlp` usa internamente `nocheckcertificate=True` (compromiso común de la herramienta; asume una red de confianza).

## Despliegue (Railway u otro PaaS)

1. Conecta el repositorio a **Railway** (o despliega la imagen construida).
2. Define las variables de entorno en **Settings → Variables**:
   - Obligatorias: `BOT_TOKEN`, `GROQ_API_KEY`.
   - Opcionales: `TIKWM_API_URL`, `BOT_API_BASE_URL`, `IG_SESSION`, `GROQ_MODEL`, `GROQ_TEMPERATURE`, `GROQ_MAX_TOKENS`.
3. El contenedor ejecuta `CMD ["python3", "multibot.py"]`.

Notas:

- Ajusta `BOT_API_BASE_URL` si por proxy de Telegram la API pública no es accesible en tu región.
- Es un proceso de **long-running** (long-polling): configura el servicio como **On**, no como one-shot.
- El contenedor incluye `ffmpeg` (necesario para merge/extract de audio).

## Verificaciones de seguridad

```bash
# Secretos en el historial (0 resultados esperados)
git grep -n -E "gsk_[A-Za-z0-9]{20,}|[0-9]{6,13}:[A-Za-z0-9_-]{30,}" $(git rev-list --all) | wc -l

# Archivos sensibles deben estar ignorados
git check-ignore cookies.txt ig_session .env .env.example 2>/dev/null
```

## Licencia

Sin licencia definida en el repositorio.
# MultiBot
