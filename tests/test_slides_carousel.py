"""T9 slides TikTok (mock tikwm), T11/T11b/T12 carrusel de Instagram (mock instaloader)."""
import pytest
import sys

from tests.mocks.instaloader import make_instaloader_module
from tests.mocks.ytdlp import FakeYdlMeta
from tests.mocks.telegram import FakeContext, FakeUpdate


def _patch_instaloader(monkeypatch, typename, error=False, nodes=4):
    monkeypatch.setitem(sys.modules, "instaloader",
                        make_instaloader_module(typename, error=error, nodes=nodes))


async def _patch_tiktok_slides(monkeypatch, pixel):
    import bot.handlers.tiktok as tiktok_mod

    async def fake_slides(url):
        return (["https://i1", "https://i2", "https://i3"], "https://m", "Slides")

    async def fake_fb(url):
        return pixel

    monkeypatch.setattr(tiktok_mod, "tiktok_slides", fake_slides)
    monkeypatch.setattr(tiktok_mod, "fetch_bytes", fake_fb)
    monkeypatch.setattr(tiktok_mod.yt_dlp, "YoutubeDL", FakeYdlMeta)


@pytest.fixture
def carousel(monkeypatch, pixel_png):
    async def fake_fb(url):
        return pixel_png

    import bot.handlers.instagram as insta_mod
    monkeypatch.setattr(insta_mod, "fetch_bytes", fake_fb)
    return insta_mod


async def test_T9_tiktok_slideshow_media_group_y_musica(monkeypatch, pixel_png):
    from bot.handlers import media

    await _patch_tiktok_slides(monkeypatch, pixel_png)
    update, ctx = FakeUpdate("https://www.tiktok.com/@u/photo/9"), FakeContext()
    await media.handle_media(update, ctx)

    groups = [r for r in update.message.replies if r.startswith("MEDIAGROUP")]
    assert groups and groups[0] == "MEDIAGROUP:3", update.message.replies
    assert any(r.startswith("AUDIO") for r in update.message.replies)
    assert update.message.deletions == 1


async def test_T11_instagram_carrusel_4_imagenes(monkeypatch, carousel):
    from bot.handlers import media

    _patch_instaloader(monkeypatch, "GraphSidecar")
    update, ctx = FakeUpdate("https://www.instagram.com/p/CxYz/"), FakeContext()
    await media.handle_media(update, ctx)

    groups = [r for r in update.message.replies if r.startswith("MEDIAGROUP")]
    assert groups and groups[0] == "MEDIAGROUP:4", update.message.replies
    assert update.message.deletions == 1


async def test_T11b_instagram_video_simple_cae_al_pipeline(monkeypatch, carousel,
                                                            install_pipeline):
    from bot.handlers import media

    _patch_instaloader(monkeypatch, "GraphVideo")
    sent = install_pipeline(payload=b"FAKE-MP4" * 64, extract_audio=lambda p: None)
    update, ctx = FakeUpdate("https://www.instagram.com/p/Single/"), FakeContext()
    await media.handle_media(update, ctx)

    assert "video" in sent, sent
    assert "100 views" in sent["video"][1], sent["video"][1]
    assert update.message.deletions == 1


async def test_T12_instagram_carrusel_error_mensaje_amigable(monkeypatch, carousel):
    from bot.handlers import media

    _patch_instaloader(monkeypatch, "GraphSidecar", error=True)
    update, ctx = FakeUpdate("https://www.instagram.com/p/Error/"), FakeContext()
    await media.handle_media(update, ctx)

    assert "No se pudo descargar el carrusel" in update.message.edits[-1]