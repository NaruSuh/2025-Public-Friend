"""
Backwards compatible re-export of vocabulary helpers.
Prefer importing directly from `modules.vocab_manager`.
"""

from typing import List, Dict

try:
    import streamlit as st  # type: ignore
except ImportError:  # pragma: no cover - CLI usage
    st = None

from .vocab_manager import (
    export_to_yaml,
    filter_vocab,
    load_vocab as _load_vocab_internal,
    merge_vocab,
    normalize_entry,
    parse_yaml,
    save_vocab,
)


if st:

    @st.cache_data(show_spinner=False)  # type: ignore[arg-type]
    def load_vocab() -> List[Dict]:
        """Streamlit-aware cached loader for backwards compatibility."""
        return _load_vocab_internal()

else:

    def load_vocab() -> List[Dict]:
        """Plain loader when Streamlit is unavailable."""
        return _load_vocab_internal()


__all__ = [
    "export_to_yaml",
    "filter_vocab",
    "load_vocab",
    "merge_vocab",
    "normalize_entry",
    "parse_yaml",
    "save_vocab",
]
