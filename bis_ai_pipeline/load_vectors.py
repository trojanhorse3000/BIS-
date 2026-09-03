"""
Load vector_corpus_upload_ready.jsonl into a local Chroma collection.
Run this on your own machine where chromadb + sentence-transformers are installed.

    pip install chromadb sentence-transformers --break-system-packages

Then: python load_vectors.py
"""
import json
import chromadb
from sentence_transformers import SentenceTransformer

client = chromadb.PersistentClient(path="./chroma_store")
collection = client.get_or_create_collection("bis_knowledge")
model = SentenceTransformer("all-MiniLM-L6-v2")

rows = []
with open("vector_corpus_upload_ready.jsonl") as f:
    for line in f:
        rows.append(json.loads(line))

ids = [r["chunk_id"] for r in rows]
docs = [r["text"] for r in rows]
metas = [{k: v for k, v in r.items() if k not in ("chunk_id", "text") and v is not None} for r in rows]
embeddings = model.encode(docs).tolist()

collection.upsert(ids=ids, documents=docs, metadatas=metas, embeddings=embeddings)
print(f"Upserted {len(rows)} chunks into 'bis_knowledge' collection.")

# quick sanity check
test = collection.query(query_texts=["how do I apply for ISI certification"], n_results=2)
for doc, meta in zip(test["documents"][0], test["metadatas"][0]):
    print("\n---")
    print(doc[:150], "...")
    print("source:", meta.get("source_url"))
