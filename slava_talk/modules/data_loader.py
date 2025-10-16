"""
Backwards compatible re-export of vocabulary helpers.
Prefer importing directly from `modules.vocab_manager`.
"""

from .vocab_manager import (
    export_to_yaml,
    filter_vocab,
    load_vocab,
    merge_vocab,
    normalize_entry,
    parse_yaml,
    save_vocab,
)

__all__ = [
    "export_to_yaml",
    "filter_vocab",
    "load_vocab",
    "merge_vocab",
    "normalize_entry",
    "parse_yaml",
    "save_vocab",
]
