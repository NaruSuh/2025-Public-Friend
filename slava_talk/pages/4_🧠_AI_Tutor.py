import streamlit as st

from modules.ai_client import AIClientError, request_tutor_reply
from modules.ui_components import apply_custom_css, render_hero_section

st.set_page_config(page_title="AI Tutor - SlavaTalk", page_icon="🧠", layout="centered")
apply_custom_css()

SCENARIOS = {
    "Diplomatic briefing": "Prepare for a bilateral meeting on reconstruction assistance and governance reforms.",
    "Defense logistics": "Coordinate equipment delivery and security posture with Ukrainian counterparts.",
    "Trade compliance": "Discuss export controls, customs clearance, and fair procurement practices.",
    "Supply-chain due diligence": "Evaluate ESG risks, labour conditions, and infrastructure resilience.",
}

QUOTA_MESSAGE = (
    "OpenAI API 크레딧 한도가 소진돼서 튜터가 응답할 수 없습니다. "
    "다음 중 하나를 조치한 뒤 ‘Start fresh’를 눌러 다시 시도하세요:\n"
    "1) https://platform.openai.com/account/usage 에서 사용량 확인\n"
    "2) Billing 페이지에서 결제 수단/월 한도 상향 또는 토큰 충전\n"
    "3) 잔여 크레딧이 있는 다른 API 키를 `OPENAI_API_KEY`로 교체"
)


def reset_dialogue(*, preserve_error: bool = False) -> None:
    """Clear chat history and optionally reset error flags."""
    st.session_state.tutor_history = []
    st.session_state.tutor_system = None
    if not preserve_error:
        st.session_state.tutor_disabled = False
        st.session_state.tutor_error_message = ""


def ensure_state() -> None:
    if "tutor_history" not in st.session_state:
        st.session_state.tutor_history = []
    if "tutor_system" not in st.session_state:
        st.session_state.tutor_system = None
    if "tutor_disabled" not in st.session_state:
        st.session_state.tutor_disabled = False
    if "tutor_error_message" not in st.session_state:
        st.session_state.tutor_error_message = ""


def flag_error(exc: AIClientError, *, context: str) -> None:
    message = str(exc)
    lowered = message.lower()
    if "insufficient_quota" in lowered or "exceeded your current quota" in lowered:
        st.session_state.tutor_disabled = True
        st.session_state.tutor_error_message = QUOTA_MESSAGE
    else:
        st.session_state.tutor_error_message = f"{context}: {message}"


ensure_state()

render_hero_section(
    "🧠 AI 대화 튜터",
    "🇺🇦 실전 시나리오로 우크라이나어 회화 연습 | AI가 교정하고 피드백"
)

with st.sidebar:
    st.header("🎯 시나리오 설정")
    scenario = st.selectbox("상황 선택", options=list(SCENARIOS.keys()))
    proficiency = st.selectbox("실력 레벨", options=["novice", "intermediate", "advanced"], index=1)
    language_mix = st.slider("영어 힌트 비율 (%)", min_value=0, max_value=60, value=25, step=5)
    korean_hint = st.slider("한국어 힌트 비율 (%)", min_value=0, max_value=40, value=15, step=5)
    auto_reset = st.checkbox("시나리오 변경시 대화 초기화", value=True)

    if st.button("🔄 새로 시작", use_container_width=True):
        reset_dialogue(preserve_error=False)
        st.rerun()

if auto_reset and (st.session_state.get("tutor_system") != scenario):
    reset_dialogue(preserve_error=True)
    st.session_state.tutor_system = scenario

if st.session_state.tutor_disabled:
    st.error(st.session_state.tutor_error_message or QUOTA_MESSAGE)
    st.stop()

if not st.session_state.tutor_history:
    seed = (
        f"Please open the dialogue for this scenario: {SCENARIOS[scenario]}.\n"
        f"Include a greeting, a probing question, and highlight 2 mission terms.\n"
        f"Use roughly {language_mix}% English scaffolding for clarity.\n"
        f"Additionally, provide {korean_hint}% Korean hints in parentheses for key terms to help Korean learners."
    )
    try:
        first_reply = request_tutor_reply(
            [{"role": "user", "content": seed}],
            scenario=scenario,
            target_language="ukrainian",
            proficiency=proficiency,
        )
    except AIClientError as exc:
        flag_error(exc, context="Unable to start tutor session")
        st.error(st.session_state.tutor_error_message)
        st.stop()
    else:
        st.session_state.tutor_history.append({"role": "assistant", "content": first_reply})

for message in st.session_state.tutor_history:
    role = message["role"]
    with st.chat_message("user" if role == "user" else "assistant"):
        st.markdown(message["content"])

user_input = st.chat_input("Перейдімо до розмови…")

if user_input:
    st.session_state.tutor_history.append({"role": "user", "content": user_input})
    try:
        reply = request_tutor_reply(
            [{"role": "user", "content": f"Keep approximately {language_mix}% English support and {korean_hint}% Korean hints in parentheses when needed."}]
            + st.session_state.tutor_history,
            scenario=scenario,
            target_language="ukrainian",
            proficiency=proficiency,
        )
    except AIClientError as exc:
        flag_error(exc, context="AI tutor error")
        st.error(st.session_state.tutor_error_message)
    else:
        st.session_state.tutor_history.append({"role": "assistant", "content": reply})
    st.rerun()

st.markdown("---")
st.caption("Tip: Copy useful turns into your YAML deck or trigger the Vocabulary Builder for deeper dives.")
