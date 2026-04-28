import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from transformers import pipeline

# Load embeddings + vector DB
embeddings = HuggingFaceEmbeddings()
db = FAISS.load_local("vectorstore", embeddings, allow_dangerous_deserialization=True)

# Load lightweight local model
generator = pipeline("text-generation", model="distilgpt2")

st.title("🚗 Automotive AI Chatbot")

query = st.text_input("Ask your question:")

if query:
    # Retrieve relevant docs
    docs = db.similarity_search(query, k=3)
    context = "\n\n".join([doc.page_content for doc in docs])

    prompt = f"""
You are an expert in automotive software and ISO 26262.

Context:
{context}

Question:
{query}

Answer clearly with explanation and example:
"""

    # Generate response
    result = generator(prompt, max_length=300, num_return_sequences=1)

    # Show answer
    st.write(result[0]["generated_text"])