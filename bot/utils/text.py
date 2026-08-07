import logging
import re

from bot.config import RE_PATTERNS

logger = logging.getLogger(__name__)


def get_link(text: str):
    for platform, pattern in RE_PATTERNS.items():
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return platform, m.group(0)
    return None, None


def convertir_url_facebook(url: str) -> str:
    if '/reel/' in url:
        video_id = re.search(r'/reel/(\d+)', url)
        if video_id:
            nueva_url = f"https://www.facebook.com/watch/?v={video_id.group(1)}"
            logger.info(f"URL Facebook convertida: {url} -> {nueva_url}")
            return nueva_url
    return url


def limpiar_url(text: str) -> str:
    text = re.sub(r'(https?://\S+)', lambda m: m.group(1).replace(' ', ''), text)
    text = re.sub(r'(instagram\.com)[A-Za-z]+(reel|stories|p|tv)', r'\1/\2', text, flags=re.IGNORECASE)
    text = re.sub(r'(tiktok\.com)[A-Za-z]+(@|video|photo)', r'\1/\2', text, flags=re.IGNORECASE)
    text = re.sub(r'(facebook\.com)[A-Za-z]+(share|watch|video)', r'\1/\2', text, flags=re.IGNORECASE)
    text = re.sub(r'(\.com)/+', r'\1/', text)
    return text


def fmt_num(n):
    if not n: return None
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 1_000: return f"{n/1_000:.0f}K"
    return str(n)


def build_title(views=None, likes=None, channel=None, uploader=None, description=None, title=None):
    parts = []
    if fmt_num(views):  parts.append(f"{fmt_num(views)} views")
    if fmt_num(likes):  parts.append(f"{fmt_num(likes)} likes")
    canal = channel or uploader or ""
    if canal:           parts.append(canal)
    desc = (description or title or "")[:150]
    if desc:            parts.append(desc)
    return " | ".join(parts) if parts else "Video"
