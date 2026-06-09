import chromadb
from sentence_transformers import SentenceTransformer
from ingest import load_documents, chunk_documents

COLLECTION_NAME = "umd_dining"
CHROMA_PATH = "./chroma_db"

def get_collection(reset=False):
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
            print(f"Deleted existing collection: {COLLECTION_NAME}")
        except Exception:
            pass
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )
    return collection

def embed_and_store(chunks, reset=True):
    print("Loading embedding model: all-MiniLM-L6-v2...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    collection = get_collection(reset=reset)
    texts = [chunk["text"] for chunk in chunks]
    metadatas = [{"source": chunk["source"], "chunk_index": chunk["chunk_index"]} for chunk in chunks]
    ids = [f"{chunk['source']}_{chunk['chunk_index']}" for chunk in chunks]
    print(f"Embedding {len(texts)} chunks...")
    embeddings = model.encode(texts, show_progress_bar=True).tolist()
    batch_size = 100
    for i in range(0, len(texts), batch_size):
        collection.add(
            documents=texts[i:i+batch_size],
            embeddings=embeddings[i:i+batch_size],
            metadatas=metadatas[i:i+batch_size],
            ids=ids[i:i+batch_size]
        )
        print(f"Stored batch {i//batch_size + 1}")
    print(f"Done. {collection.count()} chunks stored in ChromaDB.")
    return collection

def test_retrieval(collection, query, k=5):
    model = SentenceTransformer("all-MiniLM-L6-v2")
    query_embedding = model.encode([query]).tolist()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=k,
        include=["documents", "metadatas", "distances"]
    )
    print(f"\n--- RETRIEVAL TEST ---")
    print(f"Query: {query}\n")
    for i in range(len(results["documents"][0])):
        print(f"Result {i+1}:")
        print(f"  Source: {results['metadatas'][0][i]['source']}")
        print(f"  Distance: {results['distances'][0][i]:.4f}")
        print(f"  Text: {results['documents'][0][i][:200]}...")
        print()

if __name__ == "__main__":
    documents = load_documents("documents")
    chunks = chunk_documents(documents)
    collection = embed_and_store(chunks, reset=True)
    test_retrieval(collection, "vegetarian food mislabeled at Yahentamitsi")
    test_retrieval(collection, "which dining hall is most crowded during lunch")
    test_retrieval(collection, "food allergy options Purple Zone")