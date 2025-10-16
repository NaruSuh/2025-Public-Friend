from __future__ import annotations

import json
import logging
import re
import threading
from dataclasses import dataclass
from html import escape as html_escape
from pathlib import Path
from typing import Any, Dict, List, Tuple

from bs4 import BeautifulSoup, NavigableString
from filelock import FileLock, Timeout
from markdown import markdown
import bleach

APP_DIR = Path(__file__).resolve().parent
BASE_DIR = APP_DIR / "Educare"
DATA_DIR = APP_DIR / "data"
GLOSSARY_PATH = DATA_DIR / "glossary.json"
VOCAB_PATH = DATA_DIR / "vocabulary.json"
LOCK_TIMEOUT_SECONDS = 5

MARKDOWN_EXTENSIONS = [
    "extra",
    "tables",
    "fenced_code",
    "codehilite",
    "toc",
]


@dataclass
class ContentNode:
    name: str
    path: Path
    title: str


logger = logging.getLogger(__name__)

# Global cache for JSON data to handle lock timeouts
_json_cache: Dict[Path, Any] = {}
_cache_lock = threading.Lock()  # Thread-safe cache access

ALLOWED_TAGS = [
    "a",
    "blockquote",
    "br",
    "code",
    "div",
    "em",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "img",
    "li",
    "ol",
    "p",
    "pre",
    "span",
    "strong",
    "table",
    "tbody",
    "td",
    "th",
    "thead",
    "tr",
    "ul",
]

ALLOWED_ATTRS = {
    "*": {"class"},
    "a": {"href", "title", "target", "rel"},
    "img": {"alt", "src", "title"},
    "span": {"class", "data-term", "data-tooltip"},
}


def sanitize_html(html_content: str) -> str:
    """Remove unsafe tags/attributes while keeping glossary highlights intact."""

    return bleach.clean(
        html_content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        strip=True,
    )


def _get_lock(path: Path) -> FileLock:
    lock_path = path.with_suffix(path.suffix + ".lock")
    return FileLock(str(lock_path), timeout=LOCK_TIMEOUT_SECONDS)


def _ensure_json_file(path: Path, default_text: str) -> None:
    if not path.exists():
        path.write_text(default_text, encoding="utf-8")


def _load_json_unlocked(path: Path, default: Any) -> Any:
    """Load JSON without acquiring file lock (caller already holds lock)."""
    _ensure_json_file(path, json.dumps(default, ensure_ascii=False))
    try:
        with path.open(encoding="utf-8") as fp:
            data = json.load(fp)
    except json.JSONDecodeError:
        logger.warning("Failed to parse JSON from %s; resetting to default", path)
        path.write_text(json.dumps(default, ensure_ascii=False, indent=2), encoding="utf-8")
        data = default

    with _cache_lock:
        _json_cache[path] = data
    return data


def _load_json(path: Path, default: Any) -> Any:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    lock = _get_lock(path)
    try:
        with lock:
            return _load_json_unlocked(path, default)
    except Timeout:
        logger.error("Timed out trying to acquire lock for %s", path)
        with _cache_lock:
            cached = _json_cache.get(path)
        if cached is not None:
            logger.info("Returning cached data for %s", path)
            return cached
        return default


def _atomic_write_json(path: Path, data: Any) -> None:
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)
    temp_path.replace(path)


def load_glossary() -> Dict[str, Dict[str, str]]:
    raw: Dict[str, Dict[str, str]] = _load_json(GLOSSARY_PATH, {})
    return {term.lower(): value for term, value in raw.items()}


def load_vocabulary() -> List[Dict[str, str]]:
    entries = _load_json(VOCAB_PATH, [])
    if isinstance(entries, list):
        return entries
    logger.warning("Vocabulary file %s contained non-list data; resetting", VOCAB_PATH)
    save_vocabulary([])
    return []


def save_vocabulary(entries: List[Dict[str, str]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    lock = _get_lock(VOCAB_PATH)
    try:
        with lock:
            _atomic_write_json(VOCAB_PATH, entries)
            with _cache_lock:  # Update cache on successful save
                _json_cache[VOCAB_PATH] = entries
    except Timeout:
        logger.error("Timed out trying to save vocabulary to %s", VOCAB_PATH)
        # Save to cache as fallback to prevent data loss
        with _cache_lock:
            _json_cache[VOCAB_PATH] = entries
        raise TimeoutError(f"Failed to save vocabulary: lock acquisition timeout for {VOCAB_PATH}")


def iter_markdown_files() -> List[Path]:
    if not BASE_DIR.exists():
        return []

    markdown_files: List[Path] = []
    for path in sorted(BASE_DIR.rglob("*.md")):
        if APP_DIR in path.parents:
            continue
        markdown_files.append(path)
    return markdown_files


def build_content_index() -> Dict[str, dict]:
    index: Dict[str, dict] = {}
    for path in iter_markdown_files():
        parts = path.relative_to(BASE_DIR).parts
        cursor = index
        for part in parts[:-1]:
            cursor = cursor.setdefault(part, {})
        cursor.setdefault("__files__", []).append(path)
    return index


def extract_title(markdown_text: str, fallback: str) -> str:
    for line in markdown_text.splitlines():
        if line.strip().startswith("#"):
            return line.lstrip("# ")
    return fallback


def load_markdown_content(path: Path) -> Tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    title = extract_title(text, path.stem)
    return text, title


def markdown_to_html(md_text: str) -> str:
    return markdown(md_text, extensions=MARKDOWN_EXTENSIONS)


def highlight_terms(html_text: str, glossary: Dict[str, Dict[str, str]]) -> Tuple[str, List[str]]:
    if not glossary:
        return html_text, []

    soup = BeautifulSoup(html_text, "html.parser")
    found_terms: set[str] = set()

    normalized_glossary = {term.lower(): value for term, value in glossary.items()}
    sorted_terms = sorted(normalized_glossary.keys(), key=len, reverse=True)
    if not sorted_terms:
        return html_text, []
    pattern_source = "|".join(re.escape(term) for term in sorted_terms)
    use_combined_pattern = len(pattern_source) <= 32000

    if use_combined_pattern:
        combined_pattern = re.compile(
            rf"(?<![\w-])({pattern_source})(?![\w-])",
            re.IGNORECASE,
        )
    else:
        logger.warning(
            "Combined regex pattern too large (%d chars) for %d terms. Falling back to per-term highlighting.",
            len(pattern_source), len(sorted_terms)
        )
        compiled_patterns = {
            term: re.compile(rf"(?<![\w-])({re.escape(term)})(?![\w-])", re.IGNORECASE)
            for term in sorted_terms
        }

    def wrap_text(node: NavigableString) -> None:
        parent = node.parent
        if parent.name in {"code", "pre", "style", "script"}:
            return
        text = str(node)

        def replacement(match: re.Match[str]) -> str:
            matched_text = match.group(0)
            term_key = match.group(0).lower()
            entry = normalized_glossary.get(term_key, {})
            tooltip = entry.get("short") or entry.get("long") or ""
            safe_tooltip = html_escape(tooltip, quote=True)
            safe_term = html_escape(term_key, quote=True)
            safe_text = html_escape(matched_text, quote=False)
            found_terms.add(term_key)
            return (
                f"<span class=\"gloss-term\" data-term=\"{safe_term}\" "
                f"data-tooltip=\"{safe_tooltip}\">{safe_text}</span>"
            )

        if use_combined_pattern:
            new_text = combined_pattern.sub(replacement, text)
        else:
            new_text = text
            for pattern in compiled_patterns.values():
                # pattern.sub() already checks for matches, no need for separate search()
                new_text = pattern.sub(replacement, new_text)

        if new_text != text:
            fragment = BeautifulSoup(new_text, "html.parser")
            if fragment.body:
                replacement_nodes = [child for child in fragment.body.contents]
            else:
                replacement_nodes = [child for child in fragment.contents]

            if replacement_nodes:
                node.replace_with(*replacement_nodes)
            else:
                node.replace_with(new_text)

    text_nodes = soup.find_all(string=True)
    for node in text_nodes:
        wrap_text(node)

    return str(soup), sorted(found_terms)


def ensure_future_ready_extensions() -> Dict[str, str]:
    """Placeholder configuration for future parsers (PDF, images, etc.)."""
    return {
        "markdown": "Built-in pipeline",
        "pdf": "Pending implementation – plug PDF parser here",
        "image": "Pending implementation – OCR/vision module hook",
    }


def ensure_relative_path(path: Path) -> str:
    return str(path.relative_to(BASE_DIR))


def remove_vocabulary_term(term: str) -> List[Dict[str, str]]:
    """Remove a term from vocabulary with proper transaction handling."""
    lock = _get_lock(VOCAB_PATH)
    with lock:
        entries = _load_json_unlocked(VOCAB_PATH, [])
        if not isinstance(entries, list):
            entries = []
        filtered = [item for item in entries if item.get("term") != term]
        _atomic_write_json(VOCAB_PATH, filtered)
        with _cache_lock:
            _json_cache[VOCAB_PATH] = filtered
    return filtered


def upsert_vocabulary_term(term: str, definition: str) -> List[Dict[str, str]]:
    """Add or update a term in vocabulary with proper transaction handling."""
    lock = _get_lock(VOCAB_PATH)
    with lock:
        entries = _load_json_unlocked(VOCAB_PATH, [])
        if not isinstance(entries, list):
            entries = []
        existing = next((item for item in entries if item.get("term") == term), None)
        if existing:
            existing["definition"] = definition
        else:
            entries.append({"term": term, "definition": definition})
        _atomic_write_json(VOCAB_PATH, entries)
        with _cache_lock:
            _json_cache[VOCAB_PATH] = entries
    return entries


def detect_terms_in_markdown(md_text: str, glossary: Dict[str, Dict[str, str]]) -> List[str]:
    lowered = md_text.lower()
    hits = [term for term in glossary.keys() if term in lowered]
    return sorted(hits)
