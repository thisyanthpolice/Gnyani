"""
Utility helpers — URL normalization, text cleaning, retry logic.
"""

import re
import time
import functools
from urllib.parse import urlparse, urljoin, urldefrag


def normalize_url(url: str) -> str:
    """Normalize a URL: remove fragment, trailing slash, lowercase scheme/host."""
    url, _ = urldefrag(url)  # strip #fragment
    parsed = urlparse(url)
    # Rebuild with lowercase scheme + host, strip trailing slash from path
    path = parsed.path.rstrip("/") or "/"
    normalized = f"{parsed.scheme.lower()}://{parsed.netloc.lower()}{path}"
    if parsed.query:
        normalized += f"?{parsed.query}"
    return normalized


def is_same_domain(url: str, base_url: str) -> bool:
    """Check if url belongs to the same domain as base_url."""
    return urlparse(url).netloc.lower() == urlparse(base_url).netloc.lower()


def make_absolute_url(href: str, base_url: str) -> str:
    """Convert a relative URL to absolute."""
    return urljoin(base_url, href)


def clean_text(text: str) -> str:
    """Clean extracted text — collapse whitespace, strip junk."""
    if not text:
        return ""
    # Replace multiple whitespace/newlines with single space
    text = re.sub(r"\s+", " ", text)
    # Remove zero-width chars
    text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)
    return text.strip()


def is_valid_url(url: str) -> bool:
    """Basic URL validation."""
    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception:
        return False


def should_skip_url(url: str) -> bool:
    """Skip non-content URLs (images, PDFs, assets, etc.)."""
    skip_extensions = (
        ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
        ".pdf", ".zip", ".tar", ".gz",
        ".css", ".js", ".woff", ".woff2", ".ttf", ".eot",
        ".mp3", ".mp4", ".avi", ".mov",
        ".xml", ".json", ".rss",
    )
    parsed = urlparse(url)
    return parsed.path.lower().endswith(skip_extensions)


def retry(max_retries: int = 3, delay: float = 1.0):
    """Decorator — retry a function on exception."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exc = e
                    if attempt < max_retries - 1:
                        time.sleep(delay * (attempt + 1))
            raise last_exc
        return wrapper
    return decorator
