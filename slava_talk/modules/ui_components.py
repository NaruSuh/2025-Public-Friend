import streamlit as st
from typing import Dict
import io

try:
    from gtts import gTTS
except ImportError:
    gTTS = None

def apply_custom_css():
    """Applies the custom CSS file to the Streamlit app."""
    try:
        with open("assets/style.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("assets/style.css not found. Using default styles.")

def render_hero_section(title: str, subtitle: str):
    """Renders a prominent hero section with a title and subtitle."""
    hero_html = f"""
    <div class="hero-section">
        <div class="hero-title">{title}</div>
        <div class="hero-subtitle">{subtitle}</div>
    </div>
    """
    st.markdown(hero_html, unsafe_allow_html=True)

def render_vocab_card(item: Dict, index: int, tts_method: str, auto_play: bool):
    """
    Renders a single vocabulary item as a styled card with a functional TTS button.
    The key for the button is made unique by using the index.
    """
    st.markdown(f'<div class="vocab-card">', unsafe_allow_html=True)

    col1, col2 = st.columns([4, 1])

    with col1:
        st.markdown(f'<div class="ukrainian-text">🇺🇦 {item.get("ukrainian", "N/A")}</div>'
                    f'<div class="pronunciation">🔊 {item.get("pronunciation", "N/A")}</div>', unsafe_allow_html=True)

    with col2:
        if gTTS and st.button("발음 듣기", key=f"tts_{item.get('ukrainian')}_{index}", use_container_width=True):
            try:
                tts = gTTS(text=item['ukrainian'], lang='uk')
                mp3_fp = io.BytesIO()
                tts.write_to_fp(mp3_fp)
                mp3_fp.seek(0)
                st.audio(mp3_fp, format='audio/mp3')
            except Exception as e:
                st.error(f"음성 생성 중 오류 발생: {e}")

    st.markdown('<hr style="margin: 10px 0;">', unsafe_allow_html=True)

    st.markdown(f'<div class="translation-text"><b>🇰🇷 한국어:</b> {item.get("korean", "N/A")}</div>'
                f'<div class="translation-text"><b>🇬🇧 영어:</b> {item.get("english", "N/A")}</div>', unsafe_allow_html=True)

    topics = item.get("topic")
    if topics:
        if isinstance(topics, list):
            tags_html = ''.join([f'<span class="topic-tag">{topic}</span>' for topic in topics])
        else:
            tags_html = f'<span class="topic-tag">{topics}</span>'
        st.markdown(f'<div class="topic-tag-container">{tags_html}</div>', unsafe_allow_html=True)

    example_ukr = item.get("example_sentence_ukr")
    if example_ukr:
        example_eng = item.get("example_sentence_eng", "")
        example_kor = item.get("example_sentence_kor", "")

        eng_html = f'<div style="margin-top: 6px; color: #999;">{example_eng}</div>' if example_eng else ""
        kor_html = f'<div style="margin-top: 6px; color: #999;">{example_kor}</div>' if example_kor else ""

        example_html = f'''
        <div class="example-box">
            <div><b>예문:</b> {example_ukr}</div>
            {eng_html}
            {kor_html}
        </div>
        '''
        st.markdown(example_html, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

def render_streak_display(streak: int):
    """Renders the current streak count in a styled box."""
    if streak > 0:
        emoji = "🔥" * min(streak // 2 + 1, 5)
        html = f"""
        <div class="streak-display">
            <div class="streak-emoji">{emoji}</div>
            <div class="streak-text">{streak} 연속 정답!</div>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)

def render_progress_bar(score: int, total: int, label: str):
    """Renders a custom progress bar with a label."""
    st.markdown(f"**{label}**")
    progress_value = (score / total) if total > 0 else 0
    st.progress(progress_value)


def render_ai_lesson(lesson: Dict) -> None:
    """
    Render AI-generated lesson with flashcards, drills, and mission briefs.

    Args:
        lesson: AI-generated lesson dictionary with keys: flashcards, drills, mission_briefs, recommendations
    """
    flashcards = lesson.get("flashcards", [])
    drills = lesson.get("drills", [])
    briefs = lesson.get("mission_briefs", [])

    if flashcards:
        st.markdown("#### 📇 플래시카드")
        for card in flashcards:
            if isinstance(card, dict):
                prompt = card.get('prompt', card.get('ukrainian', card.get('front', '')))
                answer = card.get('answer', card.get('korean', card.get('back', '')))
                st.markdown(f"- **{prompt}** → {answer}")
            else:
                st.markdown(f"- {card}")
    else:
        st.info("플래시카드가 생성되지 않았습니다.")

    if drills:
        st.markdown("#### 🎯 연습 문제")
        for idx, drill in enumerate(drills, start=1):
            if isinstance(drill, dict):
                title = drill.get('drill_title', drill.get('title', f'연습 {idx}'))
                context = drill.get('context', '')
                instructions = drill.get('instructions', drill.get('description', drill.get('text', '')))

                st.markdown(f"**{idx}. {title}**")
                if context:
                    st.markdown(f"   - 상황: {context}")
                if instructions:
                    st.markdown(f"   - 지시사항: {instructions}")
            else:
                st.markdown(f"{idx}. {drill}")
    else:
        st.info("연습 문제가 생성되지 않았습니다.")

    if briefs:
        st.markdown("#### 🎖️ 실전 미션")
        for idx, brief in enumerate(briefs, start=1):
            if isinstance(brief, dict):
                scenario = brief.get('scenario', brief.get('summary', brief.get('description', brief.get('text', ''))))
                title = brief.get('title', f'미션 {idx}')

                if 'title' in brief:
                    st.markdown(f"**{title}**")
                    st.markdown(f"- {scenario}")
                else:
                    st.markdown(f"- {scenario}")
            else:
                st.markdown(f"- {brief}")
    else:
        st.info("실전 미션이 생성되지 않았습니다.")

    recommendations = lesson.get("recommendations", "")
    if recommendations:
        st.info(f"💡 추천: {recommendations}")
