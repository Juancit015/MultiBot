# Changelog

Todas las entradas son fechadas y verificadas contra el estado actual del repositorio.

## [2026-08-09]

### Added

- `README.md` regenerado desde cero (perfil técnico): descripción, características, Stack con versiones/rangos exactos de `requirements.txt`, bloque de instalación numerado 1-6 (requisitos previos por OS, clone con URL pública, venv, `.env`, dependencias, ejecución), comandos de ejecución y Docker, tabla de variables de entorno desde `.env.example`/`bot/config.py`, comandos de tests y tabla de troubleshooting con los mensajes de error exactos del programa (fail-fast de `BOT_TOKEN`/`GROQ_API_KEY`).
- `STRUCTURE.md` creado: mapa del repositorio con árbol comentado y tabla "Dónde se edita cada cosa" (handlers, services, utils, mocks y fixtures de tests).
- `CHANGELOG.md` creado con formato release-style fechado.

### Fixed

- URL de `git clone` documentada como pública (`https://github.com/Juancit015/MultiBot.git`) para que coincida con el remote real `git@github.com:Juancit015/MultiBot.git` (SSH) — clonable sin clave SSH.