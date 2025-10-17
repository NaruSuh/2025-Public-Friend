import io
import random
from typing import Dict, List, Optional

import streamlit as st
from gtts import gTTS

from modules.ai_client import AIClientError, generate_quiz_feedback
from modules.data_loader import filter_vocab, load_vocab
from modules.ui_components import (
    apply_custom_css,
    render_progress_bar,
    render_streak_display,
)
from modules.vocab_manager import get_topics

st.set_page_config(page_title="Quiz - SlavaTalk", page_icon="❓", layout="centered")
apply_custom_css()

# Ultra-compact layout with no scrolling
st.markdown("""
<style>
/* Kill ALL scrolling */
section.main > div {
    max-height: 100vh !important;
    overflow: hidden !important;
    padding: 0 !important;
}

section.main {
    overflow: hidden !important;
}

.block-container {
    padding-top: 1rem !important;
    padding-bottom: 0 !important;
    max-height: 100vh !important;
    overflow: hidden !important;
}

/* Ultra-compact quiz card */
.quiz-card {
    margin: 0.3rem auto !important;
    padding: 0.8rem !important;
}

/* Minimal button spacing */
.stButton > button {
    margin: 0.2rem 0 !important;
    padding: 0.4rem 1rem !important;
    font-size: 0.9rem !important;
}

/* Compact columns */
.row-widget.stHorizontal {
    gap: 0.3rem !important;
    margin: 0.2rem 0 !important;
}

/* Compact feedback */
div[style*="linear-gradient(135deg, #2d3748"] {
    margin: 0.3rem 0 !important;
    padding: 8px 12px !important;
    font-size: 10pt !important;
}

/* Minimal progress bar */
.stProgress {
    margin: 0.2rem 0 !important;
}

/* Compact audio player */
audio {
    max-height: 32px !important;
    margin: 0.3rem 0 !important;
}
</style>
""", unsafe_allow_html=True)

QUESTION_MODES = {
    "🇺🇦→🇰🇷 우크라이나어 보고 한국어 맞추기": {"type": "mc", "field": "korean", "prompt_lang": "ukrainian"},
    "🇰🇷→🇺🇦 한국어 보고 우크라이나어 쓰기": {"type": "text", "field": "korean", "prompt_lang": "korean"},
    "🇺🇦→🇬🇧 우크라이나어 보고 영어 맞추기": {"type": "mc", "field": "english", "prompt_lang": "ukrainian"},
    "🇬🇧→🇺🇦 영어 보고 우크라이나어 쓰기": {"type": "text", "field": "english", "prompt_lang": "english"},
    "🇰🇷+🇬🇧→🇺🇦 한영 보고 우크라 쓰기": {"type": "text", "field": "both", "prompt_lang": "both"},
}


def reset_answer_state():
    """Clear per-question UI state so highlights and inputs reset cleanly."""
    st.session_state.selected_choice_idx = None
    st.session_state.answer_state = None
    st.session_state.answer_revealed = False
    st.session_state.quiz_text_answer = ""


def reset_quiz_state():
    reset_answer_state()
    st.session_state.quiz_word = None
    st.session_state.quiz_options = []
    st.session_state.quiz_score = 0
    st.session_state.quiz_questions = 0
    st.session_state.quiz_streak = 0
    st.session_state.raw_feedback = "" # Refactored
    st.session_state.quiz_history = []


def ensure_state():
    if "quiz_word" not in st.session_state:
        reset_quiz_state()
    if "quiz_pool" not in st.session_state:
        st.session_state.quiz_pool = []
    if "quiz_filters_signature" not in st.session_state:
        st.session_state.quiz_filters_signature = None
    if "quiz_mode" not in st.session_state:
        st.session_state.quiz_mode = list(QUESTION_MODES.keys())[0]
    if "quiz_proficiency" not in st.session_state:
        st.session_state.quiz_proficiency = "intermediate"
    if "quiz_option_count" not in st.session_state:
        st.session_state.quiz_option_count = 4
    if "review_vocabulary" not in st.session_state:
        st.session_state.review_vocabulary = []
    if "raw_feedback" not in st.session_state: # Refactored
        st.session_state.raw_feedback = ""
    if "selected_choice_idx" not in st.session_state:
        st.session_state.selected_choice_idx = None
    if "answer_state" not in st.session_state:
        st.session_state.answer_state = None
    if "answer_revealed" not in st.session_state:
        st.session_state.answer_revealed = False
    if "quiz_text_answer" not in st.session_state:
        st.session_state.quiz_text_answer = ""


def build_question_pool(vocab: List[Dict], *, topics: List[str]) -> List[Dict]:
    filtered = filter_vocab(vocab, topics=topics)
    return filtered if filtered else vocab


def generate_new_question(question_mode: str, n_options: int):
    pool = st.session_state.quiz_pool
    if not pool:
        return

    reset_answer_state()
    vocab_entry = random.choice(pool)
    st.session_state.quiz_word = vocab_entry
    st.session_state.raw_feedback = "" # Refactored
    st.session_state.audio_played = False  # Reset audio play flag

    if QUESTION_MODES[question_mode]["type"] == "mc":
        options = [vocab_entry]
        incorrect_pool = [item for item in pool if item != vocab_entry]
        num_options_to_get = min(len(incorrect_pool), n_options - 1)

        if num_options_to_get > 0:
            options.extend(random.sample(incorrect_pool, num_options_to_get))

        random.shuffle(options)
        st.session_state.quiz_options = options
    else:
        st.session_state.quiz_options = []


def evaluate_mc_answer(selected_text: str, mode_field: str) -> bool:
    correct = st.session_state.quiz_word.get(mode_field, "")
    return selected_text == correct


def evaluate_text_answer(user_input: str) -> bool:
    correct = st.session_state.quiz_word.get("ukrainian", "")
    return user_input.strip().lower() == correct.lower()


def record_result(is_correct: bool):
    st.session_state.quiz_questions += 1
    if is_correct:
        st.session_state.quiz_score += 1
        st.session_state.quiz_streak += 1
    else:
        st.session_state.quiz_streak = 0

    st.session_state.quiz_history.append(
        {
            "term": st.session_state.quiz_word.get("ukrainian"),
            "was_correct": is_correct,
            "mode": st.session_state.quiz_mode,
        }
    )


def process_answer(user_choice: str, *, selected_idx: Optional[int] = None):
    """Evaluate the current answer once per question and store the outcome."""
    if st.session_state.get("answer_revealed"):
        return

    mode_meta = QUESTION_MODES[st.session_state.quiz_mode]
    if selected_idx is not None:
        st.session_state.selected_choice_idx = selected_idx

    if mode_meta["type"] == "mc":
        is_correct = evaluate_mc_answer(user_choice, mode_meta["field"])
        expected = st.session_state.quiz_word.get(mode_meta["field"])
    else:
        is_correct = evaluate_text_answer(user_choice)
        expected = st.session_state.quiz_word.get("ukrainian")

    record_result(is_correct)
    st.session_state.answer_state = {
        "is_correct": is_correct,
        "expected": expected,
        "user_choice": user_choice,
    }
    st.session_state.answer_revealed = True

    try:
        feedback = generate_quiz_feedback(
            st.session_state.quiz_word,
            user_answer=user_choice,
            is_correct=is_correct,
            proficiency=st.session_state.quiz_proficiency,
        )
        st.session_state.raw_feedback = feedback
    except AIClientError as exc:
        st.session_state.raw_feedback = f"(AI feedback unavailable: {exc})"


def handle_text_answer_submit():
    """Callback for text input answers."""
    if st.session_state.get("answer_revealed"):
        return

    answer = st.session_state.get("quiz_text_answer", "")
    if answer and answer.strip():
        trimmed = answer.strip()
        st.session_state.quiz_text_answer = trimmed
        process_answer(trimmed)


def handle_next_question():
    st.session_state.raw_feedback = "" # Refactored
    generate_new_question(st.session_state.quiz_mode, st.session_state.quiz_option_count)


def handle_skip_question():
    st.session_state.raw_feedback = "" # Refactored
    generate_new_question(st.session_state.quiz_mode, st.session_state.quiz_option_count)


def handle_pass_and_add_to_review():
    current_word = st.session_state.quiz_word
    if current_word:
        already_exists = any(
            item.get("ukrainian") == current_word.get("ukrainian")
            for item in st.session_state.review_vocabulary
        )
        if not already_exists:
            st.session_state.review_vocabulary.append(current_word)
    st.session_state.raw_feedback = "" # Refactored
    generate_new_question(st.session_state.quiz_mode, st.session_state.quiz_option_count)


def handle_reset_progress():
    reset_quiz_state()
    st.session_state.quiz_word = None


def calculate_max_streak(history: List[Dict]) -> int:
    if not history:
        return 0
    max_streak = 0
    current_streak = 0
    for item in history:
        if item.get("was_correct", False):
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0
    return max_streak


def generate_tts_audio(text: str, lang: str = "uk") -> bytes:
    try:
        tts = gTTS(text=text, lang=lang)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read()
    except Exception as e:
        st.error(f"Failed to generate TTS audio: {e}")
        return None


# --- Main App Logic ---
ensure_state()

vocabulary = load_vocab()
if not vocabulary:
    st.error("Vocabulary data could not be loaded. Cannot start quiz.")
    st.stop()

topics = get_topics(vocabulary)

with st.sidebar:
    # Modern sidebar styling
    st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1d24 0%, #0f1117 100%);
    }
    [data-testid="stSidebar"] .stMarkdown h2 {
        color: #4299e1;
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #90cdf4;
        font-size: 1rem;
        font-weight: 500;
        margin-bottom: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("## ⚙️ 설정")

    with st.expander("🎮 퀴즈 옵션", expanded=True):
        with st.form("quiz_filters"):
            selected_topics = st.multiselect("주제 선택", options=topics, default=topics)
            question_mode = st.selectbox("퀴즈 유형", options=list(QUESTION_MODES.keys()))
            n_options = st.slider("선택지 개수", min_value=3, max_value=6, value=4, step=1)
            proficiency = st.selectbox(
                "AI 피드백 레벨", options=["novice", "intermediate", "advanced"], index=1
            )
            apply_filters = st.form_submit_button("✅ 적용", use_container_width=True)

    with st.expander("🔊 음성 옵션", expanded=False):
        tts_method = st.radio(
            "TTS 방식",
            ["Google TTS (st.audio)", "브라우저 내장 TTS"],
            help="Google TTS는 자연스럽지만 느리고, 브라우저 TTS는 빠르지만 음질이 낮습니다",
        )
        auto_play_tts = st.checkbox("자동 재생", value=True, help="새 문제가 나올 때마다 자동으로 발음 재생")

    st.session_state.quiz_tts_method = tts_method
    st.session_state.quiz_auto_play = auto_play_tts

    st.markdown("---")

    # Session statistics in sidebar
    if st.session_state.quiz_history:
        correct = sum(1 for item in st.session_state.quiz_history if item["was_correct"])
        total = len(st.session_state.quiz_history)
        accuracy = (correct / total * 100) if total > 0 else 0
        max_streak_val = max(st.session_state.quiz_streak, calculate_max_streak(st.session_state.quiz_history))

        with st.expander("📊 세션 통계", expanded=True):
            st.metric("정답 수", f"{correct}/{total}")
            st.metric("정답률", f"{accuracy:.1f}%")
            st.metric("최고 스트릭", max_streak_val)

            miss_list = [item["term"] for item in st.session_state.quiz_history if not item["was_correct"]]
            if miss_list:
                st.markdown("**🎯 복습 필요**")
                st.caption(", ".join(list(set(miss_list))[:5]))
                if len(set(miss_list)) > 5:
                    st.caption(f"...외 {len(set(miss_list)) - 5}개")

    with st.expander("📖 복습 단어장", expanded=False):
        st.caption(f"{len(st.session_state.review_vocabulary)}개 단어")

        if st.session_state.review_vocabulary:
            from modules.data_loader import export_to_yaml

            yaml_data = export_to_yaml(st.session_state.review_vocabulary)
            st.download_button(
                "⬇️ YAML 다운로드",
                data=yaml_data,
                file_name="review_vocabulary.yaml",
                mime="application/x-yaml",
                use_container_width=True,
            )

            if st.button("🗑️ 단어장 비우기", use_container_width=True):
                st.session_state.review_vocabulary = []
                st.rerun()

            st.markdown("**저장된 단어**")
            for idx, word in enumerate(st.session_state.review_vocabulary[:5], 1):
                with st.expander(f"{idx}. {word.get('ukrainian', '')}"):
                    st.write(f"🇰🇷 {word.get('korean', '')}")
                    st.write(f"🇬🇧 {word.get('english', '')}")

            if len(st.session_state.review_vocabulary) > 5:
                st.caption(f"...외 {len(st.session_state.review_vocabulary) - 5}개")
        else:
            st.info("Pass 버튼으로 모르는 단어를 추가하세요!")

    st.markdown("---")
    st.button("🔄 진행 초기화", on_click=handle_reset_progress, use_container_width=True)

mode_config = QUESTION_MODES[question_mode]
option_count = n_options if mode_config["type"] == "mc" else 0

signature = (tuple(sorted(selected_topics)), question_mode, option_count)
if apply_filters or signature != st.session_state.quiz_filters_signature:
    st.session_state.quiz_pool = build_question_pool(vocabulary, topics=selected_topics)
    st.session_state.quiz_filters_signature = signature
    st.session_state.quiz_mode = question_mode
    st.session_state.quiz_proficiency = proficiency
    st.session_state.quiz_option_count = option_count
    generate_new_question(question_mode, option_count)

if not st.session_state.quiz_pool:
    st.error("No vocabulary available for the selected topics.")
    st.stop()

if st.session_state.quiz_word is None:
    st.session_state.quiz_mode = question_mode
    st.session_state.quiz_proficiency = proficiency
    st.session_state.quiz_option_count = option_count
    generate_new_question(st.session_state.quiz_mode, st.session_state.quiz_option_count)

col1, col2 = st.columns([2, 1])
with col1:
    render_progress_bar(
        st.session_state.quiz_score,
        st.session_state.quiz_questions,
        label=f"정답률: {st.session_state.quiz_score} / {st.session_state.quiz_questions}",
    )
with col2:
    render_streak_display(st.session_state.quiz_streak)

mode_meta = QUESTION_MODES[st.session_state.quiz_mode]
target_entry = st.session_state.quiz_word

prompt_lang = mode_meta.get("prompt_lang", "ukrainian")
field_name_kr = {"korean": "한국어", "english": "영어"}
if mode_meta["type"] == "mc":
    if prompt_lang == "ukrainian":
        field_display = field_name_kr.get(mode_meta["field"], mode_meta["field"])
        question_text = f'다음 우크라이나어의 <strong>{field_display}</strong> 뜻은?'
        question_term = target_entry["ukrainian"]
    else:
        question_text = "다음의 우크라이나어는?"
        question_term = target_entry.get(mode_meta["field"], "")
else:
    if prompt_lang == "both":
        question_text = "다음의 우크라이나어를 입력하세요:"
        question_term = f'🇰🇷 {target_entry.get("korean", "")} / 🇬🇧 {target_entry.get("english", "")}'
    elif prompt_lang == "korean":
        question_text = "다음 한국어의 우크라이나어를 입력하세요:"
        question_term = target_entry.get("korean", "")
    else:
        question_text = "다음 영어의 우크라이나어를 입력하세요:"
        question_term = target_entry.get("english", "")

ukrainian_word = target_entry.get("ukrainian", "")
pronunciation = target_entry.get("pronunciation", "—")

tts_method = st.session_state.get("quiz_tts_method", "브라우저 내장 TTS")
auto_play = st.session_state.get("quiz_auto_play", True)

quiz_card_html = f"""
<div class="quiz-card" style="margin: 0.5rem auto; padding: 1rem;">
    <div style="font-size: 16px; color: #7f8c8d; margin-bottom: 8px;">{question_text}</div>
    <div id="quiz-term" style="font-size: 28px; font-weight: 700; color: #0057B7; margin: 10px 0;">{question_term}</div>
    <div style="font-size: 14px; color: #95a5a6;">🔊 {pronunciation.replace('<', '&lt;').replace('>', '&gt;')}</div>
</div>
"""
st.markdown(quiz_card_html, unsafe_allow_html=True)

if tts_method == "Google TTS (st.audio)":
    if ukrainian_word:
        # Cache audio by question word to prevent regeneration
        audio_cache_key = f"audio_{ukrainian_word}"

        if audio_cache_key not in st.session_state:
            with st.spinner("Generating audio..."):
                audio_bytes = generate_tts_audio(ukrainian_word)
                st.session_state[audio_cache_key] = audio_bytes
        else:
            audio_bytes = st.session_state[audio_cache_key]

        # Only autoplay once per question
        if "audio_played" not in st.session_state:
            st.session_state.audio_played = False

        # NEVER autoplay on rerun (button clicks), only on new question
        should_autoplay = auto_play and not st.session_state.audio_played

        if audio_bytes:
            # Use start_time=0 and key to prevent replay on rerun
            st.audio(audio_bytes, format="audio/mp3", autoplay=should_autoplay, start_time=0)
            if should_autoplay:
                st.session_state.audio_played = True

# Display feedback from the previous question submission, if any
if st.session_state.get("raw_feedback"):
    feedback_html = f'''
    <div style="
        font-size: 11pt;
        line-height: 1.6;
        margin: 1.5rem 0;
        padding: 16px 20px;
        background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
        border-left: 4px solid #4299e1;
        border-radius: 8px;
        color: #e2e8f0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    ">
        <div style="font-weight: 600; color: #90cdf4; margin-bottom: 8px;">💡 AI 피드백</div>
        <div style="color: #cbd5e0;">{st.session_state.raw_feedback}</div>
    </div>
    '''
    st.markdown(feedback_html, unsafe_allow_html=True)

num_choices = len(st.session_state.quiz_options) if mode_meta["type"] == "mc" else 0

# MC question with clickable buttons for keyboard shortcuts
if mode_meta["type"] == "mc":
    choices = [opt.get(mode_meta["field"], "") for opt in st.session_state.quiz_options]

    # Create clickable choice buttons
    for idx, choice in enumerate(choices):
        is_selected = st.session_state.selected_choice_idx == idx
        button_style = "primary" if is_selected else "secondary"

        if st.button(
            f"{idx+1}. {choice}",
            key=f"choice_{idx}",
            use_container_width=True,
            type=button_style,
        ):
            process_answer(choice, selected_idx=idx)
else:
    st.text_input(
        "우크라이나어로 정답 입력",
        key="quiz_text_answer",
        on_change=handle_text_answer_submit,
    )

answer_state = st.session_state.get("answer_state")
if answer_state:
    if answer_state.get("is_correct"):
        st.success("✅ 정답입니다!")
    else:
        expected_answer = answer_state.get("expected") or "—"
        st.error(f"❌ 아쉽네요! 정답은 **{expected_answer}** 입니다.")

next_clicked = st.button(
    "▶️ Next [Space]",
    use_container_width=True,
    type="primary",
    key="next_primary",
)
if next_clicked:
    if not st.session_state.get("answer_revealed"):
        if mode_meta["type"] == "mc":
            st.warning("정답을 선택하세요!")
        else:
            pending_answer = st.session_state.get("quiz_text_answer", "").strip()
            if pending_answer:
                process_answer(pending_answer)
            else:
                st.warning("정답을 입력하세요!")
    else:
        handle_next_question()

col_pass, col_skip = st.columns(2)
with col_pass:
    st.button(
        "📖 Pass [P]",
        on_click=handle_pass_and_add_to_review,
        use_container_width=True,
        help="복습 단어장에 추가하고 다음으로",
        key="pass_bottom",
    )
with col_skip:
    st.button("⏭️ Skip", on_click=handle_skip_question, use_container_width=True, help="그냥 넘어가기", key="skip_bottom")

# JavaScript for TTS only - shortcuts handled by streamlit-shortcuts
js_code = f"""
<script>
(function() {{
    // TTS function for browser built-in speech synthesis
    function speakUkrainian(word) {{
        if (!word || !('speechSynthesis' in window)) return;
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(word);
        const voices = window.speechSynthesis.getVoices();
        const ukrainianVoice = voices.find(v => v.lang.startsWith('uk') || v.lang.startsWith('ru'));
        if (ukrainianVoice) utterance.voice = ukrainianVoice;
        utterance.lang = 'uk-UA';
        utterance.rate = 0.9;
        window.speechSynthesis.speak(utterance);
    }}

    // Initialize voices
    if ('speechSynthesis' in window) {{
        window.speechSynthesis.onvoiceschanged = () => window.speechSynthesis.getVoices();
        window.speechSynthesis.getVoices();
    }}

    // TTS button click handler
    function initializeTTS() {{
        const bodyElement = document.body || document.querySelector('body');
        if (!bodyElement) return;

        bodyElement.addEventListener('click', function(e) {{
            const ttsButton = e.target.closest('.tts-button');
            if (ttsButton) {{
                const word = ttsButton.getAttribute('data-word-to-speak');
                if (word) {{
                    speakUkrainian(word);
                    e.preventDefault();
                }}
            }}
        }}, true);
    }}

    // Initialize handlers
    if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', initializeTTS);
    }} else {{
        initializeTTS();
    }}
}})();
</script>
"""
st.markdown(js_code, unsafe_allow_html=True)

st.markdown(
    '<div id="slava-shortcut-status" style="font-size: 0.7rem; color: #A0AEC0; text-align: right; min-height: 1rem;"></div>',
    unsafe_allow_html=True,
)

keyboard_js = f"""
<script>
(function() {{
    const isMultipleChoice = {str(mode_meta["type"] == "mc").lower()};
    const numChoices = {num_choices};
    const keyToTargets = new Map();

    keyToTargets.set(" ", ["next_primary"]);
    keyToTargets.set("Space", ["next_primary"]);
    keyToTargets.set("Spacebar", ["next_primary"]);
    keyToTargets.set("ArrowRight", ["next_primary"]);
    keyToTargets.set("p", ["pass_bottom"]);
    keyToTargets.set("P", ["pass_bottom"]);

    if (isMultipleChoice) {{
        for (let idx = 0; idx < numChoices; idx++) {{
            const choiceKey = `choice_${{idx}}`;
            keyToTargets.set(String(idx + 1), [choiceKey]);
            keyToTargets.set(`Numpad${{idx + 1}}`, [choiceKey]);
            keyToTargets.set(`Digit${{idx + 1}}`, [choiceKey]);
        }}
    }}

    const previousHandler = window.__slavaTalkShortcutListener;
    if (previousHandler) {{
        document.removeEventListener("keydown", previousHandler);
        window.removeEventListener("keydown", previousHandler);
    }}

    function isInteractiveElement(el) {{
        if (!el) {{
            return false;
        }}
        const tag = el.tagName?.toLowerCase();
        if (tag === "button") {{
            return true;
        }}
        if (tag === "input" && !["hidden", "file"].includes((el.type || "").toLowerCase())) {{
            return true;
        }}
        const role = el.getAttribute?.("role");
        if (role && ["button", "option", "radio"].includes(role.toLowerCase())) {{
            return true;
        }}
        return false;
    }}

    function collectCandidates(targetKey) {{
        const selectors = [
            `.st-key-${{targetKey}}`,
            `[data-testid="${{targetKey}}"]`,
            `[data-testid="baseButton-${{targetKey}}"]`,
            `[aria-controls="${{targetKey}}"]`,
            `[aria-labelledby="${{targetKey}}"]`,
            `[aria-label="${{targetKey}}"]`,
        ];

        const nodes = new Set();
        selectors.forEach(selector => {{
            document.querySelectorAll(selector).forEach(node => nodes.add(node));
        }});
        document.querySelectorAll(`[class*="st-key-${{targetKey}}"]`).forEach(node => nodes.add(node));
        return Array.from(nodes);
    }}

    function findTargetElement(targetKey) {{
        const candidates = collectCandidates(targetKey);
        for (const candidate of candidates) {{
            if (isInteractiveElement(candidate)) {{
                return candidate;
            }}
        }}
        for (const candidate of candidates) {{
            const interactiveDescendant = candidate.querySelector?.("button, [role='button'], input, textarea");
            if (isInteractiveElement(interactiveDescendant)) {{
                return interactiveDescendant;
            }}
        }}
        for (const candidate of candidates) {{
            let parent = candidate.parentElement;
            while (parent) {{
                if (isInteractiveElement(parent)) {{
                    return parent;
                }}
                parent = parent.parentElement;
            }}
        }}
        return null;
    }}

    function updateStatus(message) {{
        const status = document.getElementById("slava-shortcut-status");
        if (!status) {{
            return;
        }}
        status.innerText = message;
    }}

    const handler = function(event) {{
        if (event.defaultPrevented) {{
            return;
        }}

        if (event.ctrlKey || event.altKey || event.metaKey) {{
            return;
        }}

        const activeElement = document.activeElement;
        const tagName = activeElement ? activeElement.tagName.toLowerCase() : "";
        const activeType = activeElement ? (activeElement.type || "").toLowerCase() : "";
        const textInputTypes = ["text", "search", "password", "email", "url", "tel"];
        const isTyping = tagName === "textarea" || (tagName === "input" && textInputTypes.includes(activeType));

        if (isTyping && event.key !== "Enter") {{
            return;
        }}

        const key = event.key || event.code;
        const targets =
            keyToTargets.get(key) ||
            keyToTargets.get(event.code) ||
            keyToTargets.get(event.key?.toLowerCase?.()) ||
            keyToTargets.get(event.code?.toLowerCase?.());

        if (!targets) {{
            console.debug("SlavaTalk shortcut ignored (no mapping)", {{
                key: event.key,
                code: event.code,
                isTyping,
            }});
            if (!isTyping) {{
                updateStatus(`Shortcut unmapped: key=${{event.key}} code=${{event.code}}`);
            }}
            return;
        }}

        for (const targetKey of targets) {{
            const element = findTargetElement(targetKey);
            if (element) {{
                event.preventDefault();
                if (typeof element.click === "function") {{
                    element.click();
                }} else {{
                    element.dispatchEvent(new MouseEvent("click", {{ bubbles: true }}));
                }}
                if (element.focus) {{
                    element.focus({{preventScroll: true}});
                }}
                console.debug("SlavaTalk shortcut handled", {{
                    key: event.key,
                    code: event.code,
                    targetKey,
                    elementTag: element.tagName,
                }});
                updateStatus(`Shortcut handled: ${{event.key || event.code}} -> ${{targetKey}}`);
                return;
            }}
        }}
        console.warn("SlavaTalk shortcut target not found", {{
            key: event.key,
            code: event.code,
            targets,
        }});
        updateStatus(`Shortcut target missing: ${{event.key || event.code}}`);
    }};

    window.__slavaTalkShortcutListener = handler;
    document.addEventListener("keydown", handler, {{ passive: false }});
    window.addEventListener("keydown", handler, {{ passive: false }});
    console.info("SlavaTalk keyboard shortcuts ready", {{
        isMultipleChoice,
        numChoices,
        mappedKeys: Array.from(keyToTargets.keys()),
    }});
    updateStatus("Shortcuts ready");
}})();
</script>
"""
st.markdown(keyboard_js, unsafe_allow_html=True)
