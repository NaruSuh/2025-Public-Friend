import streamlit as st
import random
from modules.data_loader import load_vocab

st.set_page_config(
    page_title="Quiz - SlavaTalk",
    page_icon="❓",
    layout="centered"
)

st.title("❓ Vocabulary Quiz")

vocabulary = load_vocab()

# Initialize session state variables if they don't exist
if 'quiz_word' not in st.session_state:
    st.session_state.quiz_word = None
    st.session_state.options = []
    st.session_state.score = 0
    st.session_state.question_count = 0
    st.session_state.answered = False

def generate_new_question():
    """Selects a new word and generates multiple-choice options."""
    # Select a random word from the vocabulary
    correct_word = random.choice(vocabulary)
    st.session_state.quiz_word = correct_word

    # Get 3 other random words for incorrect options
    options = [correct_word]
    while len(options) < 4:
        option = random.choice(vocabulary)
        if option not in options:
            options.append(option)
    
    random.shuffle(options)
    st.session_state.options = options
    st.session_state.answered = False

# --- Main App Logic ---
if not vocabulary:
    st.error("Vocabulary data could not be loaded. Cannot start quiz.")
else:
    # Generate the first question if the quiz hasn't started
    if st.session_state.quiz_word is None:
        generate_new_question()

    # Display Score
    st.subheader(f"Score: {st.session_state.score} / {st.session_state.question_count}")
    st.markdown("---")

    # Display the question
    question_word = st.session_state.quiz_word
    if question_word:
        st.markdown(f"### What is the meaning of the word: **`{question_word['ukrainian']}`**?", unsafe_allow_html=True)
        st.markdown(f"*(Pronunciation: {question_word['pronunciation']})*", unsafe_allow_html=True)
        
        # Use a form to handle the submission
        with st.form(key='quiz_form'):
            # The options are displayed as radio buttons
            user_answer = st.radio(
                "Choose your answer:",
                options=[opt['korean'] for opt in st.session_state.options],
                index=None # No default selection
            )
            
            submit_button = st.form_submit_button("Submit Answer")

            if submit_button:
                if user_answer:
                    st.session_state.answered = True
                    st.session_state.question_count += 1
                    if user_answer == question_word['korean']:
                        st.session_state.score += 1
                        st.success("Correct! ✅")
                    else:
                        st.error(f"Incorrect. ❌ The correct answer is: **{question_word['korean']}**")
                    st.info(f"**Example:** *{question_word['example_sentence_ukr']}*\n> *{question_word['example_sentence_eng']}*", icon="ℹ️")
                else:
                    st.warning("Please select an answer before submitting.")

    # --- Buttons for control ---
    col1, col2 = st.columns([1, 5])

    with col1:
        if st.button("Next Question ➡️"):
            if not st.session_state.answered and st.session_state.question_count > 0:
                st.toast("Please answer the current question first!")
            else:
                generate_new_question()
                st.rerun()

    with col2:
        if st.button("Reset Quiz"):
            st.session_state.quiz_word = None
            st.session_state.options = []
            st.session_state.score = 0
            st.session_state.question_count = 0
            st.session_state.answered = False
            st.rerun()
