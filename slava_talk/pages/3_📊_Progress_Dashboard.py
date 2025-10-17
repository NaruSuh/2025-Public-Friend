from collections import Counter
from typing import List, Dict

import streamlit as st
from modules.ui_components import apply_custom_css, render_hero_section

st.set_page_config(page_title="Progress Dashboard - SlavaTalk", page_icon="📊", layout="wide")
apply_custom_css()


def _ensure_quiz_state() -> None:
    """Guarantee expected quiz-related session keys exist."""
    st.session_state.setdefault("quiz_history", [])
    st.session_state.setdefault("quiz_score", 0)
    st.session_state.setdefault("quiz_questions", 0)
    st.session_state.setdefault("quiz_streak", 0)


def _compute_accuracy(score: int, total: int) -> float:
    return round((score / total) * 100, 1) if total else 0.0


def _prepare_miss_list(history: List[Dict[str, str]], top_n: int = 10) -> List[Dict[str, str]]:
    misses = [item["term"] for item in history if not item.get("was_correct")]
    counter = Counter(misses)
    return [{"Term": term, "Misses": count} for term, count in counter.most_common(top_n)]


_ensure_quiz_state()

render_hero_section(
    "📊 학습 진척도 대시보드",
    "퀴즈 통계 분석 | 약점 단어 파악 | 학습 현황 한눈에"
)

history: List[Dict[str, str]] = st.session_state.quiz_history
score = st.session_state.quiz_score
total = st.session_state.quiz_questions
streak = st.session_state.quiz_streak

metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
metrics_col1.metric("전체 정답률 (%)", f"{_compute_accuracy(score, total)}%")
metrics_col2.metric("총 학습 단어", total)
metrics_col3.metric("현재 연속 정답", streak)

if not history:
    st.info("📝 퀴즈를 몇 번 풀면 진척도 리포트가 생성됩니다.")
    st.stop()

st.markdown("### 📈 모드별 성과")
mode_counter = Counter(item.get("mode", "Unknown") for item in history)
mode_correct = Counter(item.get("mode", "Unknown") for item in history if item.get("was_correct"))

mode_rows = []
for mode, attempts in mode_counter.items():
    correct = mode_correct.get(mode, 0)
    mode_rows.append(
        {
            "Mode": mode,
            "Attempts": attempts,
            "Correct": correct,
            "Accuracy (%)": _compute_accuracy(correct, attempts),
        }
    )

st.dataframe(mode_rows, use_container_width=True, hide_index=True)

st.markdown("### 🎯 복습이 필요한 단어")
miss_rows = _prepare_miss_list(history)
if miss_rows:
    st.dataframe(miss_rows, use_container_width=True, hide_index=True)
else:
    st.success("✅ 틀린 단어가 없습니다! 완벽해요!")
