# Changelog

Todas las entradas siguen el formato [Keep a Changelog](https://keepachangelog.com/es/1.1.0/).

## 2026-08-09

### Agregado

- `README.md` regenerado desde cero: instalación completa en 6 pasos numerados que arrancan en el `git clone` (requisitos previos por SO → clone → venv → `.env` → pip → ejecución), con los comandos de cada variante por SO en bloques independientes etiquetados (`# Linux / macOS`, `# Windows (PowerShell)`, `# Windows (CMD)`) y bloque por distro para ffmpeg (Debian/Ubuntu, Fedora/RHEL, Arch, macOS, Windows).
- `README.md`: aclarado el intérprete del venv como binario canónico (`which python` debe apuntar a `venv/bin/python`) y que todos los comandos de ejecución corren con el venv activado.
- `README.md`: equivalencia `python-telegram-bot` → import `telegram` en el Stack y fila de troubleshooting para `ModuleNotFoundError: No module named 'telegram'`.
- `README.md`: tabla de variables de entorno verificada contra `.env.example` y `bot/config.py` (obligatorias `BOT_TOKEN` y `GROQ_API_KEY` con sus mensajes exactos de aborto), stack con versiones de `requirements.txt` y tabla de troubleshooting con mensajes reales del programa.
- `STRUCTURE.md` creado: mapa de la arquitectura en capas (`bot/{config,handlers,services,utils}` + `tests/mocks`) con árbol comentado, tabla "Dónde se edita cada cosa" y flujo de un mensaje.
- `CHANGELOG.md` creado con formato release-style.

### Corregido

- URL de `git clone` documentada como HTTPS pública (`https://github.com/Juancit015/MultiBot.git`) porque el remote `origin` del repo es SSH (`git@github.com:Juancit015/MultiBot.git`).