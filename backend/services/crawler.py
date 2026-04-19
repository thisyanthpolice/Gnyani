"""
Website Crawler
================
Crawls a website up to a configurable depth, extracts clean text content.

Uses:
  - requests + BeautifulSoup for static pages (fast, default)
  - Playwright as fallback when JS-rendered content is detected

Output:
  [{"url": "...", "title": "...", "content": "..."}]
"""

import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from collections import deque
from typing import List, Dict, Optional

from backend.config import settings
from backend.utils.helpers import (
    normalize_url,
    is_same_domain,
    make_absolute_url,
    clean_text,
    is_valid_url,
    should_skip_url,
)

logger = logging.getLogger(__name__)

# Tags to remove — navigation, boilerplate, scripts, styles
REMOVE_TAGS = [
    "nav", "footer", "header", "aside",
    "script", "style", "noscript",
    "iframe", "form", "svg", "button",
]

# Minimum text length to consider a page useful
MIN_CONTENT_LENGTH = 50


def _get_robots_parser(base_url: str) -> Optional[RobotFileParser]:
    """Load and parse robots.txt for the domain."""
    try:
        parsed = urlparse(base_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        return rp
    except Exception:
        logger.warning(f"Could not read robots.txt for {base_url}")
        return None


def _can_fetch(rp: Optional[RobotFileParser], url: str) -> bool:
    """Check if URL is allowed by robots.txt."""
    if rp is None:
        return True  # If we can't read robots.txt, allow
    return rp.can_fetch("*", url)


def _extract_content_bs4(html: str, url: str) -> Dict:
    """Parse HTML and extract clean text content using BeautifulSoup."""
    soup = BeautifulSoup(html, "html.parser")

    # Extract title
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    # Remove unwanted tags
    for tag_name in REMOVE_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    # Extract text from body (or whole doc if no body)
    body = soup.find("body")
    if body:
        text = body.get_text(separator=" ")
    else:
        text = soup.get_text(separator=" ")

    text = clean_text(text)

    return {"url": url, "title": title, "content": text}


def _extract_links(html: str, base_url: str) -> List[str]:
    """Extract all internal links from HTML."""
    soup = BeautifulSoup(html, "html.parser")
    links = set()

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"].strip()

        # Skip anchors, javascript, mailto
        if href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue

        absolute = make_absolute_url(href, base_url)

        if not is_valid_url(absolute):
            continue
        if not is_same_domain(absolute, base_url):
            continue
        if should_skip_url(absolute):
            continue

        links.add(normalize_url(absolute))

    return list(links)


def _fetch_page_static(url: str, timeout: int = 15) -> Optional[str]:
    """Fetch a page using requests (for static content)."""
    try:
        headers = {
            "User-Agent": "RAGChatBot/1.0 (Educational crawler)",
            "Accept": "text/html,application/xhtml+xml",
        }
        resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()

        content_type = resp.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            return None

        return resp.text
    except Exception as e:
        logger.warning(f"Static fetch failed for {url}: {e}")
        return None


def _is_js_heavy(html: str) -> bool:
    """Heuristic: detect if page relies heavily on JavaScript rendering."""
    soup = BeautifulSoup(html, "html.parser")
    body = soup.find("body")
    if not body:
        return False

    body_text = clean_text(body.get_text(separator=" "))

    # If body has very little text but lots of script tags → JS-heavy
    script_count = len(soup.find_all("script"))
    if len(body_text) < 100 and script_count > 3:
        return True

    # Check for common SPA indicators
    root_div = soup.find("div", {"id": "root"}) or soup.find("div", {"id": "app"})
    if root_div and len(clean_text(root_div.get_text())) < 50:
        return True

    return False


def _fetch_page_playwright(url: str) -> Optional[str]:
    """Fetch a page using Playwright (for JS-rendered content)."""
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=30000)
            html = page.content()
            browser.close()
            return html
    except ImportError:
        logger.warning("Playwright not installed — skipping JS rendering")
        return None
    except Exception as e:
        logger.warning(f"Playwright fetch failed for {url}: {e}")
        return None


def crawl_website(
    base_url: str,
    max_depth: int = None,
    max_pages: int = None,
) -> List[Dict]:
    """
    Crawl a website starting from base_url.

    Args:
        base_url:  The starting URL to crawl
        max_depth: Maximum link-follow depth (default from config)
        max_pages: Maximum pages to crawl (default from config)

    Returns:
        List of dicts: [{"url": "...", "title": "...", "content": "..."}]
    """
    if max_depth is None:
        max_depth = settings.MAX_CRAWL_DEPTH
    if max_pages is None:
        max_pages = settings.MAX_PAGES

    base_url = normalize_url(base_url)
    logger.info(f"Starting crawl: {base_url} (depth={max_depth}, max={max_pages})")

    # Load robots.txt
    rp = _get_robots_parser(base_url)

    visited = set()
    results = []

    # BFS queue: (url, depth)
    queue = deque([(base_url, 0)])

    while queue and len(results) < max_pages:
        url, depth = queue.popleft()

        if url in visited:
            continue
        visited.add(url)

        # Check robots.txt
        if not _can_fetch(rp, url):
            logger.info(f"Blocked by robots.txt: {url}")
            continue

        logger.info(f"Crawling [{depth}]: {url}")

        # Fetch page
        html = _fetch_page_static(url)
        if html is None:
            continue

        # Check if JS-heavy → try Playwright
        if _is_js_heavy(html):
            logger.info(f"JS-heavy page detected, trying Playwright: {url}")
            pw_html = _fetch_page_playwright(url)
            if pw_html:
                html = pw_html

        # Extract content
        page_data = _extract_content_bs4(html, url)

        # Skip pages with too little content
        if len(page_data["content"]) < MIN_CONTENT_LENGTH:
            logger.info(f"Skipping low-content page: {url}")
        else:
            results.append(page_data)
            logger.info(f"Extracted {len(page_data['content'])} chars from {url}")

        # Discover links (only if not at max depth)
        if depth < max_depth:
            links = _extract_links(html, url)
            for link in links:
                if link not in visited:
                    queue.append((link, depth + 1))

    logger.info(f"Crawl complete: {len(results)} pages extracted")
    return results
