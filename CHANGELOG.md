# CHANGELOG

Todas las entradas de este archivo corresponden a cambios reales verificados en el estado actual del repositorio.

## [2026-08-09]

### Changed

- `requirements.txt`: añadido `python-dotenv>=1.0.0`.
- `multibot.py`: añadido `load_dotenv()` que lee `.env` automáticamente al arrancar, antes de importar `bot.config`.
- Documentación regenerada desde cero verificando el estado actual del repo (SSOT): README.md, CHANGELOG.md y STRUCTURE.md reescritos sin consultar versiones previas.
- `README.md`: instalación como secuencia numerada que arranca en el clone; etiquetas de SO (`Linux / macOS`, `Windows (PowerShell)`, `Windows (CMD)`) fuera de los bloques de código, comandos únicos copiables; binario canónico `python` del venv (verificable con `which python`); tabla de variables de entorno extraída de `bot/config.py`; tabla de troubleshooting con mensajes de error literales del programa (`BOT_TOKEN`, `GROQ_API_KEY`, `ModuleNotFoundError: No module named 'telegram'`, PEP 668, ffmpeg); documentado que `.env` se carga automáticamente al arrancar.
- `STRUCTURE.md`: mapa de arquitectura en capas (entry point, handlers, services, utils, tests y mocks) con tabla "Dónde se edita cada cosa", incluida la fila de la carga de `.env` (`multibot.py` → `load_dotenv()`).
- URL de `git clone` documentada como pública HTTPS (`https://github.com/Juancit015/MultiBot.git`) pese a que el remote configurado es SSH.