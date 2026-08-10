# MultiBot

Bot de Telegram en Python que descarga y envía media desde TikTok, Instagram, Facebook y SoundCloud, e incluye un comando `/wiki` con respuestas generadas por Groq.

`git clone https://github.com/Juancit015/MultiBot.git`

## Qué hace

- Detecta enlaces de TikTok, Instagram y Facebook en cualquier mensaje y los descarga con `yt-dlp` (con fallbacks vía TikWM para slides de TikTok y audio extraído/compuesto con FFmpeg).
- `find <cancion>` busca y envía pistas de SoundCloud (`bot/handlers/soundcloud.py`).
- `/wiki <consulta>` responde consultas enciclopédicas con Groq (`bot/handlers/wiki.py`).
- Envía el resultado adaptado al límite de Telegram (`LIMITE_MB=2000` en `bot/config.py`).
- Acepta sesiones de cookies para descargas autenticadas: `cookies.txt` (TikTok), `cookies_ig.txt` (Instagram) y `cookiesFB.txt` (Facebook), leídas desde la raíz del repo.

## Stack

- Backend: Python (sin versión estricta en el código ni en `requirements.txt`; la imagen Docker usa `python:3.11-slim` y el entorno local se probó con Python 3.14).
- Telegram: `python-telegram-bot` >= 21 (`multibot.py`), con `httpx`/`HTTPXRequest` para el polling.
- Descargas: `yt-dlp` >= 2025.1.1 + `instaloader` (carruseles de Instagram).
- Fallbacks/metadatos: API TikWM (`bot/services/tikwm.py`).
- `/wiki`: SDK `groq`.
- Servicio auxiliar: Flask en `0.0.0.0:7860` (daemon de health-check/keep-alive, ver `multibot.py`).
- Requisito externo: **FFmpeg/FFprobe** invocados por `PATH` (`bot/services/ffmpeg.py`).

## Requisitos

- Python >= 3.8 (mínimo exigido por las dependencias; `python-telegram-bot` >= 21). Cualquier binario `python` del sistema sirve; no hace falta una versión fija.
- FFmpeg y FFprobe en `PATH` (el código los invoca como `ffmpeg`/`ffprobe`):
  - **Arch Linux:** `sudo pacman -S ffmpeg`
  - **Debian/Ubuntu:** `sudo apt install ffmpeg`
  - **Windows:** `winget install ffmpeg`

## Setup

```bash
python -m venv .venv          # usa el binario `python` del sistema (>= 3.8)
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # rellena BOT_TOKEN y GROQ_API_KEY
```

El venv se crea con el `python` del sistema: PEP 668 impide `pip install` global en varias distros (Arch, Debian 12+), pero dentro de un venv la instalación funciona sin `--break-system-packages`.

Copia los archivos `cookies*.txt` (`cookies.txt`, `cookies_ig.txt`, `cookiesFB.txt`) e `ig_session` (de tu propia sesión) en la raíz si quieres descargas autenticadas.

## Run

```bash
python multibot.py
```

El bot exige `BOT_TOKEN` y `GROQ_API_KEY` (aborta si faltan, ver `_validar_config`). Levanta un servidor Flask en el puerto `7860` y arranca el long-polling contra la API de Telegram (por defecto a través del proxy `BOT_API_BASE_URL`).

## Environment

| Variable | Requerida | Descripción |
| --- | --- | --- |
| `BOT_TOKEN` | sí | Token del bot de @BotFather |
| `GROQ_API_KEY` | sí | API key de Groq para `/wiki` |
| `TIKWM_API_URL` | no | Endpoint TikWM (por defecto `https://www.tikwm.com/api/`) |
| `BOT_API_BASE_URL` | no | Base URL de la API de Telegram (por defecto proxy Railway `https://multi-api-production.up.railway.app/bot`) |
| `IG_SESSION` | no | Archivo de sesión de Instaloader (por defecto `ig_session`) |
| `GROQ_MODEL` | no | Modelo Groq para `/wiki` (por defecto `llama-3.3-70b-versatile`) |
| `GROQ_TEMPERATURE` | no | Temperatura de Groq (por defecto `0.3`) |
| `GROQ_MAX_TOKENS` | no | Límite de tokens de respuesta (por defecto `500`) |

Los archivos descargados se guardan en `downloads/` (`BASE_DIR` en `bot/config.py`), que el bot crea al arrancar.

## Docker

```bash
docker build -t multibot .
docker run --rm -e BOT_TOKEN=TU_TOKEN -e GROQ_API_KEY=TU_KEY multibot
```

La imagen base es `python:3.11-slim` e instala FFmpeg en el build; corre como usuario no-root (`uid 1001`) en `/app`, con `downloads/` escribible (ver `Dockerfile`).

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

Suite de 27 tests con mocks de Telegram/TikWM/yt-dlp/Groq/Instaloader (`tests/mocks/`). El marcador `ffmpeg` requiere FFmpeg en el sistema (config en `pytest.ini`).

## Estructura

- `multibot.py` — entry point: validación de config, polling y Flask 7860.
- `bot/config.py` — variables de entorno, rutas y patrones URL.
- `bot/handlers/` — comandos y despacho de media por plataforma.
- `bot/services/` — yt-dlp, FFmpeg, TikWM, Groq y red.
- `bot/utils/` — helpers de texto y envío.
- `tests/` — suite pytest.
- `downloads/` — salida de descargas.
- `.env.example` — plantilla de variables de entorno.

> **Estructura del repositorio:** consultar [STRUCTURE.md](STRUCTURE.md).