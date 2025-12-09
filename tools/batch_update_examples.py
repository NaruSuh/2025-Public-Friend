"""
Batch vocabulary example updater using AI.

This script iterates through vocabulary entries and generates contextual
example sentences using the OpenAI API.

Usage:
    export OPENAI_API_KEY=sk-...
    python3 tools/batch_update_examples.py
"""

import argparse
import os
import json
import sys
import logging
from typing import List, Dict, Optional

# CRIT-001 FIX: Correct module import path to slava_talk/modules
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(_CURRENT_DIR, '..', 'slava_talk')))

from modules.ai_example_generator import generate_contextual_example

# CRIT-002 FIX: Correct data file path to slava_talk/data
DEFAULT_DATA_FILE = os.path.join(_CURRENT_DIR, '..', 'slava_talk', 'data', 'vocabulary.json')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_existing_vocab(data_file: str) -> List[Dict]:
    """Loads the current vocabulary from the JSON file."""
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"Vocabulary file not found: {data_file}")
        return []
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in vocabulary file: {e}")
        return []


def save_updated_vocab(vocabulary: List[Dict], data_file: str) -> None:
    """Saves the updated vocabulary back to the JSON file."""
    try:
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(vocabulary, f, ensure_ascii=False, indent=4)
        logging.info(f"Successfully saved {len(vocabulary)} items to {data_file}")
    except IOError as e:
        logging.error(f"Error saving vocabulary file: {e}")

def run_batch_update(data_file: str, api_key: Optional[str] = None) -> None:
    """
    Iterates through the vocabulary and updates examples using the AI generator.

    Args:
        data_file: Path to the vocabulary JSON file.
        api_key: Optional OpenAI API key. If not provided, uses env variable.
    """
    logging.info("Starting batch update for example sentences...")

    existing_vocab = load_existing_vocab(data_file)
    if not existing_vocab:
        logging.warning("No vocabulary to update.")
        return

    updated_vocab = []
    total_words = len(existing_vocab)
    success_count = 0
    fail_count = 0

    for i, item in enumerate(existing_vocab):
        word_ukr = item.get("ukrainian", "(unknown)")
        logging.info(f"[{i+1}/{total_words}] Processing: '{word_ukr}'...")

        # Generate new examples using the AI module (with API key support)
        new_examples = generate_contextual_example(item, api_key=api_key)

        if new_examples and all(k in new_examples for k in ["example_sentence_ukr", "example_sentence_eng", "example_sentence_kor"]):
            # Update the item with the new examples
            item["example_sentence_ukr"] = new_examples["example_sentence_ukr"]
            item["example_sentence_eng"] = new_examples["example_sentence_eng"]
            item["example_sentence_kor"] = new_examples["example_sentence_kor"]
            logging.info(f"  -> Done.")
            success_count += 1
        else:
            logging.warning(f"  -> Failed. Keeping existing example.")
            fail_count += 1

        updated_vocab.append(item)

    # Save the entire updated list back to the file
    save_updated_vocab(updated_vocab, data_file)
    logging.info(f"Batch update finished. Success: {success_count}, Failed: {fail_count}")


def main() -> None:
    """CRIT-003 FIX: CLI entry point with proper argument parsing."""
    parser = argparse.ArgumentParser(
        description="Batch update vocabulary examples using OpenAI API",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--data-file",
        default=DEFAULT_DATA_FILE,
        help=f"Path to vocabulary JSON file (default: {DEFAULT_DATA_FILE})"
    )
    parser.add_argument(
        "--api-key",
        help="OpenAI API key (default: uses OPENAI_API_KEY environment variable)"
    )
    args = parser.parse_args()

    # Resolve API key
    api_key = args.api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        logging.error("No API key provided. Set OPENAI_API_KEY environment variable or use --api-key.")
        sys.exit(1)

    run_batch_update(args.data_file, api_key)


if __name__ == "__main__":
    main()
