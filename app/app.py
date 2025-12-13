import streamlit as st
from pathlib import Path
from edumentor.config import settings
from edumentor.ingest.ingest import ingest_pdf, save_uploaded
from edumentor.retrieval.vectorstore import VectorStore
from edumentor.intent.classifier import detect_intent
from edumentor.llm.providers import LLM


# -----------------------------
# Page config
# -----------------------------
st.set_page_config(page_title="EduMentor AI", layout="wide")

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.title("EduMentor AI")

exam_focus = st.sidebar.selectbox(
    "Exam Focus",
    ["JEE Main", "JEE Advanced", "NEET"],
    index=0
)

top_k = st.sidebar.slider(
    "Retrieved Snippets",
    1, 10, 5
)

if not settings.google_api_key:
    st.sidebar.warning("Add your API key in the .env file and restart the app.")

# -----------------------------
# PDF Upload (FAISS-safe)
# -----------------------------
uploaded = st.sidebar.file_uploader(
    "Upload PDFs (Upload once, reused automatically)",
    type=["pdf"],
    accept_multiple_files=True
)

if uploaded:
    # ✅ FIX HERE
    with st.spinner("Processing PDFs and building knowledge base..."):
        for u in uploaded:
            path = save_uploaded(u.name, u.getvalue())
            ingest_pdf(Path(path))
    st.sidebar.success("PDFs processed and stored successfully.")

# -----------------------------
# Initialize core components
# -----------------------------
llm = LLM()
vs = VectorStore("edumentor")   # FAISS-backed vector store

# -----------------------------
# Main UI
# -----------------------------
st.title("Agentic Tutoring for JEE/NEET")

css = """
<style>
.answer-card {background:#ffffff;border:1px solid #e5e7eb;border-radius:12px;padding:16px;box-shadow:0 2px 8px rgba(0,0,0,0.04);} 
.section-title {font-weight:600;margin-top:8px;margin-bottom:6px;color:#111827;} 
.chip {display:inline-block;background:#F5F7FA;border:1px solid #e5e7eb;border-radius:999px;padding:4px 10px;margin:3px;color:#374151;font-size:12px;} 
.prompt {font-size:16px}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    q = st.text_area(
        "Your question",
        height=160,
        placeholder="Ask a concept, definition, derivation, or numerical problem"
    )
    run = st.button("Generate Answer", type="primary")

with col2:
    with st.expander("How this works"):
        st.write("• Upload PDFs once")
        st.write("• Content is embedded & stored using FAISS")
        st.write("• Ask unlimited questions without re-uploading")

# -----------------------------
# Query + Answer
# -----------------------------
if run and q.strip():
    intent = detect_intent(q)

    with st.spinner("Searching study material..."):
        contexts = vs.query(q, top_k=top_k)

    answer = llm.generate(q, contexts, intent, exam_focus)

    st.markdown(
        f"<div class='answer-card'>{answer}</div>",
        unsafe_allow_html=True
    )

    if contexts:
        st.subheader("Retrieved Sources")
        for c in contexts:
            m = c.get("metadata", {})
            st.markdown(
                f"<span class='chip'>{m.get('title','')} | p.{m.get('page','')}</span>",
                unsafe_allow_html=True
            )
else:
    st.info("Upload PDFs once and ask questions anytime.")
