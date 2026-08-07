import os
from pathlib import Path

TOKEN        = os.environ.get("BOT_TOKEN", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
BASE_DIR     = Path("downloads")
BASE_DIR.mkdir(exist_ok=True)
COOKIES_TT = Path(__file__).parent.parent / "cookies.txt"
COOKIES_IG = Path(__file__).parent.parent / "cookies_ig.txt"
COOKIES_FB = Path(__file__).parent.parent / "cookiesFB.txt"
LIMITE_MB  = 2000

TIKWM_API_URL     = os.environ.get("TIKWM_API_URL", "https://www.tikwm.com/api/")
BOT_API_BASE_URL  = os.environ.get("BOT_API_BASE_URL", "https://multi-api-production.up.railway.app/bot")
IG_SESSION        = os.environ.get("IG_SESSION", "ig_session")
GROQ_MODEL        = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_TEMPERATURE  = float(os.environ.get("GROQ_TEMPERATURE", "0.3"))
GROQ_MAX_TOKENS   = int(os.environ.get("GROQ_MAX_TOKENS", "500"))

RE_PATTERNS = {
    'tiktok':    r'https?://(?:www\.|vm\.|vt\.)?tiktok\.com/[^\s]+',
    'instagram': r'https?://(?:www\.)?instagram\.com/(?:p|reels?|tv|stories)/[^\s]+',
    'facebook':  r'https?://(?:www\.|m\.|web\.|fb\.)(?:facebook\.com|watch)/[^\s]+|https?://www\.facebook\.com/share/[^\s]+',
}
