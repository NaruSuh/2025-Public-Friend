from typing import List

import streamlit as st

from modules.ai_client import AIClientError, generate_lesson_scaffolding
from modules.data_loader import export_to_yaml, filter_vocab, load_vocab
from modules.vocab_manager import get_topics

st.set_page_config(page_title="Document Study - SlavaTalk", page_icon="📚", layout="wide")


def set_topic_filter(*, topics: List[str]) -> None:
    """Update the global topic filter selection."""
    st.session_state.doc_selected_topics = list(topics)


st.title("📚 Document Study Hub")
st.caption("Filter curated documents, extract the terms you need, and spin up micro-lessons on demand.")

vocabulary = load_vocab()

if not vocabulary:
    st.error("Vocabulary data could not be loaded. Please verify `data/vocabulary.json`.")
    st.stop()

st.sidebar.header("Filter")
search_query = st.sidebar.text_input("Search any field")
available_topics = get_topics(vocabulary)

if "doc_selected_topics" not in st.session_state:
    st.session_state.doc_selected_topics = available_topics
else:
    st.session_state.doc_selected_topics = [
        topic for topic in st.session_state.doc_selected_topics if topic in available_topics
    ] or available_topics

selected_topics: List[str] = st.sidebar.multiselect(
    "Topics",
    options=available_topics,
    key="doc_selected_topics",
)
st.sidebar.button(
    "Show all topics",
    on_click=set_topic_filter,
    kwargs={"topics": list(available_topics)},
    use_container_width=True,
)

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
    with st.expander(header):
        st.markdown(f"**English:** {item.get('english', '—')}")
        st.markdown(f"**Korean:** {item.get('korean', '—')}")
        if item.get("topics"):
            st.markdown("**Topics:**")
            topic_cols = st.columns(len(item["topics"]))
            for idx, topic in enumerate(item["topics"]):
                topic_key = f"topic-btn-{item.get('ukrainian', idx)}-{topic}"
                if topic_cols[idx].button(
                    topic,
                    key=topic_key,
                    use_container_width=True,
                    on_click=set_topic_filter,
                    kwargs={"topics": [topic]},
                ):
                    pass
        else:
            st.markdown("**Topics:** —")
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
