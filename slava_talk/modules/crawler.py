import re
from typing import Dict, Iterable, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup

from .ai_client import AIClientError, generate_vocab_from_context
from .vocab_manager import merge_vocab

USER_AGENT = (
    "SlavaTalkCrawler/1.0 (+https://slavatalk.local; contact: ops@slavatalk) "
    "Mozilla/5.0 (compatible; SlavaTalkAI/1.0)"
)
REQUEST_TIMEOUT = 15
MAX_CONTEXT_CHARS = 7000


class CrawlError(RuntimeError):
    """Raised when crawling fails for a source."""


def _fetch_url(url: str) -> str:
    """Download raw HTML from a URL."""
    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.text
    except requests.RequestException as exc:
        raise CrawlError(f"Failed to fetch {url}: {exc}") from exc


def _extract_text_from_html(html: str) -> str:
    """Convert HTML into a clean text blob."""
    soup = BeautifulSoup(html, "html.parser")

    # Remove script and style elements
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    text = re.sub(r"\n{2,}", "\n\n", text)
    return text.strip()


def _chunk_text(text: str, max_chars: int = MAX_CONTEXT_CHARS) -> List[str]:
    """Split large text to manageable chunks."""
    chunks: List[str] = []
    current = []
    current_len = 0
    for paragraph in text.split("\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        if current_len + len(paragraph) > max_chars and current:
            chunks.append("\n".join(current))
            current = [paragraph]
            current_len = len(paragraph)
        else:
            current.append(paragraph)
            current_len += len(paragraph)

    if current:
        chunks.append("\n".join(current))
    return chunks[:3]  # Keep API usage under control


def crawl_and_extract(
    urls: Iterable[str],
    *,
    topics: Optional[List[str]] = None,
    max_terms_per_source: int = 12,
    proficiency: str = "intermediate",
) -> Tuple[List[Dict], List[str]]:
    """
    Crawl a list of URLs and extract vocabulary with AI assistance.

    Returns:
        tuple: (entries, warnings)
    """
    aggregated: List[Dict] = []
    warnings: List[str] = []

    for url in urls:
        url = url.strip()
        if not url:
            continue

        try:
            html = _fetch_url(url)
            text_blob = _extract_text_from_html(html)
        except CrawlError as exc:
            warnings.append(str(exc))
            continue

        if not text_blob:
            warnings.append(f"No extractable text from {url}")
            continue

        chunks = _chunk_text(text_blob)
        chunk_entries: List[Dict] = []

        for chunk in chunks:
            try:
                payload = generate_vocab_from_context(
                    chunk,
                    topics=topics,
                    max_terms=max_terms_per_source,
                    proficiency=proficiency,
                    source=url,
                )
            except AIClientError as exc:
                warnings.append(f"AI extraction failed for {url}: {exc}")
                break

            entries = payload.get("entries", [])
            if not entries:
                continue
            chunk_entries = merge_vocab(chunk_entries, entries)
            if len(chunk_entries) >= max_terms_per_source:
                break

        aggregated = merge_vocab(aggregated, chunk_entries)

    return aggregated, warnings
