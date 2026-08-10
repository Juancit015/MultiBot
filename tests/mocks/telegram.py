"""Mocks de Telegram para la suite de tests (sin red, sin bot real)."""
import asyncio


class FakeMessage:
    def __init__(self, text=None, message_id=7):
        self.text = text
        self.message_id = message_id
        self.replies = []
        self.edits = []
        self.deletions = 0

    async def reply_text(self, text, **kw):
        self.replies.append(text)
        return self

    async def reply_video(self, f, **kw):
        self.replies.append(f"VIDEO:{kw.get('caption', '-')}")

    async def reply_audio(self, f, **kw):
        self.replies.append("AUDIO:" + str(kw.get('title', '')))

    async def reply_photo(self, *a, **k):
        self.replies.append("PHOTO")

    async def reply_media_group(self, items, **k):
        self.replies.append(f"MEDIAGROUP:{len(items)}")

    async def edit_text(self, text):
        self.edits.append(text)

    async def delete(self):
        self.deletions += 1


class FakeUpdate:
    def __init__(self, text=None):
        self.message = FakeMessage(text) if text is not None else None
        self.effective_chat = type("C", (), {"id": 1})()

    def __getattr__(self, n):
        return None


class FakeContext:
    def __init__(self, args=None):
        self.args = args or []
        self.bot = FakeBot()


class FakeBot:
    async def send_video(self, chat_id=None, video=None, **kw):
        return None

    async def send_audio(self, chat_id=None, audio=None, **kw):
        return None