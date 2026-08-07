import os
from pathlib import Path

TOKEN        = os.environ.get("BOT_TOKEN","***CLEARED***")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "***CLEARED***")
BASE_DIR     = Path("downloads")
BASE_DIR.mkdir(exist_ok=True)
COOKIES_TT = Path(__file__).parent.parent / "cookies.txt"
COOKIES_IG = Path(__file__).parent.parent / "cookies_ig.txt"
COOKIES_FB = Path(__file__).parent.parent / "cookiesFB.txt"
LIMITE_MB  = 2000

RE_PATTERNS = {
    'tiktok':    r'https?://(?:www\.|vm\.|vt\.)?tiktok\.com/[^\s]+',
    'instagram': r'https?://(?:www\.)?instagram\.com/(?:p|reels?|tv|stories)/[^\s]+',
    'facebook':  r'https?://(?:www\.|m\.|web\.|fb\.)(?:facebook\.com|watch)/[^\s]+|https?://www\.facebook\.com/share/[^\s]+',
}
