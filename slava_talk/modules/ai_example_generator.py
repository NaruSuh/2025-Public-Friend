
import os
import json
import logging
from typing import Dict, Optional

import streamlit as st
from openai import OpenAI, OpenAIError

logger = logging.getLogger(__name__)

# This function is designed to be called from a batch script or another module.
# It uses Streamlit's secrets management for the API key with environment variable fallback.


def _get_api_key() -> Optional[str]:
    """CRIT-001 FIX: Standardized API key retrieval with proper fallback."""
    # Try Streamlit secrets first (for web app context)
    try:
        return st.secrets.get("OPENAI_API_KEY")
    except (FileNotFoundError, AttributeError):
        pass

    # Fall back to environment variable (for CLI/batch script context)
    return os.getenv("OPENAI_API_KEY")


def generate_contextual_example(vocab_item: Dict, api_key: Optional[str] = None) -> Optional[Dict]:
    """
    Generates a contextual example sentence for a given vocabulary item using OpenAI API.

    Args:
        vocab_item: A dictionary representing a single vocabulary word,
                    e.g., {"ukrainian": "аудит", "english": "Audit", "topic": "Supply Chain"}
        api_key: Optional API key. If not provided, will be fetched from secrets/env.

    Returns:
        A dictionary with "example_sentence_ukr" and "example_sentence_eng", or None if an error occurs.
    """
    # CRIT-001 FIX: Allow API key to be passed as parameter or fetched safely
    resolved_api_key = api_key or _get_api_key()

    if not resolved_api_key:
        error_msg = "OpenAI API key not found. Configure OPENAI_API_KEY in Streamlit Secrets or environment variable."
        logger.error(error_msg)
        try:
            st.error(error_msg)
        except Exception:
            pass  # Not in Streamlit context
        return None

    try:
        client = OpenAI(api_key=resolved_api_key)
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")
        return None

    word_ukr = vocab_item.get("ukrainian")
    word_eng = vocab_item.get("english")
    topic = vocab_item.get("topic", "general context")

    # Advanced prompt engineering for realistic, professional sentences
    prompt = f"""
    You are a senior advisor at the Ukrainian Ministry of Defence. 
    Your task is to create a trio of realistic example sentences (one in Ukrainian, one in English, and one in Korean) 
    for a South Korean intelligence agent specializing in supply chain due diligence and reconstruction.

    The sentences must use the given word in a context relevant to the provided topic. 
    The tone should be professional, formal, and reflect a real-world scenario (e.g., a meeting, a report, a field operation).

    Word (Ukrainian): {word_ukr}
    Word (English): {word_eng}
    Topic: {topic}

    Generate the output ONLY in a valid JSON format like this:
    {{
      "example_sentence_ukr": "...",
      "example_sentence_eng": "...",
      "example_sentence_kor": "..."
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that provides responses in perfect JSON format."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            response_format={"type": "json_object"}
        )
        
        # Extract the JSON content from the response
        json_response = json.loads(response.choices[0].message.content)
        return json_response

    except OpenAIError as e:
        print(f"Error generating example for '{word_ukr}': {e}")
        return None
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error parsing JSON response for '{word_ukr}': {e}")
        return None
