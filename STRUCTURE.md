# Estructura del repositorio — MultiBot

Mapa técnico de MultiBot para mantenimiento y depuración. El README describe el proyecto; aquí se documenta dónde vive cada cosa.

```
multibot.py                # Entry point: valida BOT_TOKEN/GROQ_API_KEY y arranca
                           # Flask (healthcheck, puerto 7860) + long polling del bot
bot/
  config.py                # Todas las variables de entorno con sus defaults,
                           # regex de plataformas (RE_PATTERNS) y LIMITE_MB = 2000
  handlers/
    media.py               # Dispatcher principal: enruta links y "find <cancion>"
    tiktok.py              # Slideshows TikTok (/photo/): TikWM + música
    instagram.py           # Carruseles Instagram /p/: Instaloader + sesión
    generic.py             # Pipeline de video genérico: yt-dlp, audio, envío
    soundcloud.py          # "find <cancion>": búsqueda scsearch1 + audio
    wiki.py                # Comando /wiki: orquesta a groq
  services/
    ytdlp.py               # make_opts por modo/plataforma + download_with_retry
    tikwm.py               # API TikWM: slides, fallback de video, ensure_tiktok_audio
    ffmpeg.py              # video_has_audio / merge_audio_into_video / extract_audio_from_video
    groq.py                # Cliente Groq (/wiki), errores de quota/API
    net.py                 # fetch_bytes y resolución de short URLs (requests en hilo)
  utils/
    messaging.py           # safe_edit / safe_delete (sin explotar si expira el mensaje)
    text.py                # get_link, limpiar_url, convertir_url_facebook, build_title, fmt_num
tests/                     # Suite pytest (27 tests), red externa bloqueada
  mocks/                   # Fakes de telegram, tikwm, ytdlp, instaloader, groq
  conftest.py              # Fixtures: BASE_DIR aislado, medios reales vía FFmpeg
downloads/                 # Directorio temporal de descargas (gitignored)
```

## Dónde se edita cada cosa

| Qué quieres cambiar | Dónde |
| --- | --- |
| Mensaje de bienvenida (/start) | `multibot.py` → `start()` |
| Regex de detección de plataformas | `bot/config.py` → `RE_PATTERNS` |
| Límite de tamaño de envío | `bot/config.py` → `LIMITE_MB` |
| Variables de entorno / defaults | `bot/config.py` (mirror en `.env.example`) |
| Comportamiento de descarga (formato, reintentos) | `bot/services/ytdlp.py` → `make_opts` |
| Fallbacks de TikTok | `bot/services/tikwm.py` |
| Fusión/extracción de audio | `bot/services/ffmpeg.py` |
| Prompt y modelo de /wiki | `bot/services/groq.py` (SYSTEM_PROMPT y `GROQ_*` envs) |
| Mensajes de error al usuario | `bot/handlers/media.py` → `ERROR_RECUPERACION` |

## Assets y credenciales (no versionados)

- `cookies.txt`, `cookies_ig.txt`, `cookiesFB.txt`: cookies para yt-dlp (TikTok/Instagram/Facebook). Excluidas por `.gitignore` y `.dockerignore`.
- `ig_session`: sesión de Instaloader para carruseles de Instagram (`IG_SESSION`).
- `downloads/`: archivos temporales por descarga (carpeta UUID por mensaje, borrada al terminar).

Todos estos archivos se crean o colocan localmente; el bot los referencia solo si existen.