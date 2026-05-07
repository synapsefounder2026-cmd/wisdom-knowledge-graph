# WISDOM_ARCHITECTURE.md — Chi tiết kỹ thuật
> Chuyen tu CLAUDE.md Section 2-18 | Last updated: 2026-05-07

---

## 5-Layer Architecture

```
Layer 1: Ingestion    -> wisdom_ingest.py + wisdom_upload.py + wisdom_fb_ingest.py
Layer 2: Memory/Graph -> Neo4j (SOURCE OF TRUTH)
Layer 3: Query/Search -> wisdom_query.py + Qdrant (SEARCH INDEX)
Layer 4: Cognitive    -> wisdom_validator.py (Council + Devil's Advocate)
Layer 5: Factory      -> Blueprint system (P-009)
```

---

## EROCA Pipeline
```
EXTERNAL -> INBOX -> RAW -> WIKI -> OUTPUT
             |        |      |
           ingest   clean  verify
```

---

## KnowledgeNode Schema Day Du
```python
{
  "id": "uuid",
  "title": "...",
  "content_hash": "sha256...",
  "trust_score": 0.85,
  "decay_lambda": 0.003,
  "valid_from": "2026-05-03",
  "valid_until": None,
  "epistemic_status": "PENDING",  # PENDING|VERIFIED|CONTESTED|SHADOW|DEPRECATED
  "cultural_context": "GLOBAL",   # GLOBAL|REGION_SPECIFIC
  "source_type": "TACIT",         # ACADEMIC|TACIT|SYNTHETIC
  "review_cadence": "weekly",     # daily|weekly|monthly|archive
  "last_reviewed": None,
  "next_review": None,
  "review_count": 0,
  "retention_score": 0.0,
  "decay_on_skip": True,
  "domain_ttl": 30
}
```

---

## Neo4j Relationships
```cypher
(:KnowledgeNode)-[:SUPPORTS]->(:KnowledgeNode)
(:KnowledgeNode)-[:CONTRADICTS {confidence_diff: 0.02}]->(:KnowledgeNode)
(:KnowledgeNode)-[:DERIVED_FROM]->(:KnowledgeNode)
(:KnowledgeNode)-[:COMPILED_INTO]->(:Blueprint)
(:KnowledgeNode)-[:INTERROGATED_BY]->(:PersonaAgent)
```

---

## Temporal Decay
```python
import math
def trust_score(base: float, age_days: int, decay_lambda: float) -> float:
    return base * math.exp(-decay_lambda * age_days)

# decay_lambda mac dinh theo domain:
# AI/Tech news:      0.05  (het han nhanh)
# Frameworks:        0.01
# Core principles:   0.003
# Math/History:      ~0    (khong het han)
```

---

## Council Logic — Persona Agents
```
Buffett  -> Circle of Competence, Margin of Safety, Long-term moat
Jobs     -> User value, Simplicity, "Would I use this?"
Munger   -> Inversion, Mental models, Second-order effects
Street   -> "Mui" lua dao, algorithm changes (Phase 2-3)
Intuition-> Ban sao tu duy Sep Thang (Phase 3, unique moat)
```

---

## Error Pattern Registry

### [EP-003] No Exception Handling
```python
try:
    results = client.query_points(collection_name=COLLECTION, query=embedding, limit=top_k)
except Exception as e:
    logger.error(f"Qdrant query failed: {e}")
    results = None
```

### [EP-005] Subprocess Windows
```python
BASH_EXE = "C:/Program Files/Git/bin/bash.exe"
subprocess.run([BASH_EXE, "-c", f"command {arg}"])
```

### [EP-006] Qdrant API v1.16+
```python
# DUNG (v1.16+)
results = client.query_points(
    collection_name=COLLECTION,
    query=embedding,
    limit=5,
    with_payload=True
)
```

### [EP-011] UTF-8 Encoding
```python
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()
```

### [EP-012] Emoji Strip
```python
import re
def strip_emoji(text: str) -> str:
    return re.sub(r'[^\x00-\x7F\u00C0-\u024F\u1E00-\u1EFF]+', '', text)
```

---

## Business Model
```
San pham 1: Sach KDP (lam ngay bang Claude Project)
San pham 2: Blueprint Marketplace (khi P-009 xong) $29-99/blueprint
San pham 3: Managed Service (Phase 3)
```

## Qdrant Collections
```
wisdom_public         -> VERIFIED nodes (Global Pool)
wisdom_private_{uid}  -> Raw data chua anonymize (TTL: 30 ngay)
wisdom_shadow         -> Hypothesis nodes cho cho bang chung
```

## OPC Framework
```
Sep Thang (Founder)   = Vision + Final decisions
AI Labor Force        = Ollama local + Claude API agents
N Partners            = KDP, Affiliate, FB/TikTok, Blueprint buyers
```