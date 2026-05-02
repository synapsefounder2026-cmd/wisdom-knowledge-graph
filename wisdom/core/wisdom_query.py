"""
Wisdom Query Pipeline
Tìm kiếm knowledge đã lưu trong Neo4j + Qdrant bằng ngôn ngữ tự nhiên.

Usage:
    python wisdom_query.py "what is commitment in relationships"
    python wisdom_query.py "video về tình yêu"
"""

import requests
import json
import sys
from neo4j import GraphDatabase
from qdrant_client import QdrantClient
from qdrant_client.models import Filter

# ── Config ──────────────────────────────────────────────────────────────────
OLLAMA_BASE  = "http://localhost:11434"
OLLAMA_MODEL = "llama3.1:8b"
EMBED_MODEL  = "nomic-embed-text"
NEO4J_URI    = "bolt://localhost:7687"
NEO4J_USER   = "neo4j"
NEO4J_PASS   = "password123"
QDRANT_HOST  = "localhost"
QDRANT_PORT  = 6333
COLLECTION   = "wisdom_knowledge"
TOP_K        = 5

# ── Helpers ──────────────────────────────────────────────────────────────────

def get_embedding(text: str) -> list[float]:
    response = requests.post(
        f"{OLLAMA_BASE}/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=60
    )
    return response.json().get("embedding", [])


def search_qdrant(query: str, top_k: int = TOP_K) -> list[dict]:
    """Vector search trong Qdrant."""
    print(f"🔍 Vector searching: '{query}'")
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    embedding = get_embedding(query)

    if not embedding:
        print("  ⚠️  Could not get embedding")
        return []

    results = client.query_points(
        collection_name=COLLECTION,
        query=embedding,
        limit=top_k,
        with_vectors=False,
        with_payload=True
    )
    return [
        {
            "score": round(r.score, 3),
            "video_id": r.payload.get("video_id"),
            "title": r.payload.get("title"),
            "summary": r.payload.get("summary"),
            "tags": r.payload.get("tags", []),
            "key_concepts": r.payload.get("key_concepts", []),
            "url": r.payload.get("url"),
            "value_flywheel": r.payload.get("value_flywheel"),
        }
        for r in results.points
    ]


def search_neo4j_by_concept(concept: str) -> list[dict]:
    """Tìm video theo concept trong Neo4j."""
    print(f"🗄️  Graph searching concept: '{concept}'")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    results = []

    with driver.session() as session:
        # Tìm video có concept gần giống
        result = session.run("""
            MATCH (v:Video)-[:HAS_CONCEPT]->(c:Concept)
            WHERE toLower(c.name) CONTAINS toLower($concept)
            RETURN v.title as title, v.url as url, v.summary as summary,
                   v.id as video_id, collect(c.name) as concepts
            LIMIT 5
        """, concept=concept)

        for record in result:
            results.append({
                "title": record["title"],
                "url": record["url"],
                "summary": record["summary"],
                "video_id": record["video_id"],
                "concepts": record["concepts"]
            })

    driver.close()
    return results


def ask_ollama(question: str, context: str) -> str:
    """Dùng Ollama để trả lời câu hỏi dựa trên context từ knowledge base."""
    print(f"🧠 Generating answer with {OLLAMA_MODEL}...")
    prompt = f"""You are Wisdom AI assistant. Answer the user's question based on the knowledge base context below.
Be concise and helpful. If context is insufficient, say so honestly.

KNOWLEDGE BASE CONTEXT:
{context}

USER QUESTION: {question}

Answer in the same language as the question (Vietnamese or English):"""

    response = requests.post(
        f"{OLLAMA_BASE}/api/generate",
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=120
    )
    return response.json().get("response", "No answer generated.")


def query(question: str):
    print(f"\n{'='*60}")
    print(f"  WISDOM QUERY")
    print(f"  Q: {question}")
    print(f"{'='*60}\n")

    # 1. Vector search
    vector_results = search_qdrant(question)

    # 2. Graph search (dùng từ đầu tiên của câu hỏi làm concept)
    first_word = question.split()[0] if question else ""
    graph_results = search_neo4j_by_concept(first_word)

    # 3. Build context
    context_parts = []
    seen_ids = set()

    print(f"\n📊 Vector Search Results (top {len(vector_results)}):")
    for r in vector_results:
        vid = r.get("video_id")
        if vid not in seen_ids:
            seen_ids.add(vid)
            print(f"  [{r['score']}] {r['title']} — {r['url']}")
            print(f"        Concepts: {', '.join(r['key_concepts'])}")
            print(f"        Flywheel: {r['value_flywheel']}")
            context_parts.append(
                f"Title: {r['title']}\nSummary: {r['summary']}\n"
                f"Concepts: {', '.join(r['key_concepts'])}\nURL: {r['url']}"
            )

    if graph_results:
        print(f"\n🕸️  Graph Search Results:")
        for r in graph_results:
            vid = r.get("video_id")
            if vid not in seen_ids:
                seen_ids.add(vid)
                print(f"  {r['title']} — Concepts: {', '.join(r['concepts'])}")
                context_parts.append(
                    f"Title: {r['title']}\nSummary: {r['summary']}\n"
                    f"Concepts: {', '.join(r['concepts'])}\nURL: {r['url']}"
                )

    # 4. Generate answer
    if context_parts:
        context = "\n\n---\n\n".join(context_parts[:3])
        answer = ask_ollama(question, context)
        print(f"\n💬 Wisdom Answer:")
        print(f"{'─'*60}")
        print(answer)
        print(f"{'─'*60}")
    else:
        print("\n❌ No relevant knowledge found. Try ingesting more videos first.")

    print(f"\n✅ Found {len(seen_ids)} unique source(s)\n")


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What did you learn from the videos?"
    query(question)