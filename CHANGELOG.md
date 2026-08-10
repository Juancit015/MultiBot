# Changelog

Todas las entradas se basan únicamente en el historial Git actual y el working tree (53 commits, HEAD `d357259`).

## [0.2.0] — 2026-08-09 (working tree, no publicada)

### Added

- Suite de regresión pytest (**27 tests**) aislada de credenciales y APIs externas: mocks de Telegram, Groq, TikWM, Instaloader y yt-dlp en `tests/mocks/`; fixtures en `tests/conftest.py` (medios ffmpeg generados en tiempo de ejecución, redirección de `BASE_DIR` a tmp, guard anti-red).
- Marcador `ffmpeg` (5 tests) para los casos que ejercitan `bot/services/ffmpeg.py` real; se omiten si `ffmpeg`/`ffprobe` no están en el PATH.
- `pytest.ini` (`asyncio_mode = auto`, `testpaths = tests`, marker `ffmpeg`).
- `requirements-dev.txt` (`pytest>=8,<9`, `pytest-asyncio>=0.23,<1`).
- Sección de Testing en el README (comandos exactos de ejecución local y en contenedor).

### Changed

- `Dockerfile`: hardening — usuario no-root `app` (uid/gid 1001), `chown` de `/app/downloads`, `--no-install-recommends`, `pip install --no-cache-dir`, `PYTHONDONTWRITEBYTECODE=1`.
- `requirements.txt`: versionado por rangos (`python-telegram-bot>=21,<22`, `yt-dlp>=2025.1.1`, `groq>=0.10.0`, etc.).
- `multibot.py`: eliminado el auto-update de `yt-dlp` al arrancar (`pip install -U yt-dlp` vía `os.system`).
- `tests/failfast` cubre la validación fail-fast de `BOT_TOKEN`/`GROQ_API_KEY`.

### Fixed

- README corregido contra el código (SSOT): eliminada la nota de que el entry point auto-actualiza `yt-dlp` al arrancar (ya no es cierto); estado real del repositorio (cambios sin commitear posteriores a `d357259`, suite de tests presente).

## [0.1.0] — 2026-08-07 (documental inicial, no publicada)

> **Nota**: esta versión es un marcador documental inicial. No corresponde a una release oficial publicada ni a un tag en el repositorio.

**Saneamiento del historial (seguridad):**

- Eliminado el tracking de archivos de cookies y de sesión: `cookies.txt`, `cookiesFB.txt`, `cookies_ig.txt`, `cookies_yt.txt` y `ig_session`.
- Purgadas las credenciales expuestas del historial (Git filter-repo): `BOT_TOKEN` y `GROQ_API_KEY` antiguos ya no existen en ningún commit.
- Ampliado `.gitignore` con bloques para credenciales/sesiones y entornos/cachés (`cookies*.txt`, `ig_session`, `instagram_session`, `fb_session`, `*.session`, `.env`, `.env.*`, `.venv/`, caches, IDE, `*.wav`).
- Endurecida la configuración: las credenciales se leen solo desde variables de entorno, con validación fail-fast en el entry point.

**Refactorización reciente (base sobre la que se construyó el saneamiento):**

- `refactor: extraer config y utilidades a paquete bot/` (Commit 1, `baeb69a`).
- `refactor: extraer servicios yt-dlp, FFmpeg y TikWM` (Commit 2, `5ab1f81`).
- `Split handle_media into modular handlers` (Commit 3, `2509ebd`).
- `Extract Groq service and wiki handler, harden config and secrets` (Commit 4, `92938af`).
- `Remove sensitive cookie and session files from tracking and harden gitignore` (Commit 5, `d357259`).

**Documentación:**

- Añadidos `README.md` y `.env.example`.

### Funcionalidades presentes en el historial

- Soporte de descarga para TikTok, Instagram, Facebook y SoundCloud (vía `yt-dlp`, TikWM e Instaloader).
- `/wiki` con Groq (modelo, temperatura y tokens configurables).
- Detección de plataforma por regex, límite de tamaño de video, reintentos.

### Cambios pendientes / no incluidos

- Sin suite automatizada de tests (resuelto en `0.2.0`).
- Sin CI/CD configurado.
- Sin README previo ni `.env.example` (creados en esta revisión documental).