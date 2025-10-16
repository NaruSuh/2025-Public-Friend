import json
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import yaml

try:
    import streamlit as st  # type: ignore
except ImportError:  # pragma: no cover - CLI usage
    st = None

VOCAB_FILE = Path(__file__).resolve().parent.parent / "data" / "vocabulary.json"

DEFAULT_ENTRY = {
    "ukrainian": "",
    "pronunciation": "",
    "korean": "",
    "english": "",
    "topics": [],
    "source": "",
    "example_sentence_ukr": "",
    "example_sentence_eng": "",
    "notes": "",
    "level": "",
    "created_at": "",
}


def _normalize_topics(value) -> List[str]:
    if not value:
        return []
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def normalize_entry(entry: Dict) -> Dict:
    """Ensure all vocabulary entries follow the same schema."""
    normalized = DEFAULT_ENTRY.copy()
    normalized.update(entry or {})
    if normalized.get("source_doc") and not normalized.get("source"):
        normalized["source"] = normalized["source_doc"]
    normalized["topics"] = _normalize_topics(normalized.get("topics"))
    normalized["created_at"] = normalized.get("created_at") or datetime.utcnow().isoformat()
    # Ensure string conversion and trim whitespace
    for key, value in normalized.items():
        if key == "topics":
            continue
        if value is None:
            normalized[key] = ""
        elif isinstance(value, str):
            normalized[key] = value.strip()
        else:
            normalized[key] = value
    return normalized


def _read_vocab() -> List[Dict]:
    """Read vocabulary entries from disk without caching."""
    if not VOCAB_FILE.exists():
        return []

    try:
        raw_text = VOCAB_FILE.read_text(encoding="utf-8")
    except OSError:
        return []

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        return []

    if not isinstance(data, list):
        return []

    return [normalize_entry(item) for item in data]


def _clear_cached_vocab() -> None:
    """Clear any cached vocabulary state."""
    clear_fn = getattr(load_vocab, "clear", None)
    if callable(clear_fn):
        clear_fn()
        return
    cache_clear_fn = getattr(load_vocab, "cache_clear", None)
    if callable(cache_clear_fn):
        cache_clear_fn()
        return
    cached_fn = globals().get("_load_vocab_cached")
    cache_clear_fn = getattr(cached_fn, "cache_clear", None)
    if callable(cache_clear_fn):
        cache_clear_fn()


if st:

    @st.cache_data(show_spinner=False)  # type: ignore[arg-type]
    def load_vocab() -> List[Dict]:
        """Load vocabulary, cached within a Streamlit session."""
        return _read_vocab()

else:

    @lru_cache(maxsize=1)
    def _load_vocab_cached() -> Tuple[Dict, ...]:
        return tuple(_read_vocab())

    def load_vocab() -> List[Dict]:
        """Load vocabulary with simple process-wide caching."""
        return list(_load_vocab_cached())


def save_vocab(entries: Iterable[Dict]) -> None:
    """Persist vocabulary entries back to the JSON file."""
    normalized = [normalize_entry(item) for item in entries]
    VOCAB_FILE.parent.mkdir(parents=True, exist_ok=True)
    VOCAB_FILE.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
    _clear_cached_vocab()


def merge_vocab(
    existing: Iterable[Dict],
    new_entries: Iterable[Dict],
    *,
    dedupe_key: Tuple[str, ...] = ("ukrainian", "english"),
) -> List[Dict]:
    """Merge vocabulary lists while deduplicating on selected keys."""
    index: Dict[Tuple, Dict] = {}

    def key_for(item: Dict) -> Tuple:
        return tuple(item.get(field, "").lower() for field in dedupe_key)

    for item in existing:
        normalized = normalize_entry(item)
        index[key_for(normalized)] = normalized

    for item in new_entries:
        normalized = normalize_entry(item)
        key = key_for(normalized)
        if key in index:
            # Merge topics and notes without losing existing intelligence
            combined_topics = sorted(set(index[key].get("topics", []) + normalized.get("topics", [])))
            index[key].update({k: v for k, v in normalized.items() if v})
            index[key]["topics"] = combined_topics
        else:
            index[key] = normalized

    merged = list(index.values())
    merged.sort(key=lambda item: item.get("ukrainian", ""))
    return merged


def export_to_yaml(entries: Iterable[Dict]) -> str:
    """Convert vocabulary entries to a YAML string."""
    payload = {"generated_at": datetime.utcnow().isoformat(), "entries": [normalize_entry(e) for e in entries]}
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)


def parse_yaml(content: str) -> List[Dict]:
    """Parse a YAML payload and return normalized entries."""
    data = yaml.safe_load(content)
    if not data:
        return []

    if isinstance(data, dict) and "entries" in data:
        candidates = data["entries"]
    elif isinstance(data, list):
        candidates = data
    else:
        return []

    return [normalize_entry(item) for item in candidates if isinstance(item, dict)]


def get_topics(entries: Iterable[Dict]) -> List[str]:
    """Return a sorted list of unique topics."""
    topics = set()
    for entry in entries:
        for topic in entry.get("topics", []):
            topics.add(topic)
    return sorted(topics)


def filter_vocab(
    entries: Iterable[Dict],
    *,
    search: Optional[str] = None,
    topics: Optional[List[str]] = None,
    source: Optional[str] = None,
) -> List[Dict]:
    """Filter vocabulary entries by search term, topics, and source."""
    search = (search or "").strip().lower()
    topics = topics or []
    source = (source or "").strip().lower()

    filtered: List[Dict] = []
    for entry in entries:
        text_blob = " ".join(
            [
                entry.get("ukrainian", ""),
                entry.get("pronunciation", ""),
                entry.get("korean", ""),
                entry.get("english", ""),
                entry.get("example_sentence_ukr", ""),
                entry.get("example_sentence_eng", ""),
                entry.get("notes", ""),
            ]
        ).lower()

        matches_search = not search or search in text_blob
        matches_topics = not topics or any(topic in entry.get("topics", []) for topic in topics)
        matches_source = not source or source in entry.get("source", "").lower()

        if matches_search and matches_topics and matches_source:
            filtered.append(entry)

    return filtered
