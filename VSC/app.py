import json
from pathlib import Path

import streamlit as st
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader

from model_provider import (
    build_embeddings,
    build_llm,
    get_chat_model_name,
    get_embedding_model_name,
    get_missing_api_key_message,
    has_api_key,
    get_ollama_host,
    get_ollama_status_message,
)


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
DOCS_DIR = PROJECT_DIR / "docs"
DB_DIR = BASE_DIR / "db"
INDEXES_DIR = DB_DIR / "indexes"
ACTIVE_INDEX_FILE = DB_DIR / "active_index.txt"
INDEX_METADATA_FILE = "index_metadata.json"
SAMPLE_QUESTIONS = [
    "What is ISO 26262 and why is it used in automotive software?",
    "Summarize the coding guideline recommendations for safe software development.",
    "What do the documents say about verification, validation, or testing?",
    "What guidance is given for defensive programming or error handling?",
]

st.set_page_config(
    page_title="Automotive Safety Copilot",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top right, rgba(243, 120, 71, 0.18), transparent 28%),
                radial-gradient(circle at left center, rgba(0, 92, 79, 0.16), transparent 22%),
                linear-gradient(180deg, #f8f3ec 0%, #efe7da 100%);
        }
        .hero-card {
            padding: 1.4rem 1.5rem;
            border-radius: 24px;
            background: rgba(255, 251, 245, 0.86);
            border: 1px solid rgba(85, 60, 40, 0.12);
            box-shadow: 0 18px 40px rgba(80, 53, 25, 0.08);
            margin-bottom: 1rem;
        }
        .eyebrow {
            font-size: 0.8rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: #8b5e34;
            margin-bottom: 0.35rem;
            font-weight: 700;
        }
        .hero-title {
            font-size: 2.2rem;
            line-height: 1.1;
            color: #1f2a24;
            margin: 0;
        }
        .hero-copy {
            color: #4b514d;
            margin-top: 0.6rem;
            margin-bottom: 0;
            font-size: 1rem;
        }
        .metric-strip {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.75rem;
            margin: 1rem 0 0.25rem;
        }
        .metric-card {
            background: rgba(255, 255, 255, 0.82);
            border: 1px solid rgba(85, 60, 40, 0.12);
            border-radius: 18px;
            padding: 0.85rem 1rem;
        }
        .metric-label {
            font-size: 0.72rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #8b5e34;
            margin-bottom: 0.2rem;
            font-weight: 700;
        }
        .metric-value {
            font-size: 1.15rem;
            color: #17201c;
            font-weight: 700;
        }
        .source-chip {
            display: inline-block;
            padding: 0.25rem 0.55rem;
            margin: 0.2rem 0.35rem 0.2rem 0;
            border-radius: 999px;
            background: #e5efe9;
            color: #234235;
            border: 1px solid #bfd1c6;
            font-size: 0.8rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def list_pdf_paths() -> list[Path]:
    return sorted(DOCS_DIR.glob("*.pdf"))


def save_uploaded_files(files: list) -> list[Path]:
    DOCS_DIR.mkdir(exist_ok=True)
    saved_paths = []
    for uploaded_file in files:
        target_path = DOCS_DIR / uploaded_file.name
        with target_path.open("wb") as target:
            target.write(uploaded_file.getbuffer())
        saved_paths.append(target_path)
    return saved_paths


def load_documents() -> tuple[list, list[Path]]:
    pdf_paths = list_pdf_paths()
    documents = []
    for pdf_path in pdf_paths:
        documents.extend(PyPDFLoader(str(pdf_path)).load())
    return documents, pdf_paths


def rebuild_index() -> tuple[int, int]:
    documents, pdf_paths = load_documents()
    if not pdf_paths:
        raise FileNotFoundError("No PDF files found in the docs folder.")

    from datetime import datetime

    embeddings = build_embeddings()

    DB_DIR.mkdir(exist_ok=True)
    INDEXES_DIR.mkdir(exist_ok=True)
    index_name = datetime.now().strftime("%Y%m%d_%H%M%S")
    persist_directory = INDEXES_DIR / index_name

    Chroma.from_documents(documents, embeddings, persist_directory=str(persist_directory))
    (persist_directory / INDEX_METADATA_FILE).write_text(
        json.dumps({"embedding_model": embeddings.model, "provider": "ollama"}, indent=2),
        encoding="utf-8",
    )
    ACTIVE_INDEX_FILE.write_text(index_name, encoding="utf-8")
    get_vector_store.clear()
    return len(pdf_paths), len(documents)


def get_active_db_dir() -> Path:
    if ACTIVE_INDEX_FILE.exists():
        active_index = ACTIVE_INDEX_FILE.read_text(encoding="utf-8").strip()
        active_path = INDEXES_DIR / active_index
        if active_path.exists():
            return active_path

    legacy_db_file = DB_DIR / "chroma.sqlite3"
    if legacy_db_file.exists():
        return DB_DIR

    return DB_DIR


def get_active_index_metadata() -> dict[str, str] | None:
    metadata_path = get_active_db_dir() / INDEX_METADATA_FILE
    if not metadata_path.exists():
        return None

    try:
        return json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def get_index_status() -> tuple[bool, str | None]:
    active_db_dir = get_active_db_dir()
    if not active_db_dir.exists():
        return False, "The vector database is missing. Use the sidebar to rebuild the index."

    metadata = get_active_index_metadata()
    if metadata is None:
        return True, "Using a legacy local index. Rebuild the document index if answers look stale or irrelevant."

    expected_model = get_embedding_model_name()
    if metadata.get("provider") != "ollama" or metadata.get("embedding_model") != expected_model:
        return False, "The active index was built with a different embedding model. Rebuild the document index to match the current deployment configuration."

    return True, None


@st.cache_resource(show_spinner=False)
def get_vector_store() -> Chroma:
    embeddings = build_embeddings()
    return Chroma(persist_directory=str(get_active_db_dir()), embedding_function=embeddings)


@st.cache_resource(show_spinner=False)
def get_llm():
    return build_llm()


def format_sources(documents: list) -> list[dict[str, str]]:
    sources = []
    for document in documents:
        source_name = Path(document.metadata.get("source", "Unknown")).name
        page_number = document.metadata.get("page")
        label = source_name if page_number is None else f"{source_name} - page {page_number + 1}"
        sources.append({"label": label, "content": document.page_content})
    return sources


def ask_question(question: str) -> None:
    if not has_api_key():
        st.error(get_missing_api_key_message())
        return

    ollama_status = get_ollama_status_message()
    if ollama_status:
        st.error(ollama_status)
        return

    index_ready, status_message = get_index_status()
    if not index_ready:
        st.error(status_message)
        return

    with st.spinner("Searching the indexed documents and drafting an answer..."):
        db = get_vector_store()
        docs = db.similarity_search(question, k=4)
        context = "\n\n".join(doc.page_content for doc in docs)
        prompt = f"""
You are an automotive safety and coding standards assistant.
Answer using only the context below.
If the answer is not supported by the context, say that clearly.
Keep the answer concise and practical.

Context:
{context}

Question:
{question}
"""
    response = get_llm().invoke(prompt)
    answer = response.content if hasattr(response, "content") else str(response)

    st.session_state.chat_history.append(
        {
            "question": question,
            "answer": answer,
            "sources": format_sources(docs),
        }
    )


def render_header(pdf_paths: list[Path]) -> None:
    st.markdown(
        f"""
        <div class="hero-card">
            <div class="eyebrow">Safety Knowledge Assistant</div>
            <h1 class="hero-title">Automotive Safety Copilot</h1>
            <p class="hero-copy">
                Search ISO 26262 and your coding guidance as a conversational workspace.
                Ask targeted questions, inspect supporting excerpts, and refresh the index when documents change.
            </p>
            <div class="metric-strip">
                <div class="metric-card">
                    <div class="metric-label">Model</div>
                    <div class="metric-value">{get_chat_model_name()}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Indexed PDFs</div>
                    <div class="metric-value">{len(pdf_paths)}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Chat Turns</div>
                    <div class="metric-value">{len(st.session_state.chat_history)}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(pdf_paths: list[Path]) -> None:
    with st.sidebar:
        st.markdown("## Workspace")
        st.write("Upload PDFs, rebuild the index, and try focused prompts from the sidebar.")
        st.caption(f"Ollama host: {get_ollama_host()}")

        if not has_api_key():
            st.warning(get_missing_api_key_message())

        ollama_status = get_ollama_status_message()
        if ollama_status and has_api_key():
            st.warning(ollama_status)

        _, status_message = get_index_status()
        if status_message and has_api_key():
            st.info(status_message)

        uploaded_files = st.file_uploader(
            "Add PDF documents",
            type=["pdf"],
            accept_multiple_files=True,
        )

        if st.button("Save uploaded PDFs", use_container_width=True):
            if uploaded_files:
                saved = save_uploaded_files(uploaded_files)
                st.success(f"Saved {len(saved)} file(s) into the docs folder.")
            else:
                st.info("Choose one or more PDF files first.")

        if st.button("Rebuild document index", use_container_width=True):
            try:
                pdf_count, chunk_count = rebuild_index()
                st.success(f"Indexed {pdf_count} PDFs into {chunk_count} chunks.")
            except Exception as error:
                st.error(str(error))
            else:
                st.rerun()

        if st.button("Clear chat history", use_container_width=True):
            st.session_state.chat_history = []
            st.success("Chat history cleared.")

        st.markdown("### Available documents")
        if pdf_paths:
            for pdf_path in pdf_paths:
                st.write(f"- {pdf_path.name}")
        else:
            st.warning("No PDFs found in the docs folder.")

        st.markdown("### Sample questions")
        for index, question in enumerate(SAMPLE_QUESTIONS):
            if st.button(question, key=f"sample-{index}", use_container_width=True):
                st.session_state.pending_question = question


def render_chat() -> None:
    if not st.session_state.chat_history:
        st.info("Ask a question or pick a sample prompt to start the conversation.")
        return

    for item in st.session_state.chat_history:
        with st.chat_message("user"):
            st.write(item["question"])

        with st.chat_message("assistant"):
            st.write(item["answer"])
            if item["sources"]:
                st.markdown("**Sources**")
                chips = "".join(
                    f'<span class="source-chip">{source["label"]}</span>'
                    for source in item["sources"]
                )
                st.markdown(chips, unsafe_allow_html=True)
                with st.expander("Show supporting excerpts"):
                    for source in item["sources"]:
                        st.markdown(f"**{source['label']}**")
                        st.write(source["content"])


def main() -> None:
    inject_styles()
    DOCS_DIR.mkdir(exist_ok=True)

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "pending_question" not in st.session_state:
        st.session_state.pending_question = None

    pdf_paths = list_pdf_paths()
    render_sidebar(pdf_paths)
    render_header(pdf_paths)
    render_chat()

    prompt = st.chat_input("Ask about ISO 26262, coding practices, testing, or your uploaded PDFs")
    active_question = prompt or st.session_state.pending_question

    if active_question:
        ask_question(active_question)
        st.session_state.pending_question = None
        st.rerun()


if __name__ == "__main__":
    main()