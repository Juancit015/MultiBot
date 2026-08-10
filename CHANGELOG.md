# Changelog

## [2026-08-09]

### Added

- `README.md`: documentación del proyecto verificada contra el repo (stack con versiones de `requirements.txt`, commandos reales de `multibot.py`, variables de entorno de `.env.example`, puerto Flask 7860, `git clone` público `https://github.com/Juancit015/MultiBot.git`, tabla de fallos conocidos).
- `STRUCTURE.md`: mapa del repositorio (`bot/`, `tests/`, `downloads/`) con ubicación real de cada pieza de lógica y credenciales no versionadas.
- `CHANGELOG.md`: registro de cambios del repositorio.

### Fixed

- Documentación regenerada desde el estado actual del repo (la anterior fue eliminada a propósito; no se recuperó del historial de Git).
- Versión de runtime documentada según el `Dockerfile` (Python 3.11) y verificado que `requirements-dev.txt` no está en `requirements.txt` (pytest instalado por separado).
- Confirmada la suite de tests: 27 pasan con `pytest` (marcador `ffmpeg` para tests que requieren binarios del sistema).