"""T6, T6b, T7, T7b: utilidades de texto (get_link, limpiar_url, FB, build_title)."""
from bot.utils.text import build_title, convertir_url_facebook, get_link, limpiar_url

_CASOS_GET_LINK = [
    ("https://www.tiktok.com/@user/video/7123456789012345678", "tiktok"),
    ("https://vm.tiktok.com/ABC123/", "tiktok"),
    ("https://www.instagram.com/p/CxYz/", "instagram"),
    ("https://www.instagram.com/reels/CxYz/", "instagram"),
    ("https://instagram.com/stories/user/123/", "instagram"),
    ("https://www.facebook.com/share/v/ABC123/", "facebook"),
    ("https://m.facebook.com/watch?v=123", "facebook"),
    ("https://fb.watch/xyzw/", "facebook"),
    ("https://www.youtube.com/watch?v=x", None),
    ("hola esto no es un enlace", None),
]


def test_T6_get_link_detecta_plataformas():
    for url, esperado in _CASOS_GET_LINK:
        plat, _u = get_link(url)
        assert plat == esperado, f"get_link({url}) = {plat}, esperado {esperado}"


def test_T6_get_link_devuelve_url_saneada():
    _plat, url = get_link("https://www.tiktok.com/@user/video/7123456789012345678")
    assert url.startswith("https://www.tiktok.com/@")


def test_T6b_limpiar_url_casos_reales():
    assert limpiar_url("https://instagram.com///reel/123") == "https://instagram.com/reel/123"
    assert limpiar_url("https://tiktok.comabc@user/video/7") == "https://tiktok.com/@user/video/7"
    assert limpiar_url("https://facebook.com Some text") == "https://facebook.com Some text"


def test_T7_convertir_url_facebook_reel_a_watch():
    assert convertir_url_facebook("https://www.facebook.com/reel/987654321") == \
        "https://www.facebook.com/watch/?v=987654321"
    assert convertir_url_facebook("https://www.facebook.com/video/1") == \
        "https://www.facebook.com/video/1"


def test_T7b_build_title_default_y_metricas():
    assert build_title() == "Video"
    t = build_title(views=1234567, likes=890, channel="Chan")
    assert "1.2M views" in t and "890 likes" in t and "Chan" in t