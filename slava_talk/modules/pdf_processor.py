
import os
import json
import fitz  # PyMuPDF
import re

# --- Configuration ---
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
REFERENCE_DIR = os.path.join(_CURRENT_DIR, '..', 'reference')
DATA_FILE = os.path.join(_CURRENT_DIR, '..', 'data', 'vocabulary.json')

# Pre-defined keywords relevant to the user's mission
# (Ukrainian, Pronunciation, Korean, English)
KEYWORDS = [
    ("відновлення", "vidnovlennya", "복구, 재건", "recovery, reconstruction"),
    ("принципи", "pryntsypy", "원칙", "principles"),
    ("декларація", "deklaratsiya", "선언", "declaration"),
    ("сталий", "stalyy", "지속가능한", "sustainable"),
    ("інвестиції", "investytsiyi", "투자", "investments"),
    ("безпека", "bezpeka", "안보, 안전", "security, safety"),
    ("уряд", "uryad", "정부", "government"),
    ("суверенітет", "suverenitet", "주권", "sovereignty"),
    ("інфраструктура", "infrastruktura", "인프라", "infrastructure"),
    ("відповідальність", "vidpovidalnist", "책임", "responsibility"),
    ("співробітництво", "spivrobitnytstvo", "협력", "cooperation"),
    ("економічний", "ekonomichnyy", "경제의", "economic"),
    ("реформа", "reforma", "개혁", "reform"),
    ("суспільство", "suspilstvo", "사회", "society"),
    ("права людини", "prava lyudyny", "인권", "human rights")
]

def extract_text_from_pdf(pdf_path):
    """Extracts all text from a given PDF file."""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
        return ""

def find_example_sentences(text, keyword):
    """Finds the first sentence containing the keyword."""
    # A simple sentence tokenizer
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|!)\s', text)
    for sentence in sentences:
        # Case-insensitive search
        if keyword.lower() in sentence.lower():
            return sentence.strip()
    return None

def process_all_pdfs():
    """Processes all PDFs in the reference directory and creates a vocabulary file."""
    print("Starting PDF processing...")
    final_vocab = []
    processed_words = set()

    pdf_files = [f for f in os.listdir(REFERENCE_DIR) if f.endswith('.pdf')]

    for pdf_file in pdf_files:
        print(f"Processing document: {pdf_file}")
        pdf_path = os.path.join(REFERENCE_DIR, pdf_file)
        full_text = extract_text_from_pdf(pdf_path)

        if not full_text:
            continue

        for ukr, pron, kor, eng in KEYWORDS:
            if ukr in processed_words:
                continue # Avoid duplicate words

            example_sent = find_example_sentences(full_text, ukr)
            
            if example_sent:
                final_vocab.append({
                    "ukrainian": ukr,
                    "pronunciation": pron,
                    "korean": kor,
                    "english": eng,
                    "source_doc": pdf_file,
                    "example_sentence_ukr": example_sent,
                    "example_sentence_eng": "(Translation not available for auto-extracted sentence)" # Placeholder
                })
                processed_words.add(ukr)

    if not final_vocab:
        print("No keywords found in any of the documents. Vocabulary file not updated.")
        return

    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(final_vocab, f, ensure_ascii=False, indent=4)
        print(f"Successfully processed {len(final_vocab)} vocabulary items.")
        print(f"Vocabulary file updated: {DATA_FILE}")
    except Exception as e:
        print(f"Error writing to JSON file: {e}")

if __name__ == '__main__':
    process_all_pdfs()
