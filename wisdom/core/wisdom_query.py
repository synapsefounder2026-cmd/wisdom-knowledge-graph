"""
Wisdom Query Pipeline
Tim kiem knowledge da luu trong Neo4j + Qdrant bang ngon ngu tu nhien.

Usage:
    python wisdom_query.py "what is commitment in relationships"
    python wisdom_query.py "video ve tinh yeu"
"""

import requests
import json
import sys
import re
from neo4j import GraphDatabase
from qdrant_client import QdrantClient

# ── EP-001 Fix: Strip emoji ───────────────────────────────────────────────────
def strip_emoji(text: str) -> str:
    if not isinstance(text, str):
        return str(text) if text else ""
    emoji_pattern = re.compile(
        '['
        u'\U0001F600-\U0001F64F'
        u'\U0001F300-\U0001F5FF'
        u'\U0001F680-\U0001F6FF'
        u'\U0001F1E0-\U0001F1FF'
        u'\U00002600-\U000027BF'
        u'\U0001F900-\U0001F9FF'
        ']+',
        flags=re.UNICODE
    )
    return emoji_pattern.sub('', text).strip()

# Config
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


def get_embedding(text):
    response = requests.post(
        "%s/api/embeddings" % OLLAMA_BASE,
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=60
    )
    return response.json().get("embedding", [])


def search_qdrant(query, top_k=TOP_K):
    query = strip_emoji(query)  # EP-001 fix
    print("Searching vectors: '%s'" % query)
    try:
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        embedding = get_embedding(query)

        if not embedding:
            print("  WARNING: Could not get embedding")
            return []

        results = client.query_points(
            collection_name=COLLECTION,
            query=embedding,
            limit=top_k,
            with_payload=True
        )
        return [
            {
                "score": round(r.score, 3),
                "video_id": r.payload.get("video_id") or r.payload.get("file_id"),
                "title": r.payload.get("title"),
                "summary": r.payload.get("summary"),
                "tags": r.payload.get("tags", []),
                "key_concepts": r.payload.get("key_concepts", []),
                "url": r.payload.get("url"),
                "value_flywheel": r.payload.get("value_flywheel"),
            }
            for r in results.points
        ]
    except Exception as e:
        print("  Qdrant ERROR: %s" % e)
        return []


def search_neo4j_by_concept(concept):
    concept = strip_emoji(concept)  # EP-001 fix
    print("Graph searching concept: '%s'" % concept)
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        results = []

        with driver.session() as session:
            result = session.run("""
                MATCH (v)-[:HAS_CONCEPT]->(c:Concept)
                WHERE toLower(c.name) CONTAINS toLower($concept)
                RETURN 
                    coalesce(v.title, v.filename) as title,
                    coalesce(v.url, v.path) as url,
                    v.summary as summary,
                    coalesce(v.id, v.file_id) as video_id,
                    collect(c.name) as concepts
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
    except Exception as e:
        print("  Neo4j ERROR: %s" % e)
        return []


def ask_ollama(question, context):
    print("Generating answer with %s..." % OLLAMA_MODEL)
    prompt = """You are Wisdom AI assistant. Answer the user's question based on the knowledge base context below.
Be concise and helpful. If context is insufficient, say so honestly.

KNOWLEDGE BASE CONTEXT:
%s

USER QUESTION: %s

Answer in the same language as the question (Vietnamese or English):""" % (context, question)

    response = requests.post(
        "%s/api/generate" % OLLAMA_BASE,
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=120
    )
    return response.json().get("response", "No answer generated.")


def query(question):
    question = strip_emoji(question)  # EP-001 fix
    print("\n" + "="*60)
    print("  WISDOM QUERY")
    print("  Q: %s" % question)
    print("="*60 + "\n")

    # 1. Vector search
    vector_results = search_qdrant(question)

    # 2. Graph search
    first_word = question.split()[0] if question else ""
    graph_results = search_neo4j_by_concept(first_word)

    # 3. Build context
    context_parts = []
    seen_ids = set()

    print("\nVector Search Results (top %d):" % len(vector_results))
    for r in vector_results:
        vid = r.get("video_id")
        if vid not in seen_ids:
            seen_ids.add(vid)
            print("  [%s] %s -- %s" % (r['score'], r['title'], r['url']))
            print("        Concepts: %s" % ', '.join(r['key_concepts']))
            print("        Flywheel: %s" % r['value_flywheel'])
            context_parts.append(
                "Title: %s\nSummary: %s\nConcepts: %s\nURL: %s" % (
                    r['title'], r['summary'],
                    ', '.join(r['key_concepts']), r['url']
                )
            )

    if graph_results:
        print("\nGraph Search Results:")
        for r in graph_results:
            vid = r.get("video_id")
            if vid not in seen_ids:
                seen_ids.add(vid)
                print("  %s -- Concepts: %s" % (r['title'], ', '.join(r['concepts'])))
                context_parts.append(
                    "Title: %s\nSummary: %s\nConcepts: %s\nURL: %s" % (
                        r['title'], r['summary'],
                        ', '.join(r['concepts']), r['url']
                    )
                )

    # 4. Generate answer
    if context_parts:
        context = "\n\n---\n\n".join(context_parts[:3])
        answer = ask_ollama(question, context)
        print("\nWisdom Answer:")
        print("-"*60)
        print(answer)
        print("-"*60)
    else:
        print("\nNo relevant knowledge found. Try ingesting more content first.")

    print("\nFound %d unique source(s)\n" % len(seen_ids))


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What did you learn from the videos?"
    query(question)