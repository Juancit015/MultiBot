# MultiBot

Bot de Telegram en Python que recibe enlaces de **TikTok, Instagram y Facebook** y los reenvía como video (con audio incrustado) o álbum de fotos, busca canciones en **SoundCloud** escribiendo `find <cancion>` y responde consultas enciclopédicas con `/wiki <consulta>`.

Todo se gestiona desde el chat: pegas el enlace, el bot descarga (hasta 720p), procesa con FFmpeg y te devuelve el video más su MP3 por separado, y en caso de fallo lo intenta por vías alternativas (TikWM como fallback de TikTok).

## Características

- **TikTok** — videos, stories y slideshows (`/photo/`, hasta 10 imágenes + pista de audio vía API TikWM). Resuelve short URLs (`vm.`/`vt.`).
- **Instagram** — posts, reels, stories y carruseles (`/p/`, álbumes enviados en grupos de 10 fotos vía Instaloader).
- **Facebook** — videos y reels (los `/reel/` se convierten a `/watch/?v=`) y enlaces `share`.
- **SoundCloud** — `find <cancion>` descarga el primer resultado (yt-dlp `scsearch1`) y envía portada + MP3.
- **/wiki <consulta>** — respuestas cortas en español (máx. 4 líneas) vía API Groq con formato fijo.
- **Pipeline de video** — yt-dlp (≤720p) + FFmpeg: incrusta audio si falta y envía video y audio por separado; descarta videos de más de 2000 MB con aviso de tamaño/duración.
- **Fail-fast de configuración** — aborta el arranque si faltan credenciales obligatorias.

## Stack

- **Runtime:** Python 3.11 (imagen `python:3.11-slim` en el Dockerfile)
- **Bot:** python-telegram-bot `>=21.0,<22.0` (polling con HTTPX, timeouts largos)
- **Descargas:** yt-dlp `>=2025.1.1` · instaloader `>=4.11.0` (carruseles IG)
- **IA:** groq `>=0.10.0` (consulta `/wiki`, modelo `llama-3.3-70b-versatile`)
- **HTTP:** requests `>=2.31.0` · httpx `>=0.27.0`
- **Salud:** flask `>=3.0.0` (health check en el puerto 7860, hilo daemon)
- **Sistema:** ffmpeg + ffprobe (post-procesado de audio/video) · API externa TikWM (fallback TikTok)
- **Tests:** pytest `>=8,<9` · pytest-asyncio `>=0.23,<1`

## Instalación

1. **Requisitos previos** — Python 3.11+ (el contenedor corre `python:3.11-slim`), Git y **FFmpeg** (incluye `ffprobe`; necesario para el pipeline de audio/video):
   - Linux (Debian/Ubuntu): `sudo apt install -y ffmpeg`
   - macOS: `brew install ffmpeg`
   - Windows: `winget install Gyan.FFmpeg` (o `choco install ffmpeg`)

2. Clonar el repositorio:

   ```bash
   git clone https://github.com/Juancit015/MultiBot.git
   cd MultiBot
   ```

3. Crear y activar el entorno virtual:

   ```bash
   python3 -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   ```

4. Configurar las variables de entorno (el bot aborta si faltan `BOT_TOKEN` o `GROQ_API_KEY`):

   ```bash
   cp .env.example .env   # y rellena BOT_TOKEN (BotFather) y GROQ_API_KEY (console.groq.com)
   ```

5. Instalar dependencias:

   ```bash
   pip install -r requirements.txt
   ```

6. Ejecutar el bot:

   ```bash
   python3 multibot.py
   ```

## Ejecución

```bash
python3 multibot.py
```

- Arranca el bot en modo **polling** contra la API de Telegram usando `BOT_API_BASE_URL` (para proxies de Telegram; default apunta a un proxy en Railway).
- Levanta un servidor Flask de salud en `0.0.0.0:7860` como hilo daemon dentro del mismo proceso.
- Si una variable obligatoria no está rellenada, aborta con `Error: falta la variable de entorno BOT_TOKEN` o `Error: falta la variable de entorno GROQ_API_KEY`.

### Docker

```bash
docker build -t multibot .
docker run -d --name multibot \
  -e BOT_TOKEN=... -e GROQ_API_KEY=... \
  multibot
```

La imagen instala FFmpeg y ejecuta `python3 multibot.py` como usuario no-root (`app`, uid 1001).

## Variables de entorno

| Variable | Requerida | Descripción |
| --- | --- | --- |
| `BOT_TOKEN` | sí | Token del bot de @BotFather. El proceso aborta si falta. |
| `GROQ_API_KEY` | sí | Clave de API de Groq (formato `gsk_…`). El proceso aborta si falta. |
| `TIKWM_API_URL` | no | Endpoint de la API TikWM (slides de TikTok y fallbacks). Default `https://www.tikwm.com/api/`. |
| `BOT_API_BASE_URL` | no | Base URL de la API de Telegram (útil tras un proxy de Telegram). Default `https://multi-api-production.up.railway.app/bot`. |
| `IG_SESSION` | no | Ruta del archivo de sesión de Instagram (Instaloader). Default `ig_session`. |
| `GROQ_MODEL` | no | Modelo Groq para `/wiki`. Default `llama-3.3-70b-versatile`. |
| `GROQ_TEMPERATURE` | no | Temperatura de las respuestas de Groq. Default `0.3`. |
| `GROQ_MAX_TOKENS` | no | Límite de tokens de respuesta de Groq. Default `500`. |

Los archivos `cookies.txt` (TikTok), `cookies_ig.txt` y `cookiesFB.txt` son opcionales: si existen junto al repo, se usan como cookies de yt-dlp por plataforma (están en `.gitignore`).

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

Suite con `pytest` + `pytest-asyncio` (modo async automático). Los tests generan sus propios medios con FFmpeg en carpetas temporales y bloquean la red externa real (mocks de Telegram, Groq, yt-dlp, Instaloader y TikWM); los que requieren binarios FFmpeg se saltan si no están disponibles (`requiere ffmpeg/ffprobe`).

## Solución de problemas

| Mensaje | Causa | Solución |
| --- | --- | --- |
| `Error: falta la variable de entorno BOT_TOKEN` | `.env` no creado o `BOT_TOKEN` vacío | Copiar `.env.example` a `.env` (paso 4) y completar el token; o exportar la variable antes de ejecutar |
| `Error: falta la variable de entorno GROQ_API_KEY` | `GROQ_API_KEY` sin rellenar | Completar la clave en `.env` (paso 4) o exportarla antes de ejecutar |
| ⛔️ No se ha podido recuperar la información de la publicación | Cuenta privada, restricción de edad, enlace no reconocido o stories de Facebook no soportadas | Verificar que el enlace es válido y que la cuenta es pública; si hay cookies de plataforma, refrescarlas |
| Tests que se saltan: `requiere ffmpeg/ffprobe` | `ffmpeg`/`ffprobe` no instalados en el sistema | Instalar FFmpeg según tu OS (paso 1 de la instalación) |

## Estructura del repositorio

Resumen: `multibot.py` (entry point), `bot/config.py` (config por env vars), `bot/handlers/` (lógica por plataforma y comando), `bot/services/` (yt-dlp, FFmpeg, TikWM, Groq, red), `bot/utils/` (texto y mensajería), `tests/` (suite con mocks).

> **Estructura del repositorio:** consultar [STRUCTURE.md](STRUCTURE.md).