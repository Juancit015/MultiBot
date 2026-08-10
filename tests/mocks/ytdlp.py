"""Fakes de yt-dlp: solo metadatos, sin red ni descargas."""


class FakeYdlMeta:
    """Solo metadatos extract_info (para slideshow de TikTok)."""

    def __init__(self, *a, **k):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass

    def extract_info(self, *a, **k):
        return {"view_count": 500, "like_count": 33}


class FakeYdlAudio:
    """extract_info que escribe un stub de MP3 en el folder indicado por opts."""

    def __init__(self, opts):
        self.opts = opts

    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass

    def extract_info(self, query, download=False):
        from pathlib import Path
        (Path(self.opts["folder"]) / "cancion.mp3").write_bytes(b"ID3STUB" * 32)
        return {"title": "Título SC", "uploader": "Artist", "thumbnail": "https://thumb/x"}