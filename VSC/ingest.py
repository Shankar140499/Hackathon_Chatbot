import json
from datetime import datetime
from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader

from model_provider import build_embeddings


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
DOCS_DIR = PROJECT_DIR / "docs"
DB_DIR = BASE_DIR / "db"
INDEXES_DIR = DB_DIR / "indexes"
ACTIVE_INDEX_FILE = DB_DIR / "active_index.txt"
INDEX_METADATA_FILE = "index_metadata.json"


def load_documents() -> tuple[list, list[Path]]:
    pdf_paths = sorted(DOCS_DIR.glob("*.pdf"))
    documents = []
    for pdf_path in pdf_paths:
        documents.extend(PyPDFLoader(str(pdf_path)).load())
    return documents, pdf_paths


def build_index() -> tuple[int, int]:
	documents, pdf_paths = load_documents()
	if not pdf_paths:
		raise FileNotFoundError(f"No PDF files found in {DOCS_DIR}")

	embeddings = build_embeddings()

	DB_DIR.mkdir(exist_ok=True)
	INDEXES_DIR.mkdir(exist_ok=True)
	index_name = datetime.now().strftime("%Y%m%d_%H%M%S")
	persist_directory = INDEXES_DIR / index_name

	Chroma.from_documents(documents, embeddings, persist_directory=str(persist_directory))
	(persist_directory / INDEX_METADATA_FILE).write_text(
		json.dumps({"embedding_model": embeddings.model, "provider": "openai"}, indent=2),
		encoding="utf-8",
	)
	ACTIVE_INDEX_FILE.write_text(index_name, encoding="utf-8")
	return len(pdf_paths), len(documents)


if __name__ == "__main__":
    pdf_count, chunk_count = build_index()
    print(
        f"Documents indexed successfully! Indexed {pdf_count} PDF files into {chunk_count} chunks."
    )