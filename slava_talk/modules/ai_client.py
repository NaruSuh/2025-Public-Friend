import json
import os
from functools import lru_cache
from typing import Dict, List, Optional

from openai import OpenAI

try:
    import streamlit as st  # type: ignore
except ImportError:  # Fallback for CLI usage outside Streamlit
    st = None  # pragma: no cover


DEFAULT_MODEL = "gpt-4o-mini"
TUTOR_MODEL = "gpt-4o-mini"


class AIClientError(RuntimeError):
    """Raised when the AI client cannot complete a request."""


def _resolve_api_key() -> str:
    """Resolve the OpenAI API key from Streamlit secrets or environment variables."""
    key: Optional[str] = None

    if st and hasattr(st, "secrets"):
        # Support both top-level and [openai] section in Streamlit secrets
        key = st.secrets.get("OPENAI_API_KEY")  # type: ignore[attr-defined]
        if not key:
            try:
                section = st.secrets.get("openai")  # type: ignore[attr-defined]
                if isinstance(section, dict):
                    key = section.get("api_key")
            except Exception:
                pass

    if not key:
        key = os.getenv("OPENAI_API_KEY")

    if not key:
        raise AIClientError(
            "OpenAI API key is missing. Add `OPENAI_API_KEY` to Streamlit secrets or environment variables."
        )

    return key


@lru_cache(maxsize=1)
def _get_client() -> OpenAI:
    """Return a cached OpenAI client instance."""
    return OpenAI(api_key=_resolve_api_key())


def _coerce_to_text(value: object) -> str:
    """Best-effort conversion of mixed content payloads into plain text."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        text_value = value.get("text") if isinstance(value.get("text"), str) else None  # type: ignore[arg-type]
        if text_value:
            return text_value
        # Recursively flatten nested content blocks if present
        return _coerce_to_text(list(value.values()))
    if isinstance(value, (list, tuple, set)):
        parts = [_coerce_to_text(item) for item in value]
        return "\n\n".join(part for part in parts if part)
    if value is None:
        return ""
    return str(value)


def _as_input_block(content: object) -> Dict[str, str]:
    """Create a compliant Responses API content block."""
    text = _coerce_to_text(content).strip()
    return {"type": "input_text", "text": text}


def _create_json_schema(schema_name: str, properties: Dict, required: Optional[List[str]] = None) -> Dict:
    """Utility helper to construct a JSON schema payload."""
    return {
        "type": "json_schema",
        "json_schema": {
            "name": schema_name,
            "schema": {
                "type": "object",
                "properties": properties,
                "required": required or [],
                "additionalProperties": False,
            },
        },
    }


def generate_vocab_from_context(
    context_text: str,
    *,
    topics: Optional[List[str]] = None,
    max_terms: int = 12,
    proficiency: str = "intermediate",
    model: str = DEFAULT_MODEL,
    source: Optional[str] = None,
) -> Dict:
    """
    Ask the ChatGPT API to extract high-signal vocabulary from supplied context text.

    Returns:
        dict: Payload with keys `entries` (list) and optional `notes`.
    """
    if not context_text.strip():
        return {"entries": [], "notes": "No context text provided."}

    client = _get_client()
    topic_summary = ", ".join(topics or [])
    schema = _create_json_schema(
        "vocabulary_batch",
        properties={
            "entries": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "ukrainian": {"type": "string"},
                        "pronunciation": {"type": "string"},
                        "korean": {"type": "string"},
                        "english": {"type": "string"},
                        "topics": {"type": "array", "items": {"type": "string"}},
                        "example_sentence_ukr": {"type": "string"},
                        "example_sentence_eng": {"type": "string"},
                        "source": {"type": "string"},
                        "notes": {"type": "string"},
                        "level": {"type": "string"},
                    },
                    "required": ["ukrainian", "english"],
                    "additionalProperties": False,
                },
            },
            "notes": {"type": "string"},
        },
        required=["entries"],
    )

    instruction = (
        "You are an instructional designer creating Ukrainian vocabulary for professionals "
        "working on diplomacy, defense, trade, and supply chain due diligence. "
        "Extract high-value Ukrainian terms with concise English and Korean glosses and "
        "provide short example sentences in Ukrainian with English paraphrases. "
        "Keep the output tightly scoped to the supplied topics and context. "
        "Estimate CEFR proficiency for each term (A2/B1/B2/C1)."
    )

    user_prompt = (
        f"Topics of interest: {topic_summary or 'general professional use'}.\n"
        f"Target proficiency: {proficiency}.\n"
        f"Limit the set to {max_terms} terms.\n"
        f"Source hint: {source or 'user supplied text chunk'}.\n"
        "Return focused lexicon items that matter for reconstruction operations.\n\n"
        "Context excerpt:\n"
        f"{context_text[:7000]}"
    )

    try:
        response = client.responses.create(
            model=model,
            input=[
                {
                    "role": "system",
                    "content": [_as_input_block(instruction)],
                },
                {
                    "role": "user",
                    "content": [_as_input_block(user_prompt)],
                },
            ],
            response_format=schema,
        )
    except Exception as exc:  # pragma: no cover - network code
        raise AIClientError(f"Failed to call OpenAI API: {exc}") from exc

    try:
        payload = json.loads(response.output_text)
    except (json.JSONDecodeError, AttributeError) as exc:
        raise AIClientError("OpenAI response could not be decoded as JSON.") from exc

    entries = payload.get("entries", [])
    if source:
        for item in entries:
            item.setdefault("source", source)
    return payload


def generate_lesson_scaffolding(
    vocab_entries: List[Dict],
    *,
    proficiency: str = "intermediate",
    focus: str = "mission_playbook",
    model: str = DEFAULT_MODEL,
) -> Dict:
    """
    Create structured micro-learning assets (flashcards, drills, checkpoints)
    leveraging the extracted vocabulary.
    """
    if not vocab_entries:
        return {}

    client = _get_client()
    schema = _create_json_schema(
        "lesson_scaffold",
        properties={
            "flashcards": {"type": "array", "items": {"type": "object"}},
            "drills": {"type": "array", "items": {"type": "object"}},
            "mission_briefs": {"type": "array", "items": {"type": "object"}},
            "recommendations": {"type": "string"},
        },
        required=["flashcards", "drills"],
    )

    prompt = (
        "You are designing a fast-cycle learning block for analysts heading to Ukraine. "
        "Using the provided vocabulary list, assemble:\n"
        "1. 3-5 flashcards with Ukrainian prompt and English/Korean cues.\n"
        "2. 2 role-play drills referencing diplomacy/defense/trade/supply chain contexts.\n"
        "3. Optional mission briefs that combine multiple terms in a short scenario.\n"
        "Ensure tasks match the stated proficiency level."
    )

    user_prompt = (
        f"Focus: {focus}\n"
        f"Learner level: {proficiency}\n"
        "Vocabulary JSON:\n"
        f"{json.dumps(vocab_entries, ensure_ascii=False)}"
    )

    try:
        response = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": [_as_input_block(prompt)]},
                {"role": "user", "content": [_as_input_block(user_prompt)]},
            ],
            response_format=schema,
        )
    except Exception as exc:  # pragma: no cover
        raise AIClientError(f"Lesson generation failed: {exc}") from exc

    try:
        return json.loads(response.output_text)
    except (json.JSONDecodeError, AttributeError) as exc:
        raise AIClientError("Lesson scaffold response was not valid JSON.") from exc


def translate_vocab_entries(entries: List[Dict], *, model: str = DEFAULT_MODEL) -> List[Dict]:
    """Translate Ukrainian terms and sample sentences into English and Korean."""
    if not entries:
        return []

    client = _get_client()
    schema = _create_json_schema(
        "translation_batch",
        properties={
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "index": {"type": "integer"},
                        "ukrainian": {"type": "string"},
                        "english": {"type": "string"},
                        "korean": {"type": "string"},
                        "example_sentence_eng": {"type": "string"},
                        "notes": {"type": "string"},
                    },
                    "required": ["index", "ukrainian"],
                    "additionalProperties": True,
                },
            }
        },
        required=["items"],
    )

    instruction = (
        "You are a bilingual translator specialising in Ukrainian operational vocabulary. "
        "For each entry, supply concise English and Korean translations and translate the sample sentence into English. "
        "Keep terminology precise for diplomacy/defense/trade contexts."
    )

    payload = {
        "items": [
            {
                "index": idx,
                "ukrainian": entry.get("ukrainian", ""),
                "context_sentence": entry.get("example_sentence_ukr", ""),
                "existing_english": entry.get("english", ""),
                "existing_korean": entry.get("korean", ""),
            }
            for idx, entry in enumerate(entries)
        ]
    }

    try:
        response = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": [_as_input_block(instruction)]},
                {
                    "role": "user",
                    "content": [_as_input_block(json.dumps(payload, ensure_ascii=False))],
                },
            ],
            response_format=schema,
        )
    except Exception as exc:  # pragma: no cover
        raise AIClientError(f"Translation request failed: {exc}") from exc

    try:
        translation_payload = json.loads(response.output_text)
    except (json.JSONDecodeError, AttributeError) as exc:
        raise AIClientError("Translation response could not be parsed as JSON.") from exc

    lookup = {
        item.get("index"): item for item in translation_payload.get("items", []) if isinstance(item, dict)
    }

    enriched: List[Dict] = []
    for idx, entry in enumerate(entries):
        enriched_entry = dict(entry)
        data = lookup.get(idx)
        if data:
            enriched_entry["english"] = data.get("english", enriched_entry.get("english", ""))
            enriched_entry["korean"] = data.get("korean", enriched_entry.get("korean", ""))
            enriched_entry["example_sentence_eng"] = data.get(
                "example_sentence_eng", enriched_entry.get("example_sentence_eng", "")
            )
            notes = data.get("notes")
            if notes:
                existing = enriched_entry.get("notes", "")
                enriched_entry["notes"] = f"{existing}\n{notes}".strip() if existing else notes
        enriched.append(enriched_entry)

    return enriched


def request_tutor_reply(
    dialogue_history: List[Dict[str, str]],
    *,
    scenario: str,
    target_language: str = "ukrainian",
    proficiency: str = "intermediate",
    model: str = TUTOR_MODEL,
) -> str:
    """
    Generate the next tutor reply in a scenario-driven conversation practice.
    """
    client = _get_client()

    system_message = (
        "You are SlavaTalk, a bilingual Ukrainian tutor focusing on operational vocabulary. "
        "Stay in Ukrainian for main dialogue, optionally providing concise English glosses in parentheses. "
        "Reinforce mission-specific terminology and keep replies under 120 words."
    )

    scenario_context = (
        f"Scenario: {scenario}. Learner proficiency roughly {proficiency}. "
        f"Target language: {target_language}. Encourage correction, provide encouragement, "
        "and maintain professional tone appropriate for diplomats and defense analysts."
    )

    messages = [
        {"role": "system", "content": [_as_input_block(system_message)]},
        {"role": "user", "content": [_as_input_block(scenario_context)]},
    ]

    for turn in dialogue_history:
        messages.append(
            {
                "role": turn.get("role", "user"),
                "content": [_as_input_block(turn.get("content", ""))],
            }
        )

    try:
        response = client.responses.create(model=model, input=messages)
    except Exception as exc:  # pragma: no cover
        raise AIClientError(f"Chat tutor failed: {exc}") from exc

    return response.output_text.strip()


def generate_quiz_feedback(
    vocab_entry: Dict,
    *,
    user_answer: str,
    is_correct: bool,
    proficiency: str = "intermediate",
    model: str = DEFAULT_MODEL,
) -> str:
    """Produce short formative feedback for quiz responses."""
    client = _get_client()

    system_message = (
        "You coach learners studying Ukrainian for professional operations. "
        "Give concise feedback (<80 words) in English with Ukrainian reinforcement."
    )

    status = "correct" if is_correct else "incorrect"
    user_prompt = (
        f"Outcome: {status}\n"
        f"Learner level: {proficiency}\n"
        f"User answer: {user_answer}\n"
        f"Vocabulary item:\n{json.dumps(vocab_entry, ensure_ascii=False)}"
    )

    try:
        response = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": [_as_input_block(system_message)]},
                {"role": "user", "content": [_as_input_block(user_prompt)]},
            ],
        )
    except Exception as exc:  # pragma: no cover
        raise AIClientError(f"Quiz feedback generation failed: {exc}") from exc

    return response.output_text.strip()
