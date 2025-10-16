import json
import os

# Get the absolute path of the directory where this script is located
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Construct the absolute path to the vocabulary.json file
VOCAB_FILE = os.path.join(_CURRENT_DIR, '..', 'data', 'vocabulary.json')

def load_vocab():
    """
    Loads vocabulary from the JSON file.

    Returns:
        list: A list of vocabulary dictionaries.
        Returns an empty list if the file is not found or is invalid.
    """
    try:
        with open(VOCAB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []
