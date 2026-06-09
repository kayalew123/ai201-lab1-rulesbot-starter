"""
ingest.py — Document ingestion and chunking pipeline
Loads .txt files from the documents/ folder, cleans them, and splits into chunks.
"""

import os
import re
from langchain_text_splitters import RecursiveCharacterTextSplitter


def load_documents(docs_dir="documents"):
    documents = []
    if not os.path.exists(docs_dir):
        raise FileNotFoundError(f"Documents directory '{docs_dir}' not found.")

    for filename in os.listdir(docs_dir):
        if filename.endswith(".txt"):
            filepath = os.path.join(docs_dir, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                raw_text = f.read()
            cleaned = clean_text(raw_text)
            if cleaned.strip():
                documents.append({
                    "text": cleaned,
                    "source": filename
                })
                print(f"Loaded: {filename} ({len(cleaned)} chars)")

    print(f"\nTotal documents loaded: {len(documents)}")
    return documents


def clean_text(text):
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'&\w+;', ' ', text)
    lines = text.splitlines()
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if len(stripped) > 20 or stripped.startswith(('Q:', 'A:', 'Source:', 'POST:', 'COMMENTS:')):
            cleaned_lines.append(stripped)
    text = "\n".join(cleaned_lines)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def chunk_documents(documents, chunk_size=400, chunk_overlap=80):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    all_chunks = []
    for doc in documents:
        chunks = splitter.split_text(doc["text"])
        for i, chunk in enumerate(chunks):
            if len(chunk.strip()) >= 50:
                all_chunks.append({
                    "text": chunk.strip(),
                    "source": doc["source"],
                    "chunk_index": i
                })

    print(f"Total chunks produced: {len(all_chunks)}")
    return all_chunks


def inspect_chunks(chunks, n=5):
    import random
    sample = random.sample(chunks, min(n, len(chunks)))
    print("\n--- CHUNK INSPECTION ---")
    for i, chunk in enumerate(sample):
        print(f"\nChunk {i+1} (source: {chunk['source']}, index: {chunk['chunk_index']}):")
        print(f"Length: {len(chunk['text'])} chars")
        print(f"Text: {chunk['text']}")
        print("-" * 60)


if __name__ == "__main__":
    documents = load_documents("documents")
    chunks = chunk_documents(documents)
    inspect_chunks(chunks, n=5)