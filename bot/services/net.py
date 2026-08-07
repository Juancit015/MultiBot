import asyncio
import logging

import requests

logger = logging.getLogger(__name__)


async def fetch_bytes(url: str) -> bytes | None:
    try:
        return await asyncio.to_thread(lambda: requests.get(url, timeout=15).content)
    except Exception as e:
        logger.warning(f"fetch_bytes error: {e}")


async def resolve_short_url(url: str) -> str:
    try:
        return await asyncio.to_thread(lambda: requests.head(url, timeout=10, allow_redirects=True).url)
    except Exception as e:
        logger.warning(f"resolve_short_url error: {e}")
        return url