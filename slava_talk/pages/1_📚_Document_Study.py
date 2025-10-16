from typing import List

import streamlit as st

from modules.ai_client import AIClientError, generate_lesson_scaffolding
from modules.data_loader import export_to_yaml, filter_vocab, load_vocab
from modules.vocab_manager import get_topics

st.set_page_config(page_title="Document Study - SlavaTalk", page_icon="📚", layout="wide")

st.title("📚 Document Study Hub")
st.caption("Filter curated documents, extract the terms you need, and spin up micro-lessons on demand.")

vocabulary = load_vocab()

if not vocabulary:
    st.error("Vocabulary data could not be loaded. Please verify `data/vocabulary.json`.")
    st.stop()

st.sidebar.header("Filter")
search_query = st.sidebar.text_input("Search any field")
available_topics = get_topics(vocabulary)
selected_topics: List[str] = st.sidebar.multiselect("Topics", options=available_topics)

sources = sorted({item.get("source") or item.get("source_doc", "") for item in vocabulary if item.get("source") or item.get("source_doc")})
source_options = ["All sources"] + sources
selected_source = st.sidebar.selectbox("Source document", options=source_options)

max_results = st.sidebar.slider("Max terms to display", min_value=10, max_value=200, value=80, step=10)

filtered_vocab = filter_vocab(
    vocabulary,
    search=search_query,
    topics=selected_topics,
    source=None if selected_source == "All sources" else selected_source,
)[:max_results]

st.sidebar.download_button(
    "Download filtered set (YAML)",
    data=export_to_yaml(filtered_vocab),
    file_name="slavatalk_filtered.yaml",
    mime="application/x-yaml",
)

if not filtered_vocab:
    st.warning("No vocabulary matched your filters. Adjust search terms or topics.")
    st.stop()

st.success(f"{len(filtered_vocab)} terms loaded.")

selection_ids = st.multiselect(
    "Select terms for AI-assisted micro-lesson (optional)",
    options=[f"{item['ukrainian']} :: {item.get('english', '')}" for item in filtered_vocab],
    max_selections=12,
)

if st.button("Generate micro-lesson with ChatGPT", disabled=not selection_ids):
    subset = [
        item
        for item in filtered_vocab
        if f"{item['ukrainian']} :: {item.get('english', '')}" in selection_ids
    ]
    with st.spinner("Building lesson scaffolding..."):
        try:
            lesson = generate_lesson_scaffolding(subset, proficiency="intermediate")
        except AIClientError as exc:
            st.error(f"OpenAI request failed: {exc}")
        else:
            st.markdown("### Lesson Assets")
            if lesson.get("flashcards"):
                st.markdown("#### Flashcards")
                for card in lesson["flashcards"]:
                    st.markdown(f"- **{card.get('prompt', '')}** → {card.get('answer', '')}")
            if lesson.get("drills"):
                st.markdown("#### Drills")
                for idx, drill in enumerate(lesson["drills"], start=1):
                    st.markdown(f"{idx}. {drill.get('description', '')}")
            if lesson.get("mission_briefs"):
                st.markdown("#### Mission Briefs")
                for brief in lesson["mission_briefs"]:
                    st.markdown(f"- {brief.get('summary', '')}")
            if lesson.get("recommendations"):
                st.info(lesson["recommendations"])

st.markdown("---")

for item in filtered_vocab:
    doc_source = item.get("source") or item.get("source_doc", "—")
    header = f"{item.get('ukrainian', '—')}  ({item.get('pronunciation', '—')})"
    topics_display = ", ".join(item.get("topics", [])) or "—"
    with st.expander(header):
        st.markdown(f"**English:** {item.get('english', '—')}")
        st.markdown(f"**Korean:** {item.get('korean', '—')}")
        st.markdown(f"**Topics:** {topics_display}")
        st.markdown(f"**Level:** {item.get('level', '—')}")
        st.markdown("---")
        st.markdown("**Example (UA):**")
        st.markdown(f"> {item.get('example_sentence_ukr', '—')}")
        st.markdown("**Example (EN):**")
        st.markdown(f"> {item.get('example_sentence_eng', '—')}")
        if item.get("notes"):
            st.markdown("---")
            st.markdown(f"**Notes:** {item['notes']}")
        st.caption(f"Source: {doc_source}")
