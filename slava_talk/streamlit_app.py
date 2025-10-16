from collections import Counter
from datetime import datetime

import streamlit as st

from modules.vocab_manager import get_topics, load_vocab

st.set_page_config(page_title="SlavaTalk - Home", page_icon="🇺🇦", layout="wide")


def _latest_timestamp(entries):
    stamps = []
    for item in entries:
        ts = item.get("created_at")
        if not ts:
            continue
        ts = ts.replace("Z", "+00:00")
        try:
            stamps.append(datetime.fromisoformat(ts))
        except ValueError:
            continue
    return max(stamps) if stamps else None


vocabulary = load_vocab()
topic_counts = Counter()
for entry in vocabulary:
    for topic in entry.get("topics", []):
        topic_counts[topic] += 1

sources = sorted({entry.get("source") for entry in vocabulary if entry.get("source")})
latest_update = _latest_timestamp(vocabulary)

st.title("SlavaTalk 🇺🇦")
st.subheader("Mission-grade Ukrainian for diplomacy, defense, trade, and supply chain due diligence.")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Active Terms", len(vocabulary))
col2.metric("Source Documents", len(sources))
col3.metric("Tracked Topics", len(get_topics(vocabulary)))
col4.metric("Latest Update", latest_update.strftime("%Y-%m-%d") if latest_update else "—")

st.markdown(
    """
SlavaTalk combines curated documents, live crawling, and the ChatGPT API to deliver tactical vocabulary
for teams working on Ukraine's reconstruction portfolio. Build a YAML-based lexicon, drill it like Duolingo,
and deploy scenario-specific conversations with the AI tutor.
"""
)

with st.container():
    st.markdown("### Quick Launch")
    st.page_link("pages/1_📚_Document_Study.py", label="📚 Document Study", icon="📄")
    st.page_link("pages/2_❓_Quiz.py", label="❓ Adaptive Quiz", icon="🧠")
    st.page_link("pages/3_🧠_AI_Tutor.py", label="🧠 AI Tutor", icon="🤖")
    st.page_link("pages/4_🛠️_Vocabulary_Builder.py", label="🛠️ Vocabulary Builder", icon="🧰")

st.markdown("---")

tab_overview, tab_ai, tab_ops = st.tabs(["Operational Focus", "AI Workflow", "Ops Checklist"])

with tab_overview:
    st.markdown(
        """
        - **Diplomacy**: Negotiation, multilateral fora, reconstruction pledges.
        - **Defense & Security**: Force posture, bilateral assistance, compliance.
        - **Trade**: Customs, export controls, reconstruction tenders.
        - **Supply-chain DD**: ESG, human rights, infrastructure integrity.
        """
    )

    if topic_counts:
        st.markdown("#### Vocabulary Heatmap")
        chart_data = {
            "Topic": list(topic_counts.keys()),
            "Terms": list(topic_counts.values()),
        }
        st.bar_chart(chart_data, x="Topic", y="Terms", use_container_width=True)

with tab_ai:
    st.markdown(
        """
1. **Ingest**: Crawl official communiqués, defense briefings, WTO notices, or supply-chain advisories.
2. **Enrich**: ChatGPT distills Ukrainian keywords, Korean/English glosses, and mission-centric notes.
3. **Deploy**: Push to YAML, run quizzes, script role plays, and export/share the lexicon.
4. **Iterate**: Upload refined YAML sets and keep your team synchronized.
"""
    )

with tab_ops:
    st.markdown(
        """
        - Validate your OpenAI key inside `.streamlit/secrets.toml`.
        - Feed SlavaTalk mission documents (`reference/` or live URLs).
        - Use YAML exports for inter-agency sharing or offline study.
        - Rotate between quizzes and AI tutor for retention checks.
        """
    )

st.caption(
    "Need a new topic or workflow? Use the Vocabulary Builder to crawl trusted sources and refresh the lexicon."
)
