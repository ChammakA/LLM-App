import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
embedder = SentenceTransformer(EMBED_MODEL)

def chunk_text(text, chunk_size=500):
    """Split text into chunks with some overlap."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunks.append(" ".join(words[i:i + chunk_size]))
    return chunks

def load_notes(folder="notes"):
    docs = []
    sources = []
    for f in os.listdir(folder):
        if f.endswith(".md") or f.endswith(".txt"):
            text = open(os.path.join(folder, f), encoding="utf-8").read()
            for chunk in chunk_text(text):
                docs.append(chunk)
                sources.append(f)
    return docs, sources

def build_index(docs):
    embeddings = embedder.encode(docs, show_progress_bar=True, convert_to_numpy=True)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    return index, embeddings

def search_index(query, index, docs, sources, k=3):
    query_embedding = embedder.encode([query], convert_to_numpy=True)
    distance, indices = index.search(query_embedding, k)
    results = []
    for idx in indices[0]:
        results.append((docs[idx], sources[idx]))
    return results