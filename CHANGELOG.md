# Changelog

Todo cambio relevante (visible o de infraestructura) se registra aquí.
El formato sigue [Keep a Changelog](https://keepachangelog.com/es/1.1.0/) y este proyecto usa [Versionado Semántico](https://semver.org/lang/es/).

## [Unreleased]

### Regenerado

- README.md, CHANGELOG.md y STRUCTURE.md regenerados desde cero con la skill `repo-readme-changelog` (sin consultar el historial git). SSOT: código, requirements, Dockerfile, tests y smoke test.
- URL de clonado del README ahora es la pública `https://github.com/Juancit015/MultiBot.git` (el remote es SSH `git@github.com:Juancit015/MultiBot.git`).
- Rango de runtime documentado: Python 3.11+ (3.11 del Dockerfile y 3.14.6 verificado en el smoke test: arranque + 27 tests).
- Versiones del Stack verificadas en el venv del smoke test: python-telegram-bot 22.8, yt-dlp 2026.7.4, groq 1.6.0, Flask 3.1.3, requests 2.34.2, httpx 0.28.1, instaloader 4.15.3, python-dotenv 1.2.2.

### Agregado

- Tabla de troubleshooting con mensajes de error literales (fail-fast de `BOT_TOKEN`/`GROQ_API_KEY`, `InvalidToken`, `ModuleNotFoundError: 'telegram'`, PEP 668).
- Smoke test de arranque documentado: con token falso, el bot levanta Flask en `0.0.0.0:7860` y aborta en `getMe` — comportamiento esperado en la frontera de credenciales.
- STRUCTURE.md con arquitectura en capas y tabla "Dónde se edita cada cosa".

### Hallazgo (pendiente de decisión del mantenedor)

- El default `BOT_API_BASE_URL=https://multi-api-production.up.railway.app/bot` (`bot/config.py`) produce peticiones `.../bot<TOKEN>/getMe`, ruta que el gateway `multi-api-production.up.railway.app` no enruta (404 incluso con token válido; el gateway espera `<TOKEN>/<método>` sin `/bot`). Documentado como nota en la tabla de env vars y fila de troubleshooting. Fix sugerido: quitar el sufijo `/bot` del default (o documentar el override en `.env`). No se tocó código ni `.env.example`.

### Fixed

- Default de `BOT_API_BASE_URL` corregido en `bot/config.py` → `https://api.telegram.org/bot` (oficial, verificado). El default anterior (`…/multi-api-production.up.railway.app/bot`) rompía el arranque con 404 aun con token válido.
- Validación por smoke test del fix: `POST https://api.telegram.org/bot<TOKEN>/getMe` → `401 Unauthorized` con token falso (comportamiento esperado en frontera de credenciales; antes era 404 con URL malformada).
- **Hallazgo del loop:** el gateway `multi-api-production.up.railway.app` resultó ser incompatible con `python-telegram-bot` en ambos formatos — con `/bot` responde 404 y sin `/bot` la librería rechaza la URL (`NetworkError: InvalidURL: Invalid port 'TEST'`, el `:` del token rompe el parseo de httpx). Documentado en README y `.env.example` (el proxy debe enrutar `bot<TOKEN>/<método>`).
- `.env.example` y README actualizados: default oficial, nota del fix y filas de troubleshooting del 404 e `InvalidURL`.