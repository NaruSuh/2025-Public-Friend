
import os
import json
from typing import Dict, Optional

import streamlit as st
from openai import OpenAI, OpenAIError

# This function is designed to be called from a batch script or another module.
# It uses Streamlit's secrets management for the API key.

def generate_contextual_example(vocab_item: Dict) -> Optional[Dict]:
    """
    Generates a contextual example sentence for a given vocabulary item using OpenAI API.

    Args:
        vocab_item: A dictionary representing a single vocabulary word,
                    e.g., {"ukrainian": "аудит", "english": "Audit", "topic": "Supply Chain"}

    Returns:
        A dictionary with "example_sentence_ukr" and "example_sentence_eng", or None if an error occurs.
    """
    try:
        # Securely fetch the API key from Streamlit's secrets
        api_key = st.secrets["OPENAI_API_KEY"]
        client = OpenAI(api_key=api_key)
    except (KeyError, FileNotFoundError):
        st.error("OpenAI API key not found in Streamlit Secrets. Please configure it.")
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
