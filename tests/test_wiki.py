"""T4b/T5a/T5b + test nuevo: /wiki con el cliente Groq simulado (sin API real)."""
import pytest
from bot.services.groq import GroqAPIError

from tests.mocks.groq import FakeClient
from tests.mocks.telegram import FakeContext, FakeUpdate

EXPECTED = "RESPUESTA TEST"


async def _run_wiki(update_text, args):
    from bot.handlers.wiki import cmd_wiki
    update, ctx = FakeUpdate(update_text), FakeContext(args)
    await cmd_wiki(update, ctx)
    return update


@pytest.fixture
def wiki_online(monkeypatch):
    """Parchea is_available y cliente Groq con fakes; devuelve el cliente."""
    import bot.handlers.wiki as wiki
    from bot.services import groq

    client = FakeClient([])
    monkeypatch.setattr(groq, "_client", client)
    monkeypatch.setattr(wiki, "is_available", lambda: True)
    return client


async def test_T4b_wiki_mock_parametros_correctos(wiki_online):
    update = await _run_wiki("/wiki que es linux", ["que", "es", "linux"])
    assert EXPECTED in update.message.edits[-1]
    call = wiki_online.calls[0]
    assert call["model"] == "llama-3.3-70b-versatile"
    assert call["max_completion_tokens"] == 500
    assert call["temperature"] == 0.3
    assert call["messages"][-1]["content"] == "que es linux"


async def test_T5a_wiki_quota_muestra_mensaje_30s(monkeypatch):
    import bot.handlers.wiki as wiki
    from bot.services import groq
    monkeypatch.setattr(groq, "_client", FakeClient([], error=Exception("429 quota exceeded")))
    monkeypatch.setattr(wiki, "is_available", lambda: True)
    update = await _run_wiki("/wiki x", ["x"])
    assert "Demasiadas consultas" in update.message.edits[-1]


async def test_T5b_wiki_error_api_mensaje_generico(monkeypatch):
    import bot.handlers.wiki as wiki
    monkeypatch.setattr(wiki, "is_available", lambda: True)

    async def fake_ask(consulta):
        raise GroqAPIError("boom")

    monkeypatch.setattr(wiki, "ask_groq", fake_ask)
    update = await _run_wiki("/wiki x", ["x"])
    assert "No se pudo procesar" in update.message.edits[-1]


async def test_wiki_servicio_no_disponible(monkeypatch):
    """Test nuevo: sin credenciales el servicio responde 'no disponible'."""
    import bot.handlers.wiki as wiki
    monkeypatch.setattr(wiki, "is_available", lambda: False)
    update = await _run_wiki("/wiki x", ["x"])
    assert "no disponible" in update.message.replies[-1]