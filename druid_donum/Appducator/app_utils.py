from __future__ import annotations

import json
import re
from dataclasses import dataclass
from html import escape as html_escape
from pathlib import Path
from typing import Dict, List, Tuple

from bs4 import BeautifulSoup, NavigableString
from markdown import markdown

APP_DIR = Path(__file__).resolve().parent
BASE_DIR = APP_DIR / "Educare"
DATA_DIR = APP_DIR / "data"
GLOSSARY_PATH = DATA_DIR / "glossary.json"
VOCAB_PATH = DATA_DIR / "vocabulary.json"

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


def load_glossary() -> Dict[str, Dict[str, str]]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not GLOSSARY_PATH.exists():
        GLOSSARY_PATH.write_text("{}", encoding="utf-8")
    with GLOSSARY_PATH.open(encoding="utf-8") as f:
        raw = json.load(f)
    normalized = {term.lower(): value for term, value in raw.items()}
    return normalized


def load_vocabulary() -> List[Dict[str, str]]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not VOCAB_PATH.exists():
        VOCAB_PATH.write_text("[]", encoding="utf-8")
    with VOCAB_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def save_vocabulary(entries: List[Dict[str, str]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with VOCAB_PATH.open("w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


def iter_markdown_files() -> List[Path]:
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

    sorted_terms = sorted(glossary.keys(), key=len, reverse=True)
    patterns = {
        term: re.compile(rf"(?<![\w-])({re.escape(term)})(?![\w-])", re.IGNORECASE)
        for term in sorted_terms
    }

    def wrap_text(node: NavigableString) -> None:
        parent = node.parent
        if parent.name in {"code", "pre", "style", "script"}:
            return
        text = str(node)
        replaced = False
        for term, pattern in patterns.items():
            if not pattern.search(text):
                continue

            def _replacement(match: re.Match[str]) -> str:
                matched_text = match.group(0)
                found_terms.add(term)
                entry = glossary.get(term, {})
                tooltip = entry.get("short") or entry.get("long") or ""
                safe_tooltip = html_escape(tooltip, quote=True)
                safe_term = html_escape(term, quote=True)
                safe_text = html_escape(matched_text, quote=False)
                return (
                    f"<span class=\"gloss-term\" data-term=\"{safe_term}\" "
                    f"data-tooltip=\"{safe_tooltip}\">{safe_text}</span>"
                )

            text = pattern.sub(_replacement, text)
            replaced = True
        if replaced:
            new_nodes = BeautifulSoup(text, "html.parser")
            node.replace_with(new_nodes)

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
    entries = load_vocabulary()
    filtered = [item for item in entries if item.get("term") != term]
    save_vocabulary(filtered)
    return filtered


def upsert_vocabulary_term(term: str, definition: str) -> List[Dict[str, str]]:
    entries = load_vocabulary()
    existing = next((item for item in entries if item.get("term") == term), None)
    if existing:
        existing["definition"] = definition
    else:
        entries.append({"term": term, "definition": definition})
    save_vocabulary(entries)
    return entries


def detect_terms_in_markdown(md_text: str, glossary: Dict[str, Dict[str, str]]) -> List[str]:
    lowered = md_text.lower()
    hits = [term for term in glossary.keys() if term in lowered]
    return sorted(hits)
