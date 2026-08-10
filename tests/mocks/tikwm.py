"""Fakes para TikTok vía tikwm: nunca tocan la API real."""


async def tiktok_slides_fake(images=(1, 2, 3), music="https://m", title="Slides"):
    """Devuelve una simulacion del resultado de tikwm para un slideshow."""

    async def _fake(url):
        return (["https://i1", "https://i2", "https://i3"][:len(images)],
                music if images else None, title)

    return _fake


async def tiktok_slides_empty(url):
    """Simula que tikwm no reconoce el slideshow (cae al pipeline de video)."""
    return None, None, None


async def ensure_tiktok_audio_noop(folder, url):
    """Desactiva el fallback de audio de tikwm."""
    return None