import streamlit as st

st.set_page_config(
    page_title="SlavaTalk - Home",
    page_icon="🇺🇦",
    layout="wide"
)

st.title("Welcome to SlavaTalk! 🇺🇦")
st.subheader("A Language Learning App for Ukraine's Reconstruction Professionals")

st.markdown("""
**SlavaTalk** is a simple, stable, and modular language learning application designed to help government and intelligence professionals quickly acquire the essential Ukrainian vocabulary needed for the reconstruction efforts in Ukraine.

This app is based on key documents related to Ukraine's recovery, ensuring that you learn the words and phrases that are most relevant to your mission.

### How to Use:

1.  Navigate to the **📚 Document Study** page using the sidebar on the left.
2.  Select a source document to see the key vocabulary extracted from it.
3.  Review the words, their meanings, and the context in which they were used.
4.  Once you feel confident, go to the **❓ Quiz** page to test your knowledge.

*This application is currently in its initial development phase. The vocabulary is based on a sample set. The full vocabulary will be expanded by processing the source PDF documents.* 

Select a page from the sidebar to get started.
""")
