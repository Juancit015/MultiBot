# MultiBot

Bot de Telegram que descarga y envía videos y música de redes sociales, extrae audio de videos y responde consultas enciclopédicas breves vía Groq.

Al recibir un enlace de TikTok, Instagram o Facebook, el bot descarga el contenido con `yt-dlp` (con TikWM como fallback para TikTok y soporte de carruseles/slideshows), fusiona el audio faltante con FFmpeg cuando es necesario y lo envía de vuelta al chat. El límite de envío es de 2 GB por archivo (`LIMITE_MB = 2000` en `bot/config.py`).

## Comandos

| Entrada | Acción |
| --- | --- |
| Enlace de TikTok / Instagram / Facebook | Descarga el video o slide y lo envía al chat |
| `find <cancion>` | Busca y descarga una canción en SoundCloud |
| `/wiki <consulta>` | Respuesta corta de tipo enciclopédico con Groq |
| `/start` | Mensaje de bienvenida con las instrucciones |

## Stack

- Backend: Python 3.11 (según `Dockerfile`, imagen `python:3.11-slim`; la suite de tests también pasa en versiones posteriores)
- Bot: `python-telegram-bot` >= 21.0, < 22.0 (long polling)
- Descargas: `yt-dlp` >= 2025.1.1 + TikWM (API externa, fallback/slides TikTok) + `instaloader` >= 4.11.0 (carruseles de Instagram)
- Consultas Wiki: `groq` >= 0.10.0 (modelo por defecto `llama-3.3-70b-versatile`)
- FFmpeg/ffprobe: binarios del sistema, requeridos para extraer o fusionar audio (`bot/services/ffmpeg.py`)
- Debug: `flask` >= 3.0.0 en el puerto 7860 (healthcheck simple, sin rutas)

## Setup

Requisitos previos: Python 3.11+, Git, FFmpeg (incluye `ffprobe`) y un token de [@BotFather](https://t.me/BotFather).

```bash
# 1. Clonar
git clone https://github.com/Juancit015/MultiBot.git
cd MultiBot

# 2. Crear y activar el entorno virtual
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Configurar variables de entorno
cp .env.example .env             # rellenar BOT_TOKEN y GROQ_API_KEY

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Ejecutar
python multibot.py               # o: python3 multibot.py
```

## Run

```bash
python multibot.py
```

El bot arranca un long polling contra la API de Telegram y un `flask` mínimo en el puerto `7860` (daemon, solo como liveness). Verifica en los logs que aparezca `Bot corriendo...`; si algo falta, aborta con `Error: falta la variable de entorno BOT_TOKEN` o `... GROQ_API_KEY`.

## Environment

| Variable | Requerida | Descripción |
| --- | --- | --- |
| `BOT_TOKEN` | sí | Token del bot de Telegram (BotFather). Sin él el bot no arranca |
| `GROQ_API_KEY` | sí | API key de Groq (formato `gsk-...`). Sin ella `/wiki` no funciona y el bot no arranca |
| `TIKWM_API_URL` | no | Endpoint de la API TikWM (slides de TikTok). Default: `https://www.tikwm.com/api/` |
| `BOT_API_BASE_URL` | no | Base URL de la API de Telegram (útil tras un proxy de Telegram). Default: `https://multi-api-production.up.railway.app/bot` |
| `IG_SESSION` | no | Ruta del archivo de sesión de Instagram (Instaloader). Default: `ig_session` |
| `GROQ_MODEL` | no | Modelo Groq para `/wiki`. Default: `llama-3.3-70b-versatile` |
| `GROQ_TEMPERATURE` | no | Temperatura de respuestas Groq. Default: `0.3` |
| `GROQ_MAX_TOKENS` | no | Límite de tokens de respuesta Groq. Default: `500` |

Un `BOT_API_BASE_URL` propio solo es necesario si se monta un proxy de Telegram; en uso normal se deja el default.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

27 tests (`tests/`), con la red externa bloqueada y `BASE_DIR` redirigido a carpetas temporales. Los tests de pipeline de video/audio (`media_fx`) generan medios reales con FFmpeg y se saltan si `ffmpeg`/`ffprobe` no están en el sistema (marker `ffmpeg` en `pytest.ini`).

## Docker

```bash
docker build -t multibot .
docker run --env-file .env multibot
```

La imagen usa `python:3.11-slim`, instala FFmpeg, corre como usuario no root (`uid 1001`) y ejecuta `python3 multibot.py`. Las cookies y sesiones quedan fuera del contexto de build por `.dockerignore`.

## Estructura

```
multibot.py              # entry point: configuración, validación y long polling
bot/
  config.py              # variables de entorno, regex de plataformas, límites
  handlers/              # lógica por plataforma (media, tiktok, instagram, generic, soundcloud, wiki)
  services/              # ffmpeg, groq, net, tikwm, ytdlp
  utils/                 # messaging (safe_edit/safe_delete) y text (títulos, URLs)
tests/                   # suite pytest con mocks por servicio
downloads/               # descargas temporales (gitignored)
```

Detalle técnico completo en [STRUCTURE.md](STRUCTURE.md).

## Fallos conocidos

| Error | Causa | Solución |
| --- | --- | --- |
| `error: externally-managed-environment` al ejecutar `pip install` | Python del sistema gestionado por el SO (Debian/Ubuntu 23.04+, PEP 668) | Usar el venv del paso 2 (`pip install` dentro del venv) |
| `ModuleNotFoundError: No module named 'telegram'` al importar | Falta instalar `requirements.txt` | Activar venv e instalar dependencias antes de ejecutar |
| `Error: falta la variable de entorno BOT_TOKEN` al arrancar | `.env` no copiado o vacío | Copiar `.env.example` a `.env` y rellenarlo; exportar las variables si no se usa `--env-file` |