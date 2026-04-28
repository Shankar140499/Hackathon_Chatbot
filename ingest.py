from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

# Load documents
loader1 = PyPDFLoader("docs/iso26262.pdf")
loader2 = PyPDFLoader("docs/coding_guidelines.pdf")

docs = loader1.load() + loader2.load()

# Split into chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100
)
texts = text_splitter.split_documents(docs)

# Create vector DB
embeddings = OpenAIEmbeddings()
db = FAISS.from_documents(texts, embeddings)

# Save DB
db.save_local("vectorstore")

print("✅ Documents processed!")