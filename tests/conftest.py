"""Fixtures globales de la suite de tests MultiBot.

Aislamiento garantizado:
- BASE_DIR redirigido a tmp_path (cero residuos en downloads/ del repo).
- Red externa real bloqueada (requests.post de tikwm revienta si algo escapa).
- Medios de video/audio generados con ffmpeg en tmp (sin binarios versionados).
"""
import base64
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bot.services.ffmpeg import video_has_audio  # noqa: E402

FFMPEG_OK = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))
skip_if_no_ffmpeg = pytest.mark.skipif(not FFMPEG_OK, reason="requiere ffmpeg/ffprobe")

_PNG1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)

DEFAULT_META = {
    "view_count": 100, "like_count": 50, "channel": "Chan", "uploader": "U",
    "description": "desc", "duration": 30, "title": "TituloYT",
}


def _ffmpeg(args):
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error"] + args,
                       capture_output=True, timeout=90)
    assert r.returncode == 0, r.stderr.decode()[:300]


# ── Fixtures básicos ─────────────────────────────────────────────────────────

@pytest.fixture
def pixel_png():
    """PNG 1x1 válido para imágenes simuladas (carrusel/slides)."""
    return _PNG1


@pytest.fixture(autouse=True)
def isolated_base(monkeypatch, tmp_path):
    """Redirige BASE_DIR de todos los módulos que lo importan a una carpeta temporal."""
    import bot.config
    import bot.handlers.media
    import bot.handlers.soundcloud
    base = tmp_path / "downloads"
    base.mkdir()
    monkeypatch.setattr(bot.config, "BASE_DIR", base)
    monkeypatch.setattr(bot.handlers.media, "BASE_DIR", base)
    monkeypatch.setattr(bot.handlers.soundcloud, "BASE_DIR", base)
    return base


@pytest.fixture(autouse=True)
def no_live_requests(monkeypatch):
    """Guarda anti-red: si un test olvida un mock y llama a tikwm o net real, revienta."""
    import bot.services.net
    import bot.services.tikwm

    def _boom(*a, **k):
        raise AssertionError("I/O externa real (requests) no permitida en tests")

    monkeypatch.setattr(bot.services.tikwm.requests, "post", _boom)
    monkeypatch.setattr(bot.services.net.requests, "get", _boom)
    monkeypatch.setattr(bot.services.net.requests, "head", _boom)


@pytest.fixture(autouse=True)
def no_real_resolve_short_url(monkeypatch):
    """resolve_short_url aislado: devuelve la URL sin cambios (equivalente al
    fallback sin red) para que ningún test dependa de red real ni latencia."""
    import bot.handlers.media

    async def _resolve(url: str) -> str:
        return url

    monkeypatch.setattr(bot.handlers.media, "resolve_short_url", _resolve)


@pytest.fixture
def media_fx(ffmpeg_binaries, tmp_path_factory):
    """Videos (con y sin audio) y MP3 reales generados con ffmpeg en tmp."""
    tmp = tmp_path_factory.mktemp("media")
    va = tmp / "va.mp4"
    vn = tmp / "vn.mp4"
    mp3 = tmp / "a.mp3"
    _ffmpeg(["-f", "lavfi", "-i", "testsrc=size=128x96:rate=10",
             "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=44100",
             "-t", "0.5", "-c:v", "libx264", "-preset", "ultrafast",
             "-c:a", "aac", str(va)])
    _ffmpeg(["-f", "lavfi", "-i", "testsrc=size=128x96:rate=10", "-t", "0.5",
             "-c:v", "libx264", "-preset", "ultrafast", str(vn)])
    _ffmpeg(["-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", "0.3",
             "-q:a", "9", str(mp3)])
    return {"video_audio": va, "video_mute": vn, "mp3": mp3}


@pytest.fixture
def ffmpeg_binaries():
    if not FFMPEG_OK:
        pytest.skip("ffmpeg/ffprobe no disponibles en este entorno")
    return shutil.which("ffmpeg"), shutil.which("ffprobe")


# ── Fixtures del pipeline de video ──────────────────────────────────────────

@pytest.fixture
def pipeline_sinks():
    """Captura envíos simulados (reply_video/reply_audio) y el estado de audio."""
    sent = {}

    async def cap_video(update, context, video_path, title, reply_id, timeout_s):
        sent["video"] = (str(video_path), title)
        p = Path(str(video_path))
        sent["envio_has_audio"] = bool(p.exists() and video_has_audio(p))

    async def cap_audio(update, context, audio_path, title, reply_id):
        sent["audio"] = (str(audio_path), title)

    return sent, cap_video, cap_audio


@pytest.fixture
def install_pipeline(monkeypatch, pipeline_sinks):
    """Factory que instala el pipeline simulado (descarga fake + envíos fake)."""
    sent, cap_video, cap_audio = pipeline_sinks

    def _install(payload=b"FAKE-MP4", meta=None, extract_audio=None, merge_audio=None,
                 limite_mb=None):
        import bot.handlers.generic as generic

        async def downloader(url, opts):
            (opts["folder"] / "video.mp4").write_bytes(payload)
            return meta if meta is not None else dict(DEFAULT_META)

        monkeypatch.setattr(generic, "download_with_retry", downloader)
        monkeypatch.setattr(generic, "make_opts",
                            lambda folder, mode="video", platform=None: {"folder": folder})
        monkeypatch.setattr(generic, "send_video_fallback", cap_video)
        monkeypatch.setattr(generic, "send_audio_fallback", cap_audio)
        monkeypatch.setattr(generic, "ensure_tiktok_audio", _async_noop)
        if extract_audio is not None:
            monkeypatch.setattr(generic, "extract_audio_from_video", extract_audio)
        if merge_audio is not None:
            monkeypatch.setattr(generic, "merge_audio_into_video", merge_audio)
        if limite_mb is not None:
            monkeypatch.setattr(generic, "LIMITE_MB", limite_mb)
        return sent

    return _install


async def _async_noop(*a, **k):
    return None