# Changelog

Todas las entradas se documentan con fecha y tienen formato [Keep a Changelog](https://keepachangelog.com/).

## 2026-08-09

### Cambiado

- `python-telegram-bot` ahora se declara como `>=22.0,<23.0` en `requirements.txt`. Las versiones 21.x y anteriores son incompatibles con Python 3.12+ y fallaban al arrancar con `RuntimeError: There is no current event loop`. Arranque verificado en Python 3.11 (Dockerfile) y en Python 3.14 (host).

### Corregido

- `multibot.py` ahora llama a `load_dotenv()` antes de importar `bot/config.py`, de modo que las variables de la API (como `BOT_API_BASE_URL`, usada tras un proxy de Telegram) sí se leen del `.env` al arrancar y no solo las que ya estuvieran exportadas en el entorno.

### Documentación

- `README.md`, `CHANGELOG.md` y `STRUCTURE.md` regenerados desde cero con verificación directa contra el repositorio (runtime, dependencias, `.env.example`, entry point y errores literales).
- Documentada la secuencia de instalación completa (requisitos previos por SO, clone, venv, `.env`, dependencias, ejecución) y la tabla de troubleshooting con el error `RuntimeError: There is no current event loop` y su fix.
- Corregida la URL de clone del README a la pública `https://github.com/Juancit015/MultiBot.git` (el remote es SSH).