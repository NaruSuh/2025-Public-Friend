from typing import List

import streamlit as st

from modules.ai_client import AIClientError, generate_vocab_from_context
from modules.crawler import crawl_and_extract
from modules.data_loader import export_to_yaml, load_vocab, save_vocab
from modules.vocab_manager import merge_vocab, parse_yaml

st.set_page_config(page_title="Vocabulary Builder - SlavaTalk", page_icon="🛠️", layout="wide")

DEFAULT_URLS = """https://mfa.gov.ua/news
https://www.mil.gov.ua/en/news.html
https://www.me.gov.ua/Documents/List?lang=en-GB&tag=ForeignEconomicActivity
https://www.oecd.org/corporate/mne/"""

if "builder_results" not in st.session_state:
    st.session_state.builder_results = []
    st.session_state.builder_warnings = []

st.title("🛠️ Vocabulary Builder")
st.caption("Crawl trusted sources, let ChatGPT distill mission terms, and manage YAML decks.")

with st.expander("Step 1. Harvest sources"):
    urls_input = st.text_area("Source URLs (one per line)", value=DEFAULT_URLS, height=140)
    topics = st.multiselect(
        "Focus topics",
        options=["diplomacy", "defense", "trade", "supply chain", "due diligence", "esg"],
        default=["diplomacy", "defense", "trade", "supply chain"],
    )
    max_terms = st.slider("Max terms per source", min_value=5, max_value=30, value=12, step=1)
    proficiency = st.selectbox("Target learner level", options=["novice", "intermediate", "advanced"], index=1)
    manual_text = st.text_area("Optional: paste custom Ukrainian/English reference text", height=200, placeholder="Paste communiqués, contracts, or analyst notes…")

    if st.button("Crawl & Build set", type="primary"):
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
    st.success(f"{len(st.session_state.builder_results)} unique items extracted.")
    st.dataframe(st.session_state.builder_results, use_container_width=True)

    yaml_blob = export_to_yaml(st.session_state.builder_results)
    st.download_button(
        "Download YAML deck",
        data=yaml_blob,
        file_name="slavatalk_deck.yaml",
        mime="application/x-yaml",
    )

    if st.button("Merge into workspace dataset"):
        current = load_vocab()
        merged = merge_vocab(current, st.session_state.builder_results)
        save_vocab(merged)
        st.success(f"✅ Updated data/vocabulary.json with {len(merged)} total entries.")

if st.session_state.builder_warnings:
    st.warning("Warnings:\n- " + "\n- ".join(st.session_state.builder_warnings))

st.markdown("---")
st.subheader("Step 2. Import existing YAML deck")

uploaded = st.file_uploader("Upload YAML or JSON vocabulary dataset", type=["yaml", "yml", "json"])
if uploaded:
    try:
        content = uploaded.getvalue().decode("utf-8")
        imported_entries = parse_yaml(content)
        st.write(f"Loaded {len(imported_entries)} entries from upload.")
        st.dataframe(imported_entries, use_container_width=True)
    except Exception as exc:
        st.error(f"Failed to parse uploaded file: {exc}")
        imported_entries = []

    if imported_entries and st.button("Merge uploaded deck"):
        current = load_vocab()
        merged = merge_vocab(current, imported_entries)
        save_vocab(merged)
        st.success(f"Upload merged. Vocabulary now contains {len(merged)} entries.")

st.markdown("---")
st.caption("Tip: Keep curated YAML decks under version control and share across teams for synchronized missions.")
