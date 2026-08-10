import asyncio

from bot.config import IG_SESSION


async def carousel_sidecar(shortcode: str) -> dict | None:
    """Devuelve URLs y metadatos de un carrusel de Instagram vía Instaloader.

    None si el post no es un GraphSidecar o no tiene nodos (cae al pipeline
    de video en el handler).
    """
    import instaloader

    L = instaloader.Instaloader()
    try:
        L.load_session_from_file(IG_SESSION)
    except Exception:
        pass
    post = await asyncio.to_thread(
        lambda: instaloader.Post.from_shortcode(L.context, shortcode)
    )
    if post.typename != 'GraphSidecar':
        return None
    urls = [node.display_url for node in post.get_sidecar_nodes()]
    if not urls:
        return None
    return {
        "urls": urls,
        "likes": post.likes if hasattr(post, 'likes') else None,
        "owner": post.owner_username if hasattr(post, 'owner_username') else None,
        "caption": post.caption if post.caption else None,
    }