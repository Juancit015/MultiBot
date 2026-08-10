# MultiBot

Bot de Telegram en Python que descarga y reenvía contenido de TikTok, Instagram y Facebook (videos, carruseles, slides y stories), busca canciones en SoundCloud con `find <cancion>` y responde consultas enciclopédicas con `/wiki <consulta>` usando Groq.

- Descarga de videos TikTok / Instagram / Facebook con yt-dlp.
- Carruseles de Instagram (`/p/...`) con Instaloader y slides de TikTok (`/photo/...`) con TikWM + yt-dlp.
- Extracción y fusión de audio con FFmpeg (envía MP3 separado).
- Búsqueda de audio en SoundCloud (`find <cancion>`).
- Consultas informativas con Groq (`/wiki <consulta>`).
- Servidor Flask interno en el puerto `7860` (healthcheck, se inicia junto al bot).

## Stack

| Componente | Versión verificada | Fuente |
| --- | --- | --- |
| Python | 3.11 (imagen) / 3.14 host | `Dockerfile` (`python:3.11-slim`); smoke test en 3.14.6 |
| python-telegram-bot | 22.8 (`>=22.0,<23.0`) | `requirements.txt` |
| yt-dlp | 2026.7.4 (`>=2025.1.1`) | `requirements.txt` |
| groq | 1.6.0 (`>=0.10.0`) | `requirements.txt` |
| Flask | 3.1.3 (`>=3.0.0`) | `requirements.txt` |
| requests | 2.34.2 (`>=2.31.0`) | `requirements.txt` |
| httpx | 0.28.1 (`>=0.27.0`) | `requirements.txt` |
| instaloader | 4.15.3 (`>=4.11.0`) | `requirements.txt` |
| python-dotenv | 1.2.2 (`>=1.0.0`) | `requirements.txt` |
| pytest (dev) | 8.4.2 (`>=8,<9`) | `requirements-dev.txt` |

Rango de runtime documentado con respaldo: **Python 3.11+**, probado en 3.11 (imagen del Dockerfile) y 3.14.6 (host del smoke test: arranque + suite completa). `python-telegram-bot` 22.x requiere Python >= 3.10.

## Características

| Comando / entrada | Qué hace |
| --- | --- |
| Enlace de TikTok / Instagram / Facebook | Descarga y reenvía el video (con audio incrustado y MP3 aparte) |
| Enlace TikTok con `/photo/` | Slides con audio, vía TikWM |
| Enlace Instagram con `/p/` | Carrusel de fotos, vía Instaloader |
| `find <cancion>` | Búsqueda y descarga de audio en SoundCloud |
| `/wiki <consulta>` | Consulta enciclopédica con Groq (modelo `llama-3.3-70b-versatile`) |
| `/start` | Mensaje de bienvenida |

## Instalación y ejecución

### 1. Requisitos previos

Necesitas **Python 3.11+**, **Git** y los binarios **ffmpeg/ffprobe** (los usa yt-dlp y el pipeline de audio).

Instala todo por SO:

Debian / Ubuntu (apt):
```
sudo apt update && sudo apt install -y python3 python3-venv git ffmpeg
```

Fedora (dnf):
```
sudo dnf install -y python3 python3-virtualenv git ffmpeg
```

Arch / Manjaro (pacman):
```
sudo pacman -S --noconfirm python python-virtualenv git ffmpeg
```

macOS (Homebrew):
```
brew install python@3.12 git ffmpeg
```

Windows (winget):
```
winget install Python.Python.3.12 Git.Git Gyan.FFmpeg
```

En macOS el comando `python3` del sistema puede ser muy antiguo: si tras instalarlo `python3 --version` no reporta 3.11+, usa el interpretado de Homebrew con `export PATH="/opt/homebrew/opt/python@3.12/bin:$PATH"` (o `$(brew --prefix)/opt/python@3.12/bin/python3`).

### 2. Clonar el repositorio

```
git clone https://github.com/Juancit015/MultiBot.git && cd MultiBot
```

### 3. Crear y activar el entorno virtual

```
python3 -m venv venv
```

Linux / macOS:

```
source venv/bin/activate
```

Windows (PowerShell):

```
venv\Scripts\Activate.ps1
```

Windows (CMD):

```
venv\Scripts\activate.bat
```

Desde aquí, todos los comandos de este README corren **con el venv activado**. Verifica que `python` apunta al del venv antes de continuar:

```
which python
```

La salida debe incluir la carpeta `venv/` (y no `/usr/bin/python`).

### 4. Configurar las variables de entorno

```
cp .env.example .env
```

El programa **sí carga `.env` automáticamente** (`load_dotenv()` en `multibot.py` antes de importar `bot.config`). Edita `.env` y rellena al menos las dos obligatorias: `BOT_TOKEN` (token de @BotFather) y `GROQ_API_KEY` (clave de Groq, formato `gsk_...`). Si faltan, el bot aborta al arrancar con un mensaje claro. El resto de variables son opcionales; sus valores por defecto están en `bot/config.py` (ver tabla más abajo).

### 5. Instalar dependencias

```
pip install -r requirements.txt
```

Para ejecutar la suite de tests, instala también las dependencias de desarrollo:

```
pip install -r requirements-dev.txt
```

### 6. Ejecutar

```
python multibot.py
```

El bot hace polling a Telegram y levanta el servidor HTTP interno en `http://0.0.0.0:7860` (también accesible vía `http://localhost:7860`). Al arrancar, verifica el token con una llamada a `getMe`; si es inválido, aborta con un error de Telegram.

## Tests

```
pytest
```

Runs the full suite (27 tests): handlers, pipeline de video con FFmpeg real, carrusel/slides con mocks, wiki con cliente Groq simulado y fail-fast de configuración. Los tests que requieren FFmpeg se saltan si los binarios no están disponibles.

## Docker

El repo incluye un `Dockerfile` (imagen `python:3.11-slim`, usuario no root `app`, instala `ffmpeg`):

```
docker build -t multibot .
docker run --env-file .env multibot
```

Las variables se pasan con `--env-file .env` (mismo formato que el paso 4). El contexto de build excluye credenciales, descargas y documentación (`.dockerignore`).

## Variables de entorno

| Variable | Requerida | Default | Descripción |
| --- | --- | --- | --- |
| `BOT_TOKEN` | sí | — | Token del bot, de @BotFather. Sin ella el bot aborta |
| `GROQ_API_KEY` | sí | — | API key de Groq (`gsk_...`). Sin ella el bot aborta |
| `BOT_API_BASE_URL` | no | `https://api.telegram.org/bot` | Base URL de la API de Telegram (útil tras un proxy de Telegram; debe terminar en `bot` + token) |
| `TIKWM_API_URL` | no | `https://www.tikwm.com/api/` | API TikWM (slides de TikTok y fallbacks de audio) |
| `IG_SESSION` | no | `ig_session` | Ruta del archivo de sesión de Instaloader |
| `GROQ_MODEL` | no | `llama-3.3-70b-versatile` | Modelo Groq para `/wiki` |
| `GROQ_TEMPERATURE` | no | `0.3` | Temperatura de las respuestas de Groq |
| `GROQ_MAX_TOKENS` | no | `500` | Límite de tokens de respuesta de Groq |

> **`BOT_API_BASE_URL` (corregido 2026-08-09):** el default anterior (`https://multi-api-production.up.railway.app/bot`) generaba `…/bot<TOKEN>/getMe`, ruta que ese gateway no enruta (404 con tokens válidos). El default ahora es el oficial `https://api.telegram.org/bot` (verificado: smoke test → 401 con token falso, URL bien formada). Nota: ese gateway railway es incompatible con `python-telegram-bot`: con `/bot` responde 404 y sin el sufijo `/bot` la librería rechaza la URL (`InvalidURL: Invalid port`). Si usas un proxy, debe enrutar `bot<TOKEN>/<método>` como la API oficial.

## Troubleshooting

| Error (mensaje literal) | Causa | Solución |
| --- | --- | --- |
| `Error: falta la variable de entorno BOT_TOKEN` / `Error: falta la variable de entorno GROQ_API_KEY` | variable no rellenada; el bot hace fail-fast en `multibot.py` | rellenar `.env` (paso 4) o exportar la variable antes de ejecutar |
| `HTTP Request: POST https://…/bot<TOKEN>/getMe "HTTP/1.1 404 Not Found"` seguido de `telegram.error.InvalidToken: The token '<TOKEN>' was rejected by the server.` y `Network Retry Loop (Bootstrap Initialize Application): Invalid token. Aborting retry loop.` | (a) token inválido/vencido (la API oficial responde `401 Unauthorized`); (b) `BOT_API_BASE_URL` apuntando a un proxy cuyo enrutamiento no acepta `bot<TOKEN>/<método>` | revisar el token; usar un proxy compatible con la ruta `bot<TOKEN>/<método>` (el default oficial ya funciona) |
| `telegram.error.NetworkError: Unknown error in HTTP implementation: InvalidURL("Invalid port: 'TEST'")` | `BOT_API_BASE_URL` sin prefijo `bot` antes del token (p. ej. el gateway railway sin `/bot`): el `:` del token rompe el parseo de URL de httpx | usar `https://api.telegram.org/bot` u otra URL que termine en `bot` (el token va pegado después) |
| `ModuleNotFoundError: No module named 'telegram'` | el paquete instalable es `python-telegram-bot`, pero el import es `telegram`; el error aparece al usar el intérprete equivocado o sin venv activado | activar el venv (`source venv/bin/activate`) o ejecutar con `venv/bin/python multibot.py`; reinstalar con `pip install -r requirements.txt` |
| `error: externally-managed-environment` (pip rechaza la instalación) | PEP 668: el Python del sistema bloquea `pip install` fuera de venv | usar el venv del paso 3; no instalar dependencias con el `pip` del sistema |
| `RuntimeError: This event loop is already running` / problemas de asyncio al arrancar | runtime de Python más nuevo que el verificado con `python-telegram-bot` | usar Python 3.11–3.14 (rango verificado) o actualizar `python-telegram-bot` dentro del rango `>=22,<23` |

> **Estructura del repositorio:** consultar [STRUCTURE.md](STRUCTURE.md).