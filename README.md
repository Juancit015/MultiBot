# MultiBot

Bot de Telegram que descarga y reenvía contenido multimedia de TikTok, Instagram y Facebook (videos, reels, stories, carruseles y slideshows), busca canciones en SoundCloud y responde consultas enciclopédicas con Groq (`/wiki`).

## Funciones

- **Videos:** pega un enlace de TikTok (`tiktok.com`), Instagram (`instagram.com/p|reel|tv|stories`) o Facebook (`facebook.com`, `fb.watch`) y el bot lo descarga con yt-dlp, incrusta el audio con FFmpeg y lo envía junto con su MP3. Límite de subida: 2000 MB.
- **Carruseles de Instagram:** los posts `/p/...` con varias fotos se envían como álbum (instaloader + sesión `ig_session`).
- **Slides de TikTok:** los enlaces `/photo/...` se envían como álbum con su audio (API TikWM).
- **SoundCloud:** `find <cancion>` descarga el primer resultado (`scsearch1`) como MP3 con su carátula.
- **Consultas:** `/wiki <consulta>` responde información enciclopédica vía Groq (modelo `llama-3.3-70b-versatile` por defecto).
- **Keep-alive:** al arrancar levanta, además, un servidor Flask en el puerto `7860`.

## Stack

| Componente | Versión / rango (requirements.txt) |
| --- | --- |
| Python | 3.11+ (Dockerfile: `python:3.11-slim`; probado local en 3.14) |
| python-telegram-bot | `>=21.0, <22.0` — se importa como `telegram` |
| yt-dlp | `>=2025.1.1` |
| groq | `>=0.10.0` |
| flask | `>=3.0.0` |
| requests | `>=2.31.0` |
| httpx | `>=0.27.0` |
| instaloader | `>=4.11.0` |
| ffmpeg + ffprobe | binarios del sistema (los instala el paso 1; no son paquetes pip) |

La descarga de video usa yt-dlp con salida MP4 (H.264 + AAC, máx. 720p); el audio se extrae o fusiona con FFmpeg. Todo el tráfico de subida sale por la API de Telegram (`BOT_API_BASE_URL`).

## Instalación

