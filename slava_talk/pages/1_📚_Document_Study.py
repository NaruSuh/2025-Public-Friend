import streamlit as st
from modules.data_loader import load_vocab

st.set_page_config(
    page_title="Document Study - SlavaTalk",
    page_icon="📚",
    layout="wide"
)

st.title("📚 Document-Based Vocabulary Study")

vocabulary = load_vocab()

if not vocabulary:
    st.error("Vocabulary data could not be loaded. Please check the data file.")
else:
    # --- Sidebar for filtering ---
    st.sidebar.header("Filter Options")
    
    # Get unique source documents for the filter
    doc_sources = sorted(list(set(item['source_doc'] for item in vocabulary)))
    doc_sources.insert(0, "All Documents")

    selected_doc = st.sidebar.selectbox(
        "Select a Source Document:",
        options=doc_sources
    )

    # --- Display Vocabulary ---
    if selected_doc == "All Documents":
        filtered_vocab = vocabulary
    else:
        filtered_vocab = [item for item in vocabulary if item['source_doc'] == selected_doc]

    if not filtered_vocab:
        st.warning("No vocabulary found for the selected filter.")
    else:
        st.info(f"Displaying **{len(filtered_vocab)}** words from **{selected_doc}**.")
        
        for item in filtered_vocab:
            expander_title = f"**{item['ukrainian']}**  *({item['pronunciation']})*"
            with st.expander(expander_title):
                st.markdown(f"- **Korean:** {item['korean']}")
                st.markdown(f"- **English:** {item['english']}")
                st.markdown("---")
                st.markdown("**Example Sentence (from document):**")
                st.markdown(f"> *{item['example_sentence_ukr']}*")
                st.markdown(f"> *{item['example_sentence_eng']}*" )
                st.markdown(f"<p style='text-align: right; color: grey; font-size: small;'>Source: {item['source_doc']}</p>", unsafe_allow_html=True)
