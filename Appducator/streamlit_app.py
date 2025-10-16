from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import streamlit as st

from app_utils import (
    ensure_future_ready_extensions,
    ensure_relative_path,
    highlight_terms,
    iter_markdown_files,
    load_glossary,
    load_markdown_content,
    load_vocabulary,
    markdown_to_html,
    remove_vocabulary_term,
    sanitize_html,
    upsert_vocabulary_term,
)

st.set_page_config(
    page_title="Appducator — Education Reader",
    page_icon="📚",
    layout="wide",
)

CUSTOM_CSS = """
<style>
body {
    background: radial-gradient(circle at top left, rgba(66,135,245,0.18), rgba(12,12,34,0.95));
    color: #f5f5f5;
    font-family: 'Inter', 'Pretendard', sans-serif;
}

.stApp {
    background: transparent;
}

main .block-container {
    padding-top: 2.5rem;
    padding-bottom: 4rem;
    max-width: 1200px;
}

.md-viewer {
    background: rgba(255, 255, 255, 0.04);
    border-radius: 24px;
    padding: 2.2rem 2.4rem;
    backdrop-filter: blur(14px);
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 30px 80px rgba(15, 23, 42, 0.45);
    line-height: 1.65;
    color: #eef1f5;
}

.md-viewer h1,
.md-viewer h2,
.md-viewer h3,
.md-viewer h4 {
    background: rgba(255, 255, 255, 0.06);
    border-radius: 18px;
    padding: 0.6rem 1rem;
    margin-top: 1.8rem;
    margin-bottom: 1rem;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.1);
}

.md-viewer h1 { font-size: 2.1rem; }
.md-viewer h2 { font-size: 1.7rem; }
.md-viewer h3 { font-size: 1.35rem; }
.md-viewer h4 { font-size: 1.2rem; }

.md-viewer p, .md-viewer li { font-size: 1.02rem; }

.md-viewer code {
    background: rgba(255,255,255,0.08);
    padding: 0.2rem 0.4rem;
    border-radius: 10px;
    font-size: 0.95rem;
}

.md-viewer pre code {
    display: block;
    padding: 1rem 1.1rem;
    border-radius: 20px;
    background: rgba(10, 20, 45, 0.9);
    box-shadow: inset 0 0 0 1px rgba(255,255,255,0.04);
}

.md-viewer ul, .md-viewer ol {
    padding-left: 1.4rem;
}

.gloss-term {
    position: relative;
    background: linear-gradient(120deg, rgba(120,170,255,0.14), rgba(255,255,255,0.08));
    border-bottom: 1px dotted rgba(255,255,255,0.45);
    border-radius: 12px;
    padding: 0.05rem 0.3rem;
    transition: transform 0.18s ease, box-shadow 0.18s ease;
    cursor: help;
}

.gloss-term:hover {
    transform: scale(1.04);
    box-shadow: 0 12px 30px rgba(80,120,255,0.25);
}

.gloss-term::after {
    content: attr(data-tooltip);
    position: absolute;
    left: 50%;
    transform: translate(-50%, -5px);
    bottom: calc(100% + 8px);
    white-space: nowrap;
    padding: 0.35rem 0.6rem;
    border-radius: 12px;
    background: rgba(10,16,33,0.92);
    color: rgba(255,255,255,0.95);
    font-size: 0.78rem;
    line-height: 1.2;
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.15s ease, transform 0.15s ease;
    box-shadow: 0 12px 26px rgba(0,0,0,0.35);
    border: 1px solid rgba(255,255,255,0.08);
}

.gloss-term:hover::after {
    opacity: 1;
    transform: translate(-50%, -12px);
}

.sidebar-card {
    background: rgba(255,255,255,0.04);
    border-radius: 18px;
    padding: 1rem 1.2rem;
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 18px 40px rgba(10,10,30,0.45);
}

.vocab-card {
    background: rgba(255,255,255,0.04);
    border-radius: 16px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
    border: 1px solid rgba(255,255,255,0.1);
}

.vocab-card h4 {
    margin: 0;
    color: rgba(255,255,255,0.92);
}

.stTabs [data-baseweb="tab"] {
    font-size: 1rem;
    padding-top: 0.75rem;
    padding-bottom: 0.75rem;
}

.info-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.35rem 0.7rem;
    border-radius: 999px;
    background: rgba(120,170,255,0.15);
    color: rgba(226,236,255,0.95);
    font-size: 0.85rem;
    margin-right: 0.4rem;
    margin-bottom: 0.4rem;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def get_catalog() -> List[Dict[str, str]]:
    catalog: List[Dict[str, str]] = []
    for path in iter_markdown_files():
        markdown_text, title = load_markdown_content(path)
        relative = ensure_relative_path(path)
        catalog.append(
            {
                "path": str(path),
                "title": title,
                "relative": relative,
                "preview": markdown_text[:200],
            }
        )
    return catalog


def ensure_vocabulary_state() -> None:
    if "vocab_entries" not in st.session_state:
        st.session_state["vocab_entries"] = load_vocabulary()
    if "glossary" not in st.session_state:
        st.session_state["glossary"] = load_glossary()
    if "modal_term" not in st.session_state:
        st.session_state["modal_term"] = None


ensure_vocabulary_state()

catalog = get_catalog()
if not catalog:
    st.error("Education 폴더에서 학습 자료(.md)를 찾을 수 없습니다.")
    st.stop()

glossary = st.session_state["glossary"]

if st.sidebar.button("🔄 글로서리 새로고침"):
    st.session_state["glossary"] = load_glossary()
    st.rerun()

st.sidebar.title("Appducator Navigator")
search_query = st.sidebar.text_input("검색", placeholder="예: FastAPI, ML, 보안")

path_options = catalog
if search_query:
    sq = search_query.lower()
    path_options = [
        item
        for item in catalog
        if sq in item["title"].lower()
        or sq in item["relative"].lower()
        or sq in item["preview"].lower()
    ]

sections = sorted({item["relative"].split("/")[0] for item in path_options})
selected_section = st.sidebar.selectbox(
    "폴더 필터",
    options=["전체"] + sections,
    index=0,
)

if selected_section != "전체":
    path_options = [item for item in path_options if item["relative"].split("/")[0] == selected_section]

option_labels = [f"{item['relative']} — {item['title']}" for item in path_options]

if not option_labels:
    st.warning("필터 조건을 만족하는 문서를 찾을 수 없습니다.")
    st.stop()

selected_label = st.sidebar.selectbox("학습 문서", option_labels)
selected_item = next(item for item in path_options if f"{item['relative']} — {item['title']}" == selected_label)
selected_path = Path(selected_item["path"])

md_text, doc_title = load_markdown_content(selected_path)
html = markdown_to_html(md_text)
highlighted_html, highlighted_terms = highlight_terms(html, glossary)
safe_html = sanitize_html(highlighted_html)

st.sidebar.markdown(
    """
<div class="sidebar-card">
<h4>인식된 기술 용어</h4>
<p style="font-size:0.9rem; opacity:0.8;">마우스를 올리면 설명이 나타나고, 아래 탭에서 용어장을 관리할 수 있습니다.</p>
</div>
""",
    unsafe_allow_html=True,
)

with st.sidebar.expander("지원 형식 로드맵", expanded=False):
    extensions = ensure_future_ready_extensions()
    for ext, status in extensions.items():
        st.markdown(f"- **{ext.upper()}** → {status}")

reader_tab, vocab_tab, about_tab = st.tabs(["📖 Reader", "🗂 Vocabulary", "ℹ️ About"])

with reader_tab:
    st.markdown(f"<div class='info-chip'>📄 {selected_item['relative']}</div>", unsafe_allow_html=True)
    st.title(doc_title)
    st.markdown(f"<div class='md-viewer'>{safe_html}</div>", unsafe_allow_html=True)

    recognized_terms = sorted(set(highlighted_terms))
    if recognized_terms:
        st.subheader("Detected Concepts")
        st.caption("마우스 오버로 간단 설명을 확인하고, 아래에서 용어장에 추가하세요.")
        for term in recognized_terms:
            short = glossary.get(term, {}).get("short", "정의가 등록되어 있지 않습니다.")
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{term}** — {short}")
            with col2:
                if st.button("용어장 추가", key=f"add-{term}"):
                    st.session_state["modal_term"] = term
    else:
        st.info("인식된 기술 용어가 없습니다. 필요한 용어를 글로서리에 추가해 보세요.")

if st.session_state.get("modal_term"):
    term = st.session_state["modal_term"]
    details = glossary.get(term, {"short": "", "long": "정의가 없습니다."})
    with st.modal(f"{term} — 상세 설명"):
        st.write(details.get("long") or details.get("short"))
        note = st.text_input("추가 메모", key=f"note-{term}", placeholder="개인 메모를 남겨주세요 (선택)")
        if st.button("용어장에 저장", key=f"save-{term}"):
            definition = details.get("long") or details.get("short") or "정의 미등록"
            if note:
                definition = f"{definition}\n\n메모: {note}"
            updated = upsert_vocabulary_term(term, definition)
            st.session_state["vocab_entries"] = updated
            st.toast(f"'{term}'가 용어장에 추가되었습니다.")
            st.session_state["modal_term"] = None
        if st.button("취소", key=f"cancel-{term}"):
            st.session_state["modal_term"] = None

with vocab_tab:
    st.subheader("내 용어장")
    entries = st.session_state.get("vocab_entries", [])
    if not entries:
        st.info("아직 저장된 용어가 없습니다. 문서를 읽으며 용어를 추가해 보세요!")
    else:
        for entry in entries:
            term = entry.get("term") or ""
            definition = entry.get("definition") or ""
            with st.container():
                safe_term = sanitize_html(term)
                safe_definition = sanitize_html(definition).replace("\n", "<br />")
                st.markdown(
                    f"""<div class='vocab-card'><h4>{safe_term}</h4><p style='margin-top:0.4rem;'>{safe_definition}</p></div>""",
                    unsafe_allow_html=True,
                )
                cols = st.columns([0.2, 0.8, 0.2])
                with cols[0]:
                    if st.button("삭제", key=f"delete-{term}"):
                        updated = remove_vocabulary_term(term)
                        st.session_state["vocab_entries"] = updated
                        st.rerun()
        st.download_button(
            "용어장 JSON 내보내기",
            data=json.dumps(entries, ensure_ascii=False, indent=2),
            file_name="appducator_vocabulary.json",
            mime="application/json",
        )

with about_tab:
    st.subheader("Appducator Mission")
    st.markdown(
        """
        Appducator는 Education 폴더의 학습 자료를 누구나 쉽게 탐색하고 이해할 수 있도록 돕는
        Vibe Coding 기반 튜터입니다.

        **학습 여정을 돕는 원칙**
        - 📂 새 폴더나 문서가 추가되어도 자동으로 사이드바에 노출됩니다.
        - 🧠 용어 하이라이팅과 툴팁, 모달을 통해 모르는 개념을 즉시 학습할 수 있습니다.
        - 🗂 용어장은 JSON으로 내보내고, 필요 시 그대로 수정하여 재적재할 수 있습니다.
        - 🧩 PDF/이미지 등 확장 형식은 `ensure_future_ready_extensions()`를 통해 구조적으로 연계할 수 있도록 준비해 두었습니다.

        앞으로 PDF, 이미지 파싱 모듈이 도입되면 `Appducator`의 파이프라인에 손쉽게 추가할 수 있도록
        설계를 유연하게 유지했습니다.
        """
    )

st.sidebar.markdown("---")
st.sidebar.caption("Appducator · Powered by Streamlit · Designed with Vibe Coding principles")
