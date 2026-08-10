# MultiBot

Bot de Telegram que descarga y envía videos de **TikTok**, **Instagram** y **Facebook**, extrae el audio y busca canciones en **SoundCloud**. Incluye un comando `/wiki` que responde consultas enciclopédicas mediante la API de **Groq** (modelo Llama).

Funciona por mensaje directo: envía el enlace de una publicación (o `find <cancion>` para SoundCloud) y el bot responde con el video/audio dentro de Telegram.

## Stack

- **Python** — 3.11+ (probado en 3.11 con el Dockerfile `python:3.11-slim` y en 3.14 en el host).
- **python-telegram-bot** — `>=22.0,<23.0`. Se importa como `telegram`. Las versiones `<22.0` fallan con Python 3.12+ (`RuntimeError: There is no current event loop`).
- **Flask** — `>=3.0.0`. Solo sirve de health-endpoint pasivo en `:7860`, en un hilo `daemon` secundario.
- **yt-dlp** — `>=2025.1.1`. Descarga de TikTok, Instagram, Facebook y SoundCloud.
- **groq** — `>=0.10.0`. Backend del comando `/wiki`.
- **instaloader** — `>=4.11.0`. Carruseles y slides de Instagram (`/p/...`).
- **python-dotenv** — `>=1.0.0`. Carga `.env` al arrancar.
- **requests** — `>=2.31.0`, **httpx** — `>=0.27.0`. Clientes HTTP internos.
- **FFmpeg** — binario de sistema (`ffmpeg`/`ffprobe`): incrusta MP3 en el video, extrae audio y es requerido por la suite de tests.
- **Tests** — `pytest>=8,<9` + `pytest-asyncio>=0.23,<1` (ver `requirements-dev.txt`).

## Instalación

### 1. Requisitos previos

- **Python 3.11+ con `venv`** (probado en 3.11 y 3.14). En Debian/Ubuntu el paquete es `python3-venv`.
- **Git**.
- **FFmpeg** — necesario para la fusión/extracción de audio y para los tests.

Instala FFmpeg según tu sistema:

Debian / Ubuntu:

```bash
sudo apt install ffmpeg
```

Fedora / RHEL:

```bash
sudo dnf install ffmpeg
```

Arch Linux:

```bash
sudo pacman -S ffmpeg
```

macOS (con Homebrew):

```bash
brew install ffmpeg
```

Windows (con winget):

```bash
winget install Gyan.FFmpeg
```

### 2. Clonar el repositorio

```bash
git clone https://github.com/Juancit015/MultiBot.git
cd MultiBot
```

### 3. Crear y activar el entorno virtual

Linux / macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

Windows (PowerShell):

```powershell
py -m venv venv
venv\Scripts\Activate.ps1
```

Windows (CMD):

```cmd
py -m venv venv
venv\Scripts\activate.bat
```

A partir de aquí, todos los comandos de instalación y ejecución usan el `python` del venv activado (verificable con `which python`).

### 4. Configurar las variables de entorno

```bash
cp .env.example .env
```

El arranque lee el archivo `.env` de la raíz: `multibot.py` llama a `load_dotenv()` antes de importar `bot/config.py`, por lo que las variables se cargan siempre al arrancar. Rellena al menos los dos valores obligatorios (`BOT_TOKEN` y `GROQ_API_KEY`); si faltan, el bot aborta con `Error: falta la variable de entorno ...`.

### 5. Instalar dependencias

```bash
pip install -r requirements.txt
```

Para correr la suite de tests, además:

```bash
pip install -r requirements-dev.txt
```

### 6. Ejecutar

```bash
python multibot.py
```

El bot levanta Flask en `http://0.0.0.0:7860` (útil como health-check) y arranca el polling de Telegram. Cuando está listo imprime `Bot corriendo...`. El arranque solo falla por credenciales inválidas o falta de conexión con la API de Telegram.

## Uso

- **Descargar video/audio:** envía un enlace de TikTok, Instagram o Facebook. Los carruseles de Instagram y los slides de TikTok se envían como álbum de fotos.
- **Buscar en SoundCloud:** `find <canción>`.
- **Consulta enciclopédica:** `/wiki <consulta>`.

## Variables de entorno

| Variable | Obligatoria | Descripción |
| --- | --- | --- |
| `BOT_TOKEN` | sí | Token del bot de BotFather. El bot aborta si falta. |
| `GROQ_API_KEY` | sí | Clave de Groq (formato `gsk-...`). El bot aborta si falta. |
| `TIKWM_API_URL` | no | Endpoint de TikWM para slides de TikTok y fallbacks. Default: `https://www.tikwm.com/api/`. |
| `BOT_API_BASE_URL` | no | Base URL de la API de Telegram (útil tras un proxy). Default: `https://multi-api-production.up.railway.app/bot`. |
| `IG_SESSION` | no | Ruta de sesión de Instaloader. Default: `ig_session`. |
| `GROQ_MODEL` | no | Modelo de Groq para `/wiki`. Default: `llama-3.3-70b-versatile`. |
| `GROQ_TEMPERATURE` | no | Temperatura de las respuestas de Groq. Default: `0.3`. |
| `GROQ_MAX_TOKENS` | no | Límite de tokens de respuesta de Groq. Default: `500`. |

## Tests

```bash
pytest
```

La suite aísla la red y los archivos temporales (fixtures en `tests/conftest.py`). Los tests que requieren FFmpeg se saltan automáticamente si el binario no está disponible.

## Troubleshooting

| Error | Causa | Solución |
| --- | --- | --- |
| `RuntimeError: There is no current event loop` al arrancar | `python-telegram-bot` `<22.0` (no compatible con Python 3.12+/3.14) | `pip install -U "python-telegram-bot>=22.0,<23.0"` |
| `Error: falta la variable de entorno BOT_TOKEN` / `GROQ_API_KEY` | `.env` vacío, no copiado o valores en blanco | Copiar `.env.example` a `.env` y rellenar los valores (paso 4) |
| `ModuleNotFoundError: No module named 'telegram'` | Paquete `python-telegram-bot` no instalado, o se está usando el intérprete del sistema sin venv | Activar el venv (`source venv/bin/activate`) o usar `venv/bin/python multibot.py` |
| `error: externally-managed-environment` (PEP 668) | pip del sistema bloqueado en Debian/Ubuntu | Usar el venv del paso 3, nunca `pip` global |
| Fallos de audio / `ffmpeg not found` | Binarios `ffmpeg`/`ffprobe` ausentes | Instalar FFmpeg según tu SO (paso 1) |

> **Estructura del repositorio:** consultar [STRUCTURE.md](STRUCTURE.md).