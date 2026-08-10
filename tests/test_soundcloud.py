"""T13: busqueda SoundCloud con yt-dlp simulado (sin FFmpeg, sin red)."""
from tests.mocks.ytdlp import FakeYdlAudio
from tests.mocks.telegram import FakeContext, FakeUpdate


async def test_T13_soundcloud_find_thumb_audio_y_borrado(monkeypatch):
    import bot.handlers.soundcloud as sc_mod
    from bot.handlers import media

    monkeypatch.setattr(sc_mod.yt_dlp, "YoutubeDL", FakeYdlAudio)
    monkeypatch.setattr(sc_mod, "make_opts",
                        lambda folder, mode="audio": {"folder": str(folder)})

    update, ctx = FakeUpdate("find artista cancion"), FakeContext()
    await media.handle_media(update, ctx)

    assert "PHOTO" in update.message.replies, update.message.replies
    assert "AUDIO:Título SC" in update.message.replies, update.message.replies
    assert update.message.deletions == 1