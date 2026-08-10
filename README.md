# MultiBot

Bot de Telegram en Python que descarga y envía media desde TikTok, Instagram, Facebook y SoundCloud, e incluye un comando `/wiki` con respuestas generadas por Groq.

`git clone https://github.com/Juancit015/MultiBot.git`

## Qué hace

- Detecta enlaces de TikTok, Instagram y Facebook en cualquier mensaje y los descarga con `yt-dlp` (con fallbacks vía TikWM para TikTok y audio de la API nativa de TikTok).
- Convierte y compone audio/video con FFmpeg (`bot/services/ffmpeg.py`) y reenvía el resultado adaptado al límite de Telegram (`LIMITE_MB=2000`).
- `find <cancion>` busca y envía pistas de SoundCloud (`bot/handlers/soundcloud.py`).
- `/wiki <consulta>` responde consultas con Groq (`bot/handlers/wiki.py`).
- Acepta sesiones de cookies (TikTok, Instagram, Facebook, YouTube) para descargas autenticadas.

## Stack

- Backend: Python (`.py` con `match` → requiere **Python ≥ 3.10**; el `Dockerfile` usa `python:3.11-slim`).
- Telegram: `python-telegram-bot` ≥ 21 (`multibot.py`).
- Descargas: `yt-dlp` ≥ 2025.1.1 + `instaloader` (Instagram).
- Fallbacks/metadatos: TikWM API, API nativa de TikTok.
- `/wiki`: SDK `groq`.
- Servicio auxiliar: Flask (port `7860`) para el health-check/keep-alive del bot.
- Buffer HTTP: `httpx` con `HTTPXRequest` en `Application.builder()`.
- Requisito externo: **FFmpeg/FFprobe** invocados por `PATH` (`bot/services/ffmpeg.py`).

## Requisitos

- Python ≥ 3.10 (cualquier binario `python` del sistema; no hace falta una versión fija).
- FFmpeg y FFprobe en `PATH` (el código los invoca como `ffmpeg`/`ffprobe`):
  - **Arch Linux:** `sudo pacman -S ffmpeg`
  - **Debian/Ubuntu:** `sudo apt install ffmpeg`
  - **Windows:** `winget install ffmpeg`

## Setup

```bash
python -m venv .venv          # usa el binario `python` del sistema (>= 3.10)
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # rellena BOT_TOKEN y GROQ_API_KEY
```

El venv se crea con el `python` del sistema: PEP 668 impide `pip install` global en varias distros (Arch, Debian 12+), pero dentro de un venv la instalación funciona sin `--break-system-packages`. No uses un binario `python3.11` fuera de la imagen Docker: en muchos sistemas host no existe.

Copia los archivos `cookies*.txt` e `ig_session` (de tu propia sesión) en la raíz si quieres descargas autenticadas.

## Run

```bash
python multibot.py
```

El bot exige `BOT_TOKEN` y `GROQ_API_KEY` (aborta si faltan, ver `_validar_config`). Levanta un servidor Flask en el puerto `7860` y arranca el long-pooling contra la API de Telegram.

## Environment

| Variable | Requerida | Descripción |
| --- | --- | --- |
| `BOT_TOKEN` | sí | Token del bot de @BotFather |
| `GROQ_API_KEY` | sí | API key de Groq para `/wiki` |
| `TIKWM_API_URL` | no | Endpoint TikWM (por defecto `https://www.tikwm.com/api/`) |
| `BOT_API_BASE_URL` | no | Base URL de la API de Telegram (por defecto proxy Railway) |
| `IG_SESSION` | no | Archivo de sesión de Instaloader (por defecto `ig_session`) |
| `GROQ_MODEL` | no | Modelo Groq (por defecto `llama-3.3-70b-versatile`) |
| `GROQ_TEMPERATURE` | no | Temperatura de Groq (por defecto `0.3`) |
| `GROQ_MAX_TOKENS` | no | Límite de tokens de respuesta (por defecto `500`) |

Los archivos descargados se guardan en `downloads/` (`BASE_DIR` en `bot/config.py`).

## Docker

```bash
docker build -t multibot .
docker run --rm -e BOT_TOKEN=TU_TOKEN -e GROQ_API_KEY=TU_KEY multibot
```

La imagen base es `python:3.11-slim` e instala FFmpeg en el build; corre como usuario no-root en `/app` con `downloads/` escribible (ver `Dockerfile`).

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

Suite de 27 tests con mocks de Telegram/TikWM/yt-dlp/Groq/Instaloader (`tests/mocks/`). El marcador `ffmpeg` requiere FFmpeg en el sistema.

## Estructura

- `multibot.py` — entry point: validación + polling + Flask.
- `bot/config.py` — variables de entorno, rutas y patrones URL.
- `bot/handlers/` — comandos y despacho de media por plataforma.
- `bot/services/` — yt-dlp, FFmpeg, TikWM, Groq y red.
- `bot/utils/` — helpers de texto y envío.
- `tests/` — suite pytest.
- `downloads/` — salida de descargas.
- `.env.example` — plantilla de variables de entorno.

> **Estructura del repositorio:** consultar [STRUCTURE.md](STRUCTURE.md).