import streamlit as st

from modules.ai_client import AIClientError, request_tutor_reply

st.set_page_config(page_title="AI Tutor - SlavaTalk", page_icon="🧠", layout="centered")

SCENARIOS = {
    "Diplomatic briefing": "Prepare for a bilateral meeting on reconstruction assistance and governance reforms.",
    "Defense logistics": "Coordinate equipment delivery and security posture with Ukrainian counterparts.",
    "Trade compliance": "Discuss export controls, customs clearance, and fair procurement practices.",
    "Supply-chain due diligence": "Evaluate ESG risks, labour conditions, and infrastructure resilience.",
}


def reset_dialogue():
    st.session_state.tutor_history = []
    st.session_state.tutor_system = None


if "tutor_history" not in st.session_state:
    reset_dialogue()

st.title("🧠 AI Conversation Tutor")
st.caption("Role-play high-stakes scenarios in Ukrainian. The tutor corrects, reinforces, and keeps you mission-ready.")

with st.sidebar:
    st.header("Scenario Setup")
    scenario = st.selectbox("Scenario", options=list(SCENARIOS.keys()))
    proficiency = st.selectbox("Proficiency", options=["novice", "intermediate", "advanced"], index=1)
    language_mix = st.slider("English assist (%)", min_value=0, max_value=60, value=25, step=5)
    auto_reset = st.checkbox("Reset conversation on scenario change", value=True)

    if st.button("Start fresh"):
        reset_dialogue()
        st.experimental_rerun()

if auto_reset and (st.session_state.get("tutor_system") != scenario):
    reset_dialogue()
    st.session_state.tutor_system = scenario

if not st.session_state.tutor_history:
    seed = (
        f"Please open the dialogue for this scenario: {SCENARIOS[scenario]}.\n"
        f"Include a greeting, a probing question, and highlight 2 mission terms.\n"
        f"Use roughly {language_mix}% English scaffolding for clarity."
    )
    try:
        first_reply = request_tutor_reply(
            [{"role": "user", "content": seed}],
            scenario=scenario,
            target_language="ukrainian",
            proficiency=proficiency,
        )
    except AIClientError as exc:
        st.error(f"Unable to start tutor session: {exc}")
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
            [{"role": "user", "content": f"Keep approximately {language_mix}% English support when needed."}]
            + st.session_state.tutor_history,
            scenario=scenario,
            target_language="ukrainian",
            proficiency=proficiency,
        )
    except AIClientError as exc:
        st.error(f"AI tutor error: {exc}")
    else:
        st.session_state.tutor_history.append({"role": "assistant", "content": reply})
    st.experimental_rerun()

st.markdown("---")
st.caption("Tip: Copy useful turns into your YAML deck or trigger the Vocabulary Builder for deeper dives.")
