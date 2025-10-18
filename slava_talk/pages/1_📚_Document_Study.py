from typing import List

import streamlit as st

from modules.ai_client import AIClientError, generate_lesson_scaffolding
from modules.data_loader import export_to_yaml, filter_vocab, load_vocab
from modules.vocab_manager import get_topics
from modules.ui_components import apply_custom_css, render_vocab_card, render_hero_section, render_ai_lesson

st.set_page_config(page_title="Document Study - SlavaTalk", page_icon="📚", layout="wide")
apply_custom_css()


def set_topic_filter(*, topics: List[str]) -> None:
    """Update the global topic filter selection."""
    st.session_state.doc_selected_topics = list(topics)


vocabulary = load_vocab()

if not vocabulary:
    st.error("Vocabulary data could not be loaded. Please verify `data/vocabulary.json`.")
    st.stop()

st.sidebar.header("🔧 설정")

# TTS Settings
st.sidebar.subheader("🔊 음성 재생 옵션")
tts_method = st.sidebar.radio(
    "TTS 방식",
    ["브라우저 내장 TTS", "Google TTS (st.audio)"],
    help="브라우저 TTS는 빠르지만 음질이 낮고, Google TTS는 느리지만 자연스럽습니다"
)
st.sidebar.caption("💡 단어 카드에서는 '발음 듣기' 버튼을 클릭하여 재생하세요")

# Store in session state
st.session_state.tts_method = tts_method

st.sidebar.markdown("---")
st.sidebar.header("🔍 Filter")
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

st.success(f"✅ {len(filtered_vocab)}개 단어 로드 완료!")

# AI Lesson generation at the top (collapsible)
with st.expander("🤖 AI로 맞춤 레슨 생성 (선택사항)", expanded=False):
    st.caption("단어를 선택하고 AI가 플래시카드, 드릴, 미션 브리핑을 생성합니다.")

    selection_ids = st.multiselect(
        "레슨에 포함할 단어 선택 (최대 12개)",
        options=[f"{item['ukrainian']} :: {item.get('english', '')}" for item in filtered_vocab],
        max_selections=12,
    )

    if st.button("🚀 AI 레슨 생성", disabled=not selection_ids):
        subset = [
            item
            for item in filtered_vocab
            if f"{item['ukrainian']} :: {item.get('english', '')}" in selection_ids
        ]
        with st.spinner("AI가 레슨을 만드는 중..."):
            try:
                lesson = generate_lesson_scaffolding(subset, proficiency="intermediate")
            except AIClientError as exc:
                st.error(f"❌ OpenAI API 오류: {exc}")
            else:
                st.markdown("### 📖 생성된 레슨")
                render_ai_lesson(lesson)

st.markdown("---")
st.markdown("### 📚 단어 카드")

for idx, item in enumerate(filtered_vocab):
    render_vocab_card(
        item,
        index=idx,
        tts_method=st.session_state.tts_method,
        auto_play=False
    )
