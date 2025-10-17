from typing import List

import streamlit as st

from modules.ai_client import AIClientError, generate_vocab_from_context
from modules.crawler import crawl_and_extract
from modules.data_loader import export_to_yaml, load_vocab, save_vocab
from modules.vocab_manager import merge_vocab, parse_yaml
from modules.ui_components import apply_custom_css, render_hero_section

st.set_page_config(page_title="Vocabulary Builder - SlavaTalk", page_icon="🛠️", layout="wide")
apply_custom_css()

DEFAULT_URLS = """https://en.wikipedia.org/wiki/Ukraine
https://en.wikipedia.org/wiki/Economy_of_Ukraine
https://en.wikipedia.org/wiki/Politics_of_Ukraine"""

if "builder_results" not in st.session_state:
    st.session_state.builder_results = []
    st.session_state.builder_warnings = []

render_hero_section(
    "🛠️ 단어 추가 도구",
    "AI로 웹사이트에서 자동 추출 | YAML 파일 업로드 | 단어장 관리"
)

with st.expander("📥 Step 1. 웹에서 단어 추출", expanded=True):
    urls_input = st.text_area("📌 URL 목록 (한 줄에 하나씩)", value=DEFAULT_URLS, height=140)
    topics = st.multiselect(
        "🏷️ 주제 선택",
        options=["diplomacy", "defense", "trade", "supply chain", "due diligence", "esg"],
        default=["diplomacy", "defense", "trade", "supply chain"],
    )
    max_terms = st.slider("📊 소스당 최대 단어 수", min_value=5, max_value=30, value=12, step=1)
    proficiency = st.selectbox("🎯 학습자 레벨", options=["novice", "intermediate", "advanced"], index=1)
    manual_text = st.text_area("✍️ 또는 텍스트 직접 입력 (우크라이나어/영어)", height=200, placeholder="뉴스 기사, 문서, 계약서 등을 붙여넣으세요...")

    if st.button("🚀 AI로 단어 추출 시작", type="primary"):
        urls = [line.strip() for line in urls_input.splitlines() if line.strip()]
        results: List[dict] = []
        warnings: List[str] = []

        with st.spinner("Processing sources with ChatGPT…"):
            if urls:
                new_entries, crawl_warnings = crawl_and_extract(
                    urls,
                    topics=topics,
                    max_terms_per_source=max_terms,
                    proficiency=proficiency,
                )
                results = merge_vocab(results, new_entries)
                warnings.extend(crawl_warnings)

            if manual_text.strip():
                try:
                    payload = generate_vocab_from_context(
                        manual_text,
                        topics=topics,
                        max_terms=max_terms,
                        proficiency=proficiency,
                        source="Manual input",
                    )
                    results = merge_vocab(results, payload.get("entries", []))
                    if payload.get("notes"):
                        warnings.append(payload["notes"])
                except AIClientError as exc:
                    warnings.append(f"Manual text extraction failed: {exc}")

        st.session_state.builder_results = results
        st.session_state.builder_warnings = warnings
        if not results:
            st.warning("No vocabulary extracted. Double-check network access or refine your inputs.")

if st.session_state.builder_results:
    st.success(f"✅ {len(st.session_state.builder_results)}개 단어 추출 완료!")
    st.dataframe(st.session_state.builder_results, use_container_width=True)

    yaml_blob = export_to_yaml(st.session_state.builder_results)
    st.download_button(
        "⬇️ YAML 파일 다운로드",
        data=yaml_blob,
        file_name="slavatalk_deck.yaml",
        mime="application/x-yaml",
    )

    if st.button("💾 메인 단어장에 병합하기"):
        current = load_vocab()
        merged = merge_vocab(current, st.session_state.builder_results)
        save_vocab(merged)
        st.success(f"✅ data/vocabulary.json 업데이트 완료! 총 {len(merged)}개 단어")

if st.session_state.builder_warnings:
    st.warning("Warnings:\n- " + "\n- ".join(st.session_state.builder_warnings))

st.markdown("---")
st.subheader("📤 Step 2. YAML/JSON 파일 업로드")

uploaded = st.file_uploader("💾 YAML 또는 JSON 단어장 파일 업로드", type=["yaml", "yml", "json"])
if uploaded:
    try:
        content = uploaded.getvalue().decode("utf-8")
        imported_entries = parse_yaml(content)
        st.write(f"✅ {len(imported_entries)}개 단어 로드 완료")
        st.dataframe(imported_entries, use_container_width=True)
    except Exception as exc:
        st.error(f"❌ 파일 파싱 실패: {exc}")
        imported_entries = []

    if imported_entries and st.button("💾 업로드한 단어 병합하기"):
        current = load_vocab()
        merged = merge_vocab(current, imported_entries)
        save_vocab(merged)
        st.success(f"✅ 병합 완료! 현재 총 {len(merged)}개 단어")

st.markdown("---")
st.caption("💡 팁: YAML 파일을 Git으로 관리하고 팀원들과 공유하세요!")