Secuencia completa, del clone al arranque. Ejecuta los pasos en orden. Desde el paso 3, los comandos de `python`/`pip` corresponden al intérprete del venv (ver [intérprete del venv](#intérprete-del-venv)).

### 1. Requisitos previos

Necesitas Git, Python con soporte de venv y los binarios `ffmpeg`/`ffprobe` (los requiere yt-dlp para fusionar audio y los tests).

```bash
# Debian / Ubuntu
sudo apt update && sudo apt install -y git python3 python3-venv ffmpeg
```

```bash
# Fedora / RHEL
sudo dnf install -y git python3 python3-virtualenv ffmpeg
```

```bash
# Arch Linux
sudo pacman -S --noconfirm git python python-virtualenv ffmpeg
```

```bash
# macOS (requiere Homebrew)
brew install git python ffmpeg
```

```powershell
# Windows (PowerShell)
winget install --id Git.Git -e
winget install --id Python.Python.3.12 -e
winget install --id Gyan.FFmpeg -e
```

En Windows, si `winget` no está disponible, descarga los instaladores oficiales de Python, Git y FFmpeg desde sus páginas de descarga y añade sus carpetas `bin` al `PATH`.

### 2. Clonar el repositorio

```bash
git clone https://github.com/Juancit015/MultiBot.git
cd MultiBot
```

### 3. Crear y activar el entorno virtual

```bash
# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

```powershell
# Windows (PowerShell)
python -m venv venv
venv\Scripts\Activate.ps1
```

```cmd
# Windows (CMD)
python -m venv venv
venv\Scripts\activate.bat
```

#### Intérprete del venv

Verifica que el comando `python` apunta al binario del venv:

```bash
# Linux / macOS
which python
```

```powershell
# Windows (PowerShell)
where.exe python
```

La salida debe ser una ruta dentro de `venv/` (por ejemplo `/home/usuario/MultiBot/venv/bin/python` o `venv\Scripts\python.exe`). Si muestra el intérprete del sistema, el venv no está activado. Todos los comandos de ejecución de este README corren con el venv activado y usan `python` como binario canónico.

### 4. Crear `.env` desde la plantilla

```bash
# Linux / macOS
cp .env.example .env
```

```powershell
# Windows (PowerShell)
Copy-Item .env.example .env
```

```cmd
# Windows (CMD)
copy .env.example .env
```

Edita `.env` y rellena las variables obligatorias (tabla [Variables de entorno](#variables-de-entorno)). El bot aborta al arrancar si falta alguna:

```
Error: falta la variable de entorno BOT_TOKEN
```

### 5. Instalar dependencias

```bash
pip install -r requirements.txt
```

Solo si vas a correr los tests, instala también las dependencias de desarrollo:

```bash
pip install -r requirements-dev.txt
```

### 6. Ejecutar

```bash
python multibot.py
```

Deberías ver `Bot corriendo...` en la consola y el servidor Flask escuchando en el puerto `7860`.

## Variables de entorno

Verificadas en `.env.example` y `bot/config.py`.

| Variable | Requerida | Descripción | Valor por defecto |
| --- | --- | --- | --- |
| `BOT_TOKEN` | sí | Token del bot creado con @BotFather | — (aborta si falta) |
| `GROQ_API_KEY` | sí | API key de Groq (formato `gsk-...`) | — (aborta si falta) |
| `TIKWM_API_URL` | no | Endpoint de la API TikWM (slides de TikTok y fallbacks) | `https://www.tikwm.com/api/` |
| `BOT_API_BASE_URL` | no | Base URL de la API de Telegram (útil tras un proxy) | `https://multi-api-production.up.railway.app/bot` |
| `IG_SESSION` | no | Archivo de sesión de Instaloader | `ig_session` |
| `GROQ_MODEL` | no | Modelo Groq para `/wiki` | `llama-3.3-70b-versatile` |
| `GROQ_TEMPERATURE` | no | Temperatura de las respuestas de Groq | `0.3` |
| `GROQ_MAX_TOKENS` | no | Límite de tokens de respuesta de Groq | `500` |

Nunca versiones `.env` (está en `.gitignore`); el repo solo mantiene `.env.example`.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

La suite aísla `downloads/` en una carpeta temporal y bloquea peticiones de red reales durante los tests (`tests/conftest.py`). Los tests marcados como `ffmpeg` se omiten si los binarios `ffmpeg`/`ffprobe` no están disponibles (marker declarado en `pytest.ini`).

## Docker

La imagen base `python:3.11-slim` ya incluye ffmpeg (Dockerfile). El contenedor corre como usuario `app` (uid 1001) y arranca con `python3 multibot.py`.

```bash
docker build -t multibot .
docker run --rm -e BOT_TOKEN=... -e GROQ_API_KEY=... multibot
```

## Troubleshooting

| Error | Causa | Solución |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'telegram'` | El paquete `python-telegram-bot` se importa como `telegram`; el error indica intérprete del sistema o venv sin activar | Activa el venv antes de ejecutar: `source venv/bin/activate` (o lanza directo con `venv/bin/python multibot.py`) |
| `Error: falta la variable de entorno BOT_TOKEN` | Variable obligatoria sin rellenar | Edita `.env` (paso 4) o exporta la variable antes del paso 6 |
| `Error: falta la variable de entorno GROQ_API_KEY` | Variable obligatoria sin rellenar | Edita `.env` (paso 4) o exporta la variable antes del paso 6 |
| `error: externally-managed-environment` (PEP 668) | `pip` corriendo en el intérprete del sistema, no en el venv | Crea y activa el venv (paso 3) antes de instalar dependencias |
| `ffmpeg`/`ffprobe` no encontrados | Binarios de sistema ausentes | Instálalos con el comando de tu distro/SO del paso 1 |
| Video sin audio en TikTok | yt-dlp no consiguió pista de audio | Automático: el bot usa la API TikWM como fallback (`ensure_tiktok_audio`) |

> **Estructura del repositorio:** consulta [STRUCTURE.md](STRUCTURE.md) para saber dónde se edita cada comportamiento.