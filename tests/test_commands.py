"""T3 /start, T4a /wiki uso, T14 BASE_DIR y limite de tamano (sin red)."""
from tests.mocks.telegram import FakeContext, FakeUpdate


async def test_T3_start_responde_bienvenida():
    from multibot import start
    update = FakeUpdate("hola")
    ctx = FakeContext()
    await start(update, ctx)
    assert any("TikTok" in r for r in update.message.replies)


async def test_T4a_wiki_sin_args_muestra_uso(monkeypatch):
    import bot.handlers.wiki as wiki
    monkeypatch.setattr(wiki, "is_available", lambda: True)
    update, ctx = FakeUpdate("/wiki"), FakeContext()
    await wiki.cmd_wiki(update, ctx)
    assert "Uso:" in update.message.replies[-1]


async def test_T14_base_dir_y_limite(isolated_base):
    from bot.config import BASE_DIR, LIMITE_MB
    assert BASE_DIR.exists()
    assert LIMITE_MB == 2000