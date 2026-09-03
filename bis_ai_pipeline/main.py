"""
main.py
End-to-end runner demonstrating the complete BIS AI Pipeline:
1. Normalize query & extract entities
2. Classify user intent
3. Retrieve structured facts (SQLite) & vector knowledge chunks (ChromaDB)
4. Synthesize final answer
"""

import sys
from pipeline.normalize import normalize_query, extract_entities
from pipeline.intent import classify_intent
from pipeline.retrieve import HybridRetriever
from pipeline.generate import AnswerGenerator


def run_pipeline(user_query: str):
    print(f"\n{'='*70}")
    print(f"User Query: {user_query}")
    print(f"{'='*70}")

    # Step 1: Normalize & Extract
    cleaned = normalize_query(user_query)
    entities = extract_entities(user_query)
    print(f"[1. Normalized Entities]: {entities}")

    # Step 2: Intent Classification
    intent_data = classify_intent(cleaned, entities)
    print(f"[2. Intent]: {intent_data['intent'].value} (Confidence: {intent_data['confidence']})")

    # Step 3: Retrieval
    retriever = HybridRetriever()
    retrieved = retriever.retrieve(cleaned, intent_data, entities)
    print(f"[3. Retrieved]: {len(retrieved['structured_results'])} structured row(s), {len(retrieved['vector_results'])} vector doc(s)")

    # Step 4: Generation
    generator = AnswerGenerator()
    response = generator.generate(cleaned, intent_data, retrieved)

    print(f"\n[4. Final Response] (Source: {response['source']}):\n")
    print(response["answer"])
    print(f"{'='*70}\n")
    return response


if __name__ == "__main__":
    test_queries = [
        "Please verify gold hallmark HUID code AB1234",
        "What are the mandatory requirements under IS 1293:2019?",
        "Which Indian Standard applies to HS code 8504.40.90 for power adaptors?",
        "Do lithium-ion batteries need compulsory registration under BIS CRS scheme?"
    ]

    query = sys.argv[1] if len(sys.argv) > 1 else test_queries[0]
    run_pipeline(query)
