"""Variantes 100% mock del pipeline (sin FFmpeg) + URL no soportada."""
from tests.mocks.telegram import FakeContext, FakeUpdate


def _no_extract(p):
    return None


def _no_merge(video, audio):
    return None


async def test_T10a_mock_tiktok_photo_video_mudo(install_pipeline):
    """Equivalente a T10a sin FFmpeg: extract falla simuladamente -> original."""
    from bot.handlers import media

    sent = install_pipeline(payload=b"FAKE-MP4" * 64,
                            extract_audio=_no_extract, merge_audio=_no_merge)
    update, ctx = FakeUpdate("https://www.tiktok.com/@u/photo/7"), FakeContext()
    await media.handle_media(update, ctx)

    vpath = sent.get("video", ("", ""))[0]
    assert vpath.endswith("video.mp4"), f"debe enviar original: {sent}"
    assert "audio" not in sent, "no debe haber audio si no hay MP3"
    assert update.message.deletions == 1


async def test_T16_mock_limite_tamano_aborta(install_pipeline):
    """Equivalente a T16 sin FFmpeg: el corte por tamaño ocurre antes del merge."""
    from bot.handlers import media

    sent = install_pipeline(payload=b"FAKE-MP4" * 64,
                            extract_audio=_no_extract, merge_audio=_no_merge,
                            limite_mb=0.000001)
    update, ctx = FakeUpdate("https://www.tiktok.com/@u/video/8"), FakeContext()
    await media.handle_media(update, ctx)

    assert "video" not in sent, f"debió abortar antes de enviar: {sent}"
    assert any("demasiado grande" in e for e in update.message.edits), update.message.edits


async def test_url_youtube_ignorada_sin_respuesta():
    """Test nuevo: el bot descarta silenciosamente URLs no soportadas (YouTube)."""
    from bot.handlers import media

    update, ctx = FakeUpdate("https://www.youtube.com/watch?v=x"), FakeContext()
    await media.handle_media(update, ctx)
    assert update.message.replies == []
    assert update.message.deletions == 0