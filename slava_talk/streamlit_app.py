from modules.ui_components import apply_custom_css
apply_custom_css()

from collections import Counter
from datetime import datetime

import streamlit as st

from modules.vocab_manager import get_topics, load_vocab
from modules.ui_components import apply_custom_css, render_hero_section

st.set_page_config(page_title="SlavaTalk - Home", page_icon="🇺🇦", layout="wide")
apply_custom_css()


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

render_hero_section(
    "SlavaTalk 🇺🇦",
    "🇰🇷 한국어로 배우는 우크라이나어 | 외교·국방·무역 전문가를 위한 실전 어휘"
)

# Metrics in styled cards
st.markdown("### 📊 현재 학습 현황")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div style="font-size: 36px; font-weight: 800;">{len(vocabulary)}</div>
        <div style="font-size: 14px; opacity: 0.9; margin-top: 8px;">등록된 단어</div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class="metric-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
        <div style="font-size: 36px; font-weight: 800;">{len(sources)}</div>
        <div style="font-size: 14px; opacity: 0.9; margin-top: 8px;">참고 문서</div>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown(f"""
    <div class="metric-card" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
        <div style="font-size: 36px; font-weight: 800;">{len(get_topics(vocabulary))}</div>
        <div style="font-size: 14px; opacity: 0.9; margin-top: 8px;">주제 분야</div>
    </div>
    """, unsafe_allow_html=True)
with col4:
    update_text = latest_update.strftime("%Y-%m-%d") if latest_update else "—"
    st.markdown(f"""
    <div class="metric-card" style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);">
        <div style="font-size: 24px; font-weight: 800;">{update_text}</div>
        <div style="font-size: 14px; opacity: 0.9; margin-top: 8px;">최근 업데이트</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Navigation cards
st.markdown("### 🚀 빠른 시작")
nav_cols = st.columns(3)

with nav_cols[0]:
    st.page_link("pages/1_📚_Document_Study.py", label="📚 단어장", icon="📖")
    st.caption("카드형 단어장으로 우크라-한국-영어 학습")

with nav_cols[1]:
    st.page_link("pages/2_❓_Quiz.py", label="❓ 퀴즈", icon="🎯")
    st.caption("한국어 우선 모드로 퀴즈 풀기")

with nav_cols[2]:
    st.page_link("pages/4_🧠_AI_Tutor.py", label="🧠 AI 튜터", icon="🤖")
    st.caption("실전 대화 시뮬레이션")

st.markdown("")
nav_cols2 = st.columns(2)

with nav_cols2[0]:
    st.page_link("pages/3_📊_Progress_Dashboard.py", label="📊 진척도", icon="📈")
    st.caption("학습 현황 및 약점 단어 분석")

with nav_cols2[1]:
    st.page_link("pages/5_🛠️_Vocabulary_Builder.py", label="🛠️ 단어 추가", icon="🧰")
    st.caption("AI로 새 단어 자동 추출")

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
