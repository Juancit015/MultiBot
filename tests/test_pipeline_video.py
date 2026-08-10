"""T8, T10a, T10b, T16: pipeline de video con FFmpeg real y descarga simulada."""
import pytest

from tests.conftest import skip_if_no_ffmpeg
from tests.mocks.telegram import FakeContext, FakeUpdate

pytestmark = [skip_if_no_ffmpeg, pytest.mark.ffmpeg]


async def test_T8_pipeline_tiktok_extract_merge_envio(install_pipeline, media_fx):
    from bot.handlers import media

    sent = install_pipeline(payload=media_fx["video_audio"].read_bytes())
    update, ctx = FakeUpdate("https://www.tiktok.com/@u/video/1"), FakeContext()
    await media.handle_media(update, ctx)

    assert "video" in sent, f"no se envió video: {sent}"
    vpath, title = sent["video"]
    assert title.count("100 views") == 1 and title.count("50 likes") == 1
    assert vpath.endswith("merged_video.mp4"), "no ejecutó merge de audio"
    assert sent["envio_has_audio"] is True, "video final sin audio (merge real)"
    assert "audio" in sent and sent["audio"][1] == title, sent
    assert update.message.deletions == 1, "mensaje proceso no eliminado"


async def test_T10a_tiktok_photo_fallback_video_mudo(install_pipeline, media_fx):
    """Rama: tikwm sin slides -> descarga video mudo -> extract falla -> original."""
    from bot.handlers import media

    sent = install_pipeline(payload=media_fx["video_mute"].read_bytes())
    update, ctx = FakeUpdate("https://www.tiktok.com/@u/photo/7"), FakeContext()
    await media.handle_media(update, ctx)

    vpath = sent.get("video", ("", ""))[0]
    assert vpath.endswith("video.mp4"), f"video mudo debe enviar original: {sent}"
    assert "audio" not in sent, "no debe haber audio si la extracción falló"
    assert sent.get("envio_has_audio") is False
    assert update.message.deletions == 1


async def test_T10b_tiktok_video_con_audio_merge_y_mp3(install_pipeline, media_fx):
    from bot.handlers import media

    sent = install_pipeline(payload=media_fx["video_audio"].read_bytes())
    update, ctx = FakeUpdate("https://www.tiktok.com/@u/video/7"), FakeContext()
    await media.handle_media(update, ctx)

    assert "merged_video.mp4" in sent["video"][0], sent
    assert "audio" in sent, "falta audio por separado"
    assert sent["envio_has_audio"] is True, "video enviado sin audio"
    assert update.message.deletions == 1


async def test_T16_limite_tamano_aborta_envio(install_pipeline, media_fx):
    from bot.handlers import media

    sent = install_pipeline(payload=media_fx["video_audio"].read_bytes(),
                            limite_mb=0.000001)
    update, ctx = FakeUpdate("https://www.tiktok.com/@u/video/8"), FakeContext()
    await media.handle_media(update, ctx)

    assert "video" not in sent, f"debió abortar antes de enviar: {sent}"
    assert any("demasiado grande" in e for e in update.message.edits), update.message.edits