# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.
Formato basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/).

## [Unreleased]

### Added

- README.md regenerado desde el estado real del repositorio: setup con venv del `python` del sistema (PEP 668), tabla de variables de entorno, guía Docker, suite de 27 tests y mapeo de cookies por plataforma.
- STRUCTURE.md con el mapa del repositorio y dónde se edita cada parte del bot.
- CHANGELOG.md en formato release-style.

### Fixed

- Se eliminó el requisito de "Python >= 3.10 por usar `match`": el código no contiene `match` y el mínimo real lo imponen las dependencias (`python-telegram-bot` >= 21 exige Python >= 3.8). La imagen Docker usa `python:3.11-slim` y el entorno local se probó con Python 3.14.
- Mapeo de cookies corregido contra `bot/config.py`: solo se leen `cookies.txt` (TikTok), `cookies_ig.txt` (Instagram) y `cookiesFB.txt` (Facebook). `cookies_yt.txt` existe en el repo pero el código no la referencia, así que ya no se documenta como soportada.
- URL de `git clone` alineada con `git remote -v`: el remote es SSH, así que se documenta la URL pública equivalente `https://github.com/Juancit015/MultiBot.git` (clonable sin clave SSH).