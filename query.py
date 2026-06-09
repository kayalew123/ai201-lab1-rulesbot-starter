"""
query.py — Retrieval and grounded generation pipeline
"""

import os
from dotenv import load_dotenv
import chromadb
from sentence_transformers import SentenceTransformer
from groq import Groq

load_dotenv()

COLLECTION_NAME = "umd_dining"
CHROMA_PATH = "./chroma_db"
TOP_K = 5

_model = None
_collection = None
_groq_client = None


def get_embedding_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection = client.get_collection(COLLECTION_NAME)
    return _collection


def get_groq_client():
    global _groq_client
    if _groq_client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in .env file.")
        _groq_client = Groq(api_key=api_key)
    return _groq_client


def retrieve(query, k=TOP_K):
    model = get_embedding_model()
    collection = get_collection()

    query_embedding = model.encode([query]).tolist()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=k,
        include=["documents", "metadatas", "distances"]
    )

    chunks = []
    for i in range(len(results["documents"][0])):
        chunks.append({
            "text": results["documents"][0][i],
            "source": results["metadatas"][0][i]["source"],
            "distance": results["distances"][0][i]
        })
    return chunks


def generate(query, chunks):
    client = get_groq_client()

    context_parts = []
    for i, chunk in enumerate(chunks):
        context_parts.append(f"[Source {i+1}: {chunk['source']}]\n{chunk['text']}")
    context = "\n\n".join(context_parts)

    system_prompt = """You are a helpful assistant for University of Maryland students with questions about campus dining halls.

Answer the user's question using ONLY the information provided in the documents below.
Do NOT use any outside knowledge or general information not present in the provided documents.
Always cite which source(s) your answer comes from using the source labels provided (e.g., "According to [Source 1: filename]...").
If the provided documents do not contain enough information to answer the question, say exactly: "I don't have enough information in my documents to answer that question."
Be specific and helpful. If multiple sources provide relevant information, synthesize them."""

    user_prompt = f"""Documents:
{context}

Question: {query}

Answer (cite your sources):"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.1,
        max_tokens=600
    )

    return response.choices[0].message.content


def ask(question):
    chunks = retrieve(question)
    answer = generate(question, chunks)
    sources = list(dict.fromkeys([chunk["source"] for chunk in chunks]))
    return {
        "answer": answer,
        "sources": sources,
        "chunks": chunks
    }


if __name__ == "__main__":
    test_questions = [
        "Have students reported vegetarian food being mislabeled at UMD dining halls?",
        "What allergen-free options does UMD dining offer for students with food allergies?",
        "Which UMD dining hall gets the most crowded during peak hours?",
    ]

    for q in test_questions:
        print(f"\nQ: {q}")
        result = ask(q)
        print(f"A: {result['answer']}")
        print(f"Sources: {result['sources']}")
        print("=" * 70)