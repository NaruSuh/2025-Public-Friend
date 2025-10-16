"""
Advanced PDF processing utilities for SlavaTalk.

This module extracts candidate Ukrainian vocabulary from reference PDFs using
spaCy/NLP heuristics, enriches them with machine translations, and merges the
results into the workspace dataset.
"""

from __future__ import annotations

import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

import fitz  # PyMuPDF

try:
    import spacy
    from spacy.language import Language
except ImportError:  # pragma: no cover - optional dependency
    spacy = None
    Language = None  # type: ignore

from .ai_client import AIClientError, translate_vocab_entries
from .vocab_manager import load_vocab, merge_vocab, normalize_entry, save_vocab

LOGGER = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
REFERENCE_DIR = BASE_DIR / "reference"

CYRILLIC_PATTERN = re.compile(r"[А-ЩЬЮЯЇІЄҐа-щьюяїієґ]")
SENTENCE_SPLITTER = re.compile(r"(?<=[.!?])\s+")
WORD_PATTERN = re.compile(r"[А-ЩЬЮЯЇІЄҐа-щьюяїієґ'`-]+")

# Minimal Ukrainian stopword list to reduce noise when spaCy isn't available.
UKRAINIAN_STOPWORDS = {
    "і",
    "й",
    "та",
    "що",
    "це",
    "але",
    "для",
    "від",
    "також",
    "при",
    "який",
    "яка",
    "які",
    "буде",
    "може",
    "через",
    "після",
    "коли",
    "тому",
    "якщо",
}

CANDIDATE_POS = {"NOUN", "PROPN", "ADJ"}
MAX_SENTENCE_CHARS = 400


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract raw text from a PDF; returns empty string if parsing fails."""
    try:
        with fitz.open(pdf_path) as doc:
            return "\n".join(page.get_text().strip() for page in doc)
    except Exception as exc:  # pragma: no cover - PyMuPDF errors
        LOGGER.error("Failed to read %s: %s", pdf_path, exc)
        return ""


def _clean_sentence(value: str) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    if len(value) > MAX_SENTENCE_CHARS:
        value = value[: MAX_SENTENCE_CHARS - 1].rstrip() + "…"
    return value


def _is_valid_term(text: str) -> bool:
    text = text.strip()
    return bool(text) and len(text) > 2 and CYRILLIC_PATTERN.search(text)


def _topic_score(sentence: str, topics: Sequence[str]) -> int:
    if not topics:
        return 0
    sentence_lower = sentence.lower()
    return sum(1 for topic in topics if topic in sentence_lower)


@lru_cache(maxsize=1)
def _get_nlp() -> Optional[Language]:
    """Load a spaCy pipeline if available; fall back to None."""
    if not spacy:
        return None

    try:
        return spacy.load("xx_sent_ud_sm")
    except OSError:
        # Minimal multilingual pipeline with just a sentencizer
        nlp = spacy.blank("xx")
        if "sentencizer" not in nlp.pipe_names:
            nlp.add_pipe("sentencizer")
        return nlp


def _iter_sentences(text: str) -> Iterator[str]:
    """Yield sentences from text when spaCy is unavailable."""
    for sentence in SENTENCE_SPLITTER.split(text):
        sentence = _clean_sentence(sentence)
        if sentence:
            yield sentence


def _iter_tokens(sentence: str) -> Iterator[str]:
    for token in WORD_PATTERN.findall(sentence):
        cleaned = token.strip("-`'")
        if cleaned:
            yield cleaned


def _extract_candidates_with_spacy(
    doc,
    topics: Sequence[str],
) -> Dict[str, Dict]:
    candidates: Dict[str, Dict] = {}

    for sentence in doc.sents:
        sentence_text = _clean_sentence(sentence.text)
        if not sentence_text:
            continue

        sentence_score = _topic_score(sentence_text, topics)
        for token in sentence:
            lemma = token.lemma_.lower() if token.lemma_ not in ("", "-PRON-") else token.text.lower()
            surface = token.text.strip()

            if not _is_valid_term(surface):
                continue
            if token.pos_ and token.pos_ not in CANDIDATE_POS:
                continue
            if token.is_stop or token.like_num:
                continue

            key = lemma or surface.lower()
            entry = candidates.setdefault(
                key,
                {
                    "surface": surface,
                    "lemma": key,
                    "count": 0,
                    "sentence": sentence_text,
                    "score": 0.0,
                },
            )
            entry["count"] += 1
            if len(surface) > len(entry["surface"]):
                entry["surface"] = surface
            entry["score"] += 1 + sentence_score

        # Capture noun chunks for multi-word terms
        try:
            chunks = sentence.noun_chunks  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            chunks = ()

        for chunk in chunks:
            chunk_text = _clean_sentence(chunk.text)
            if not _is_valid_term(chunk_text):
                continue
            key = chunk_text.lower()
            entry = candidates.setdefault(
                key,
                {
                    "surface": chunk_text,
                    "lemma": key,
                    "count": 0,
                    "sentence": sentence_text,
                    "score": 0.0,
                },
            )
            entry["count"] += 1
            entry["score"] += 1 + sentence_score

    return candidates


def _extract_candidates_fallback(text: str, topics: Sequence[str]) -> Dict[str, Dict]:
    candidates: Dict[str, Dict] = {}
    for sentence in _iter_sentences(text):
        sentence_score = _topic_score(sentence.lower(), topics)
        for token in _iter_tokens(sentence):
            if not _is_valid_term(token):
                continue
            if token.lower() in UKRAINIAN_STOPWORDS:
                continue
            key = token.lower()
            entry = candidates.setdefault(
                key,
                {
                    "surface": token,
                    "lemma": key,
                    "count": 0,
                    "sentence": sentence,
                    "score": 0.0,
                },
            )
            entry["count"] += 1
            entry["score"] += 1 + sentence_score
    return candidates


def extract_candidate_terms(text: str, topics: Optional[Sequence[str]] = None) -> List[Dict]:
    """Return scored candidate vocabulary items from raw text."""
    topics = [topic.lower() for topic in topics or []]
    nlp = _get_nlp()

    if nlp:
        doc = nlp(text)
        candidates = _extract_candidates_with_spacy(doc, topics)
    else:
        candidates = _extract_candidates_fallback(text, topics)

    sorted_candidates = sorted(
        candidates.values(),
        key=lambda item: (item["score"], item["count"], len(item["surface"])),
        reverse=True,
    )
    return sorted_candidates


def _build_entries(
    candidates: Iterable[Dict],
    *,
    source: str,
    topics: Optional[Sequence[str]] = None,
    max_terms: int = 20,
) -> List[Dict]:
    topics_list = list(topics or [])
    entries: List[Dict] = []
    for candidate in candidates:
        if len(entries) >= max_terms:
            break
        entries.append(
            {
                "ukrainian": candidate["surface"],
                "english": "",
                "korean": "",
                "pronunciation": "",
                "topics": topics_list,
                "source": source,
                "example_sentence_ukr": candidate["sentence"],
                "example_sentence_eng": "",
                "notes": f"Auto-extracted from {source} (score={candidate['score']:.1f}, count={candidate['count']}).",
                "level": "",
            }
        )
    return entries


def harvest_pdf_vocabulary(
    pdf_path: Path,
    *,
    topics: Optional[Sequence[str]] = None,
    max_terms: int = 20,
    translate: bool = True,
) -> List[Dict]:
    """Convert a PDF into enriched vocabulary entries."""
    text = extract_text_from_pdf(pdf_path)
    if not text.strip():
        raise RuntimeError(f"No extractable text found in {pdf_path.name}")

    candidates = extract_candidate_terms(text, topics=topics)
    if not candidates:
        raise RuntimeError(f"No Ukrainian terms detected in {pdf_path.name}")

    entries = _build_entries(candidates, source=pdf_path.name, topics=topics, max_terms=max_terms)

    if translate:
        try:
            entries = translate_vocab_entries(entries)
        except AIClientError as exc:
            for entry in entries:
                note = entry.get("notes", "")
                note = f"{note}\nTranslation unavailable: {exc}".strip()
                entry["notes"] = note

    return [normalize_entry(entry) for entry in entries]


def process_reference_library(
    *,
    topics: Optional[Sequence[str]] = None,
    max_terms_per_doc: int = 20,
    translate: bool = True,
    update_dataset: bool = True,
) -> Tuple[List[Dict], List[str]]:
    """
    Process all PDFs in the reference directory.

    Returns:
        tuple: (new_entries, warnings)
    """
    new_entries: List[Dict] = []
    warnings: List[str] = []

    for pdf_path in sorted(REFERENCE_DIR.glob("*.pdf")):
        try:
            entries = harvest_pdf_vocabulary(
                pdf_path,
                topics=topics,
                max_terms=max_terms_per_doc,
                translate=translate,
            )
        except RuntimeError as exc:
            warnings.append(str(exc))
            continue

        new_entries = merge_vocab(new_entries, entries)

    if update_dataset and new_entries:
        merged = merge_vocab(load_vocab(), new_entries)
        save_vocab(merged)

    return new_entries, warnings


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Harvest vocabulary from reference PDFs.")
    parser.add_argument("--topics", nargs="*", default=None, help="Optional focus topics to prioritise.")
    parser.add_argument("--max-terms", type=int, default=20, help="Max terms to extract per PDF.")
    parser.add_argument("--no-translate", action="store_true", help="Skip translation step.")
    parser.add_argument("--dry-run", action="store_true", help="Do not merge into the main dataset.")
    args = parser.parse_args()

    entries, warnings = process_reference_library(
        topics=args.topics,
        max_terms_per_doc=args.max_terms,
        translate=not args.no_translate,
        update_dataset=not args.dry_run,
    )

    print(f"Extracted {len(entries)} unique terms from reference PDFs.")
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"- {warning}")
