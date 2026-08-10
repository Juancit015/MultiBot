# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.
Formato basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/).

## [Unreleased]

### Added

- README.md regenerado desde el estado real del repositorio: setup con venv del `python` del sistema (≥ 3.10), instalación de FFmpeg por OS, tabla de variables de entorno, guía Docker y suite de 27 tests.
- STRUCTURE.md con el mapa del repositorio y dónde se edita cada parte del bot.
- CHANGELOG.md en formato release-style.

### Fixed

- Setup de venv corregido: se usa `python -m venv .venv` en vez de `.venv` con `python3.11` (binario que solo existe dentro de la imagen Docker y falta en el host); documentado el PEP 668 como motivo del venv.
- URL de `git clone` alineada con `git remote -v`: el remote es SSH, así que se documenta la URL pública equivalente `https://github.com/Juancit015/MultiBot.git` (clonable sin clave SSH).