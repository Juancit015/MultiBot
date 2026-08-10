# MultiBot

Bot de Telegram en Python que descarga y reenvía contenido de **TikTok, Instagram y Facebook** (videos, reels, stories, carruseles y slideshows con su audio), busca canciones en **SoundCloud** (`find <cancion>`) y responde consultas informativas en **Groq** (`/wiki <consulta>`).

Arranque robusto: valida las credenciales obligatorias antes de iniciar (fail-fast) y levanta un endpoint Flask de healthcheck en paralelo al polling de Telegram.

## Stack

- Runtime: **Python 3.11+** (imagen del contenedor `python:3.11-slim`; no hay restricción de versión en `requirements.txt`)
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) **≥ 21.0, < 22.0** — cliente de la API de Telegram (import: `telegram` / `telegram.ext`)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) **≥ 2025.1.1** — descarga de medias (import: `yt_dlp`), requiere **ffmpeg/ffprobe** en el sistema
- [groq](https://github.com/groq/groq-python) **≥ 0.10.0** — modelo `llama-3.3-70b-versatile` para `/wiki`
- [flask](https://flask.palletsprojects.com/) **≥ 3.0.0** — healthcheck HTTP en el puerto 7860
- [instaloader](https://instaloader.github.io/) **≥ 4.11.0** — carruseles de Instagram (`/p/`)
- [requests](https://requests.readthedocs.io/) **≥ 2.31.0** y [httpx](https://www.python-httpx.org/) **≥ 0.27.0** — HTTP (descargas auxiliares, cliente de Telegram)
- [python-dotenv](https://github.com/theskumar/python-dotenv) **≥ 1.0.0** — carga de `.env` al arrancar
- Desarrollo: pytest **≥ 8, < 9** + pytest-asyncio **≥ 0.23, < 1** (`requirements-dev.txt`)

## Instalación

### 1. Requisitos previos

- **Python 3.11 o superior**
- **Git**
- **ffmpeg y ffprobe** (los usa yt-dlp para fusionar video/audio y extraer MP3)

**Linux / macOS:**
```bash
sudo apt update && sudo apt install -y ffmpeg
```

> En Fedora: `sudo dnf install ffmpeg`. En Arch: `sudo pacman -S ffmpeg`. En macOS con Homebrew: `brew install ffmpeg` (suele venir ya incluido en formularias de yt-dlp).

**Windows:**
Descarga los binarios desde [gyan.dev/ffmpeg/builds](https://www.gyan.dev/ffmpeg/builds/) y añade la carpeta `bin` al `PATH`.

Para verificar: `ffmpeg -version` debe imprimir la versión sin errores.

### 2. Clonar el repositorio

```bash
git clone https://github.com/Juancit015/MultiBot.git
cd MultiBot
```

### 3. Crear y activar el entorno virtual

**Linux / macOS:**
```bash
python -m venv venv
source venv/bin/activate
```

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

El venv es obligatorio: los paquetes se instalan ahí, aislados del Python del sistema. Además evita el bloqueo PEP 668 (`externally-managed-environment`) de muchas distros.

### 4. Configurar `.env`

```bash
cp .env.example .env
```

Edita `.env` y rellena **`BOT_TOKEN`** (de @BotFather) y **`GROQ_API_KEY`** (formato `gsk_...`). El programa carga `.env` automáticamente al arrancar (`load_dotenv()` en `multibot.py`, antes de importar la configuración), así que solo con que el archivo exista y esté relleno basta.

### 5. Instalar dependencias

```bash
pip install -r requirements.txt
```

> Para ejecutar la suite de tests, instala además: `pip install -r requirements-dev.txt`

### 6. Ejecutar

```bash
python multibot.py
```

Todos los comandos de ejecución corren con el venv activado. Si dudas de qué intérprete estás usando, verifica:

```bash
which python
```

La salida debe apuntar dentro de tu venv (por ejemplo `/home/tu_usuario/MultiBot/venv/bin/python`).

## Uso

Una vez corriendo, el bot responde en cualquier chat de Telegram donde esté añadido:

| Comando / entrada | Qué hace |
| --- | --- |
| Enlace de TikTok / Instagram / Facebook | Descarga y reenvía el video (o slideshow/carrusel con su audio MP3) |
| `find <cancion>` | Busca el primer resultado en SoundCloud y envía el MP3 con su thumbnail |
| `/wiki <consulta>` | Respuesta enciclopédica de 2-4 líneas vía Groq |

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

Suite de 9 archivos en `tests/` con mocks de Telegram/yt-dlp/Instaloader/Groq/TikWM: fail-fast de configuración, pipeline de video (con y sin audio), slides/carrusel, SoundCloud, `/wiki` y utilidades. Requiere ffmpeg/ffprobe para los casos de medios reales (marker `ffmpeg`); la red externa está bloqueada fuera de los mocks.

## Docker

El Dockerfile usa `python:3.11-slim`, instala ffmpeg y ejecuta `multibot.py` como usuario no root.

```bash
docker build -t multibot .
docker run --env-file .env -p 7860:7860 multibot
```

## Environment

Definidas en `bot/config.py` y documentadas en `.env.example`. Las dos obligatorias abortan el arranque si faltan (fail-fast).

| Variable | Obligatoria | Default | Descripción |
| --- | --- | --- | --- |
| `BOT_TOKEN` | sí | — | Token del bot (de @BotFather) |
| `GROQ_API_KEY` | sí | — | API key de Groq (formato `gsk_...`) |
| `TIKWM_API_URL` | no | `https://www.tikwm.com/api/` | Endpoint TikWM (slides de TikTok y fallbacks de audio) |
| `BOT_API_BASE_URL` | no | `https://multi-api-production.up.railway.app/bot` | Base URL de la API de Telegram (útil tras un proxy) |
| `IG_SESSION` | no | `ig_session` | Ruta del archivo de sesión de Instagram (Instaloader) |
| `GROQ_MODEL` | no | `llama-3.3-70b-versatile` | Modelo Groq para `/wiki` |
| `GROQ_TEMPERATURE` | no | `0.3` | Temperatura de las respuestas de Groq |
| `GROQ_MAX_TOKENS` | no | `500` | Límite de tokens de respuesta |

## Troubleshooting

| Error | Causa | Solución |
| --- | --- | --- |
| `Error: falta la variable de entorno BOT_TOKEN` | Token sin rellenar en `.env` | Rellenar `BOT_TOKEN` en `.env` (paso 4) y reiniciar |
| `Error: falta la variable de entorno GROQ_API_KEY` | API key sin rellenar en `.env` | Rellenar `GROQ_API_KEY` en `.env` (paso 4) y reiniciar |
| `ModuleNotFoundError: No module named 'telegram'` | El paquete pip `python-telegram-bot` no está instalado: venv no activado o intérprete equivocado | Activar el venv (`source venv/bin/activate`) o usar `<venv>/bin/python multibot.py`; reinstalar con `pip install -r requirements.txt` |
| `error: externally-managed-environment` (PEP 668) | `pip install` ejecutado con el Python del sistema, que rechaza paquetes externos | Crear y activar el venv (paso 3) y repetir el `pip install` dentro |
| `ffmpeg: command not found` / ffprobe ausente | Binarios de ffmpeg no instalados o fuera del `PATH` | Instalar ffmpeg/ffprobe (paso 1) y verificar con `ffmpeg -version` |

---

> **Estructura del repositorio:** consultar [STRUCTURE.md](STRUCTURE.md).