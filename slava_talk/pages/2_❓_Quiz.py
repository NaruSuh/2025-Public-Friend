import random
from typing import Dict, List

import streamlit as st

from modules.ai_client import AIClientError, generate_quiz_feedback
from modules.data_loader import filter_vocab, load_vocab
from modules.vocab_manager import get_topics

st.set_page_config(page_title="Quiz - SlavaTalk", page_icon="❓", layout="centered")

QUESTION_MODES = {
    "Recognize meaning (English)": {"type": "mc", "field": "english"},
    "Recognize meaning (Korean)": {"type": "mc", "field": "korean"},
    "Produce Ukrainian (type answer)": {"type": "text", "field": "english"},
}


def reset_quiz_state():
    st.session_state.quiz_word = None
    st.session_state.quiz_options = []
    st.session_state.quiz_score = 0
    st.session_state.quiz_questions = 0
    st.session_state.quiz_streak = 0
    st.session_state.quiz_feedback = ""
    st.session_state.quiz_history = []


def ensure_state():
    if "quiz_word" not in st.session_state:
        reset_quiz_state()
    if "quiz_pool" not in st.session_state:
        st.session_state.quiz_pool = []
    if "quiz_filters_signature" not in st.session_state:
        st.session_state.quiz_filters_signature = None


def build_question_pool(
    vocab: List[Dict],
    *,
    topics: List[str],
) -> List[Dict]:
    filtered = filter_vocab(vocab, topics=topics)
    return filtered if filtered else vocab


def generate_new_question(question_mode: str, n_options: int):
    pool = st.session_state.quiz_pool
    if not pool:
        return

    vocab_entry = random.choice(pool)
    st.session_state.quiz_word = vocab_entry
    st.session_state.quiz_feedback = ""

    if QUESTION_MODES[question_mode]["type"] == "mc":
        options = [vocab_entry]
        # Use random.sample to efficiently get unique incorrect options
        incorrect_pool = [item for item in pool if item != vocab_entry]
        num_options_to_get = min(len(incorrect_pool), n_options - 1)
        
        if num_options_to_get > 0:
            options.extend(random.sample(incorrect_pool, num_options_to_get))

        random.shuffle(options)
        st.session_state.quiz_options = options
    else:
        st.session_state.quiz_options = []


def evaluate_mc_answer(selected_text: str, mode_field: str) -> bool:
    correct = st.session_state.quiz_word.get(mode_field, "")
    return selected_text == correct


def evaluate_text_answer(user_input: str) -> bool:
    correct = st.session_state.quiz_word.get("ukrainian", "")
    return user_input.strip().lower() == correct.lower()


def record_result(is_correct: bool):
    st.session_state.quiz_questions += 1
    if is_correct:
        st.session_state.quiz_score += 1
        st.session_state.quiz_streak += 1
    else:
        st.session_state.quiz_streak = 0

    st.session_state.quiz_history.append(
        {
            "term": st.session_state.quiz_word.get("ukrainian"),
            "was_correct": is_correct,
            "mode": st.session_state.quiz_mode,
        }
    )


ensure_state()

vocabulary = load_vocab()
if not vocabulary:
    st.error("Vocabulary data could not be loaded. Cannot start quiz.")
    st.stop()

topics = get_topics(vocabulary)

st.title("❓ Adaptive Quiz")
st.caption("Rotate through recognition and production drills. Keep the streak alive like Duolingo, but mission-ready.")

with st.sidebar:
    st.header("Quiz Controls")
    with st.form("quiz_filters"):
        selected_topics = st.multiselect("Limit to topics", options=topics, default=topics)
        question_mode = st.selectbox("Exercise type", options=list(QUESTION_MODES.keys()))
        n_options = st.slider("Options per question", min_value=3, max_value=6, value=4, step=1)
        proficiency = st.selectbox("AI feedback level", options=["novice", "intermediate", "advanced"], index=1)
        apply_filters = st.form_submit_button("Apply")

    if st.button("Reset progress"):
        reset_quiz_state()
        st.rerun()

if QUESTION_MODES[question_mode]["type"] == "text":
    n_options = 0

signature = (tuple(sorted(selected_topics)), question_mode, n_options)
if apply_filters or signature != st.session_state.quiz_filters_signature:
    st.session_state.quiz_pool = build_question_pool(vocabulary, topics=selected_topics)
    st.session_state.quiz_filters_signature = signature
    st.session_state.quiz_mode = question_mode
    st.session_state.quiz_proficiency = proficiency
    generate_new_question(question_mode, max(n_options, 3) if n_options else 0)

if not st.session_state.quiz_pool:
    st.error("No vocabulary available for the selected topics.")
    st.stop()

if st.session_state.quiz_word is None:
    st.session_state.quiz_mode = question_mode
    st.session_state.quiz_proficiency = proficiency
    generate_new_question(question_mode, max(n_options, 3) if n_options else 0)

st.metric("Score", f"{st.session_state.quiz_score} / {st.session_state.quiz_questions}")
st.metric("Current Streak", st.session_state.quiz_streak)

mode_meta = QUESTION_MODES[st.session_state.quiz_mode]
target_entry = st.session_state.quiz_word

if mode_meta["type"] == "mc":
    question_text = f"What is the **{mode_meta['field']}** meaning of `{target_entry['ukrainian']}`?"
else:
    question_text = f"Type the Ukrainian term for: **{target_entry[mode_meta['field']]}**"

st.markdown(f"### {question_text}")
st.caption(f"Pronunciation: {target_entry.get('pronunciation', '—')}")

with st.form("quiz_form"):
    if mode_meta["type"] == "mc":
        choices = [opt.get(mode_meta["field"], "") for opt in st.session_state.quiz_options]
        user_choice = st.radio("Choose an answer", options=choices, index=None)
    else:
        user_choice = st.text_input("Your answer in Ukrainian")

    submitted = st.form_submit_button("Submit")

    if submitted:
        if not user_choice:
            st.warning("Submit an answer to continue.")
        else:
            if mode_meta["type"] == "mc":
                is_correct = evaluate_mc_answer(user_choice, mode_meta["field"])
            else:
                is_correct = evaluate_text_answer(user_choice)

            record_result(is_correct)

            if is_correct:
                st.success("Correct! ✅")
            else:
                expected = (
                    st.session_state.quiz_word.get(mode_meta["field"])
                    if mode_meta["type"] == "mc"
                    else st.session_state.quiz_word.get("ukrainian")
                )
                st.error(f"Not quite. The correct answer is **{expected}**.")

            pronunciation = st.session_state.quiz_word.get("pronunciation", "")
            st.info(
                f"Example: {st.session_state.quiz_word.get('example_sentence_ukr', '—')}\n"
                f"EN: {st.session_state.quiz_word.get('example_sentence_eng', '—')}\n"
                f"Pronunciation: {pronunciation}",
                icon="🇺🇦",
            )

            try:
                feedback = generate_quiz_feedback(
                    st.session_state.quiz_word,
                    user_answer=user_choice,
                    is_correct=is_correct,
                    proficiency=st.session_state.quiz_proficiency,
                )
            except AIClientError as exc:
                feedback = f"(AI feedback unavailable: {exc})"
            st.session_state.quiz_feedback = feedback

if st.session_state.quiz_feedback:
    st.caption(st.session_state.quiz_feedback)

col_next, col_skip = st.columns([1, 1])
with col_next:
    if st.button("Next ▶️"):
        generate_new_question(st.session_state.quiz_mode, max(n_options, 3) if n_options else 0)
        st.rerun()

with col_skip:
    if st.button("Skip ❌"):
        generate_new_question(st.session_state.quiz_mode, max(n_options, 3) if n_options else 0)
        st.rerun()

st.markdown("---")

if st.session_state.quiz_history:
    correct = sum(1 for item in st.session_state.quiz_history if item["was_correct"])
    total = len(st.session_state.quiz_history)
    st.write(f"Session accuracy: **{correct}/{total}**")
    miss_list = [item["term"] for item in st.session_state.quiz_history if not item["was_correct"]]
    if miss_list:
        st.markdown("Revisit these terms next:")
        st.write(", ".join(miss_list))
