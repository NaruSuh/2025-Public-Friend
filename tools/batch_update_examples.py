
import os
import json
import sys
from typing import List, Dict

# Add the project root to the Python path to allow imports from the `modules` directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.ai_example_generator import generate_contextual_example

# --- Configuration ---
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(_CURRENT_DIR, '..', 'data', 'vocabulary.json')

def load_existing_vocab() -> List[Dict]:
    """Loads the current vocabulary from the JSON file."""
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("Vocabulary file not found or is invalid. Starting fresh.")
        return []

def save_updated_vocab(vocabulary: List[Dict]):
    """Saves the updated vocabulary back to the JSON file."""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(vocabulary, f, ensure_ascii=False, indent=4)
        print(f"\nSuccessfully saved {len(vocabulary)} items to {DATA_FILE}")
    except IOError as e:
        print(f"Error saving vocabulary file: {e}")

def run_batch_update():
    """Iterates through the vocabulary and updates examples using the AI generator."""
    print("Starting batch update for example sentences...")
    
    existing_vocab = load_existing_vocab()
    if not existing_vocab:
        print("No vocabulary to update.")
        return

    updated_vocab = []
    total_words = len(existing_vocab)

    for i, item in enumerate(existing_vocab):
        word_ukr = item.get("ukrainian", "(unknown)")
        print(f"[{i+1}/{total_words}] Processing: '{word_ukr}'...", end="", flush=True)

        # Generate new examples using the AI module
        new_examples = generate_contextual_example(item)

        if new_examples and all(k in new_examples for k in ["example_sentence_ukr", "example_sentence_eng", "example_sentence_kor"]):
            # Update the item with the new examples
            item["example_sentence_ukr"] = new_examples["example_sentence_ukr"]
            item["example_sentence_eng"] = new_examples["example_sentence_eng"]
            item["example_sentence_kor"] = new_examples["example_sentence_kor"] # Add Korean example
            print(" Done.")
        else:
            print(" Failed. Keeping existing example.")
        
        updated_vocab.append(item)

    # Save the entire updated list back to the file
    save_updated_vocab(updated_vocab)
    print("Batch update process finished.")

if __name__ == "__main__":
    # Note: This script requires Streamlit's secrets handling, 
    # so it's best run in an environment where Streamlit can find the secrets file.
    # For direct execution, you might need to temporarily adapt how the API key is loaded.
    print("This script is intended to be run within a Streamlit-aware environment or adapted for direct execution.")
    # To run it, you would typically call the run_batch_update() function.
    # run_batch_update()
