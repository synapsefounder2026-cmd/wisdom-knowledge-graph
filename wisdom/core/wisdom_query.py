"""
Wisdom Query Pipeline
Tim kiem knowledge da luu trong Neo4j + Qdrant bang ngon ngu tu nhien.

Usage:
    python wisdom_query.py "what is commitment in relationships"
    python wisdom_query.py "video ve tinh yeu"
    python wisdom_query.py --inverse "trust"
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
    query = strip_emoji(query)
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
    concept = strip_emoji(concept)
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


# ── P-073: Inverse Knowledge Search (Dark Matter) ────────────────────────────
def query_inverse(concept: str):
    """
    Traverse NGUOC Neo4j graph de tim chuoi suy luan dan den concept.
    Thay vi hoi "X la gi?" -> hoi "Chuoi nao dan den X?"

    Usage: python wisdom_query.py --inverse "trust"
    """
    concept = strip_emoji(concept)
    print("\n" + "="*60)
    print("  WISDOM INVERSE SEARCH — Dark Matter Layer")
    print("  Concept: '%s'" % concept)
    print("  Tim: Chuoi suy luan nao dan den concept nay?")
    print("="*60 + "\n")

    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        chains = []

        with driver.session() as session:

            # --- Query 1: Tim ancestor nodes dan den concept nay ---
            result = session.run("""
                MATCH (target)
                WHERE toLower(coalesce(target.title, target.name, ''))
                      CONTAINS toLower($concept)
                MATCH path = (ancestor)-[:LEADS_TO|SUPPORTS|CAUSES|HAS_CONCEPT*1..5]->(target)
                WHERE ancestor <> target
                RETURN
                    [node in nodes(path) |
                        coalesce(node.title, node.name, node.filename, '')] as chain,
                    [rel in relationships(path) | type(rel)] as rel_types,
                    length(path) as depth,
                    target.summary as target_summary
                ORDER BY depth
                LIMIT 10
            """, concept=concept)

            for record in result:
                chains.append({
                    "chain": record["chain"],
                    "rel_types": record["rel_types"],
                    "depth": record["depth"],
                    "target_summary": record["target_summary"]
                })

            # --- Query 2: Tim concept co cung HAS_CONCEPT container ---
            siblings = session.run("""
                MATCH (c:Concept)
                WHERE toLower(c.name) CONTAINS toLower($concept)
                MATCH (source)-[:HAS_CONCEPT]->(c)
                MATCH (source)-[:HAS_CONCEPT]->(sibling:Concept)
                WHERE sibling <> c
                RETURN
                    coalesce(source.title, source.name) as source_title,
                    c.name as target_concept,
                    collect(DISTINCT sibling.name) as related_concepts
                LIMIT 5
            """, concept=concept)

            sibling_list = []
            for record in siblings:
                sibling_list.append({
                    "source": record["source_title"],
                    "related": record["related_concepts"]
                })

        driver.close()

        # --- In ket qua ---
        if chains:
            print("Chuoi suy luan dan den '%s':\n" % concept)
            for i, c in enumerate(chains, 1):
                steps = " → ".join([s for s in c["chain"] if s])
                rels  = " / ".join(c["rel_types"])
                print("  [Chain %d — depth %d]" % (i, c["depth"]))
                print("  %s" % steps)
                print("  Quan he: %s" % rels)
                if c["target_summary"]:
                    print("  Tom tat: %s" % c["target_summary"][:120])
                print()
        else:
            print("  Khong tim thay chuoi suy luan nao trong graph.")
            print("  Goi y: Ingest them content lien quan den '%s'" % concept)
            print("         Hoac concept chua co LEADS_TO/SUPPORTS/CAUSES edges.\n")

        if sibling_list:
            print("Concepts lien quan (cung nguon):")
            for s in sibling_list:
                related = ", ".join(s["related"][:5])
                print("  [%s] → %s" % (s["source"], related))
            print()

        # --- Tong hop voi Ollama neu co chains ---
        if chains:
            context = "\n".join([
                "Chain %d: %s" % (i+1, " → ".join([s for s in c["chain"] if s]))
                for i, c in enumerate(chains[:3])
            ])
            print("Generating synthesis...")
            prompt = """You are Wisdom AI. A user wants to understand the reasoning chain behind a concept.

Concept: %s

Reasoning chains found in knowledge graph:
%s

Explain in 3-5 sentences: What is the reasoning path that leads to this concept?
Answer in Vietnamese if the concept is Vietnamese, otherwise English.""" % (concept, context)

            try:
                response = requests.post(
                    "%s/api/generate" % OLLAMA_BASE,
                    json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
                    timeout=120
                )
                answer = response.json().get("response", "")
                if answer:
                    print("\nWisdom Synthesis:")
                    print("-"*60)
                    print(answer)
                    print("-"*60)
            except Exception as e:
                print("  Ollama ERROR: %s" % e)

        print("\nFound %d reasoning chain(s) for '%s'\n" % (len(chains), concept))

    except Exception as e:
        print("  Neo4j ERROR: %s" % e)


# ── Forward query (giu nguyen) ────────────────────────────────────────────────
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
    question = strip_emoji(question)
    print("\n" + "="*60)
    print("  WISDOM QUERY")
    print("  Q: %s" % question)
    print("="*60 + "\n")

    vector_results = search_qdrant(question)

    first_word = question.split()[0] if question else ""
    graph_results = search_neo4j_by_concept(first_word)

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


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    args = sys.argv[1:]

    if not args:
        question = "What did you learn from the videos?"
        query(question)
    elif args[0] == "--inverse" and len(args) > 1:
        # Dark Matter mode: traverse nguoc
        concept = " ".join(args[1:])
        query_inverse(concept)
    else:
        # Forward mode: query thuong
        question = " ".join(args)
        query(question)
