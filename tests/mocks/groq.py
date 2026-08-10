"""Cliente Groq simulado: reproduce la interfaz _client.chat.completions.create."""


class FakeCompletions:
    def __init__(self, client):
        self.client = client

    def create(self, **kw):
        self.client.calls.append(kw)
        if self.client.error:
            raise self.client.error
        class C:
            content = self.client.content
        class M:
            message = C()
        class R:
            choices = [M()]
        return R()


class FakeChat:
    def __init__(self, client):
        self.completions = FakeCompletions(client)


class FakeClient:
    def __init__(self, calls, error=None, content="RESPUESTA TEST"):
        self.calls = calls
        self.error = error
        self.content = content
        self.chat = FakeChat(self)