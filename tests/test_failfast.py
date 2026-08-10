"""T1/T2: fail-fast de configuracion (_validar_config) en subprocesos aislados."""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SNIPPET = "import multibot; multibot._validar_config()"


def _env_sin_credenciales():
    return {k: v for k, v in os.environ.items()
            if k not in ("BOT_TOKEN", "GROQ_API_KEY")}


def test_T1_validar_config_aborta_sin_bot_token():
    r = subprocess.run([sys.executable, "-c", SNIPPET],
                       capture_output=True, env=_env_sin_credenciales(),
                       text=True, timeout=60, cwd=ROOT)
    assert r.returncode != 0
    assert "BOT_TOKEN" in (r.stdout + r.stderr)


def test_T2_validar_config_pasa_con_credenciales():
    env = {**_env_sin_credenciales(), "BOT_TOKEN": "123:fake", "GROQ_API_KEY": "gsk_fake"}
    r = subprocess.run([sys.executable, "-c", SNIPPET],
                       capture_output=True, env=env, text=True, timeout=60, cwd=ROOT)
    assert r.returncode == 0, r.stderr