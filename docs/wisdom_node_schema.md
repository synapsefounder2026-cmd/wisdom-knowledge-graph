# wisdom_node_schema.md — KnowledgeNode Properties Reference
> Doc nay dinh nghia CHUAN HOA cho moi KnowledgeNode trong Wisdom.
> Moi agent phai doc file nay truoc khi tao node moi.
> Last updated: 2026-05-07

---

## 1. KnowledgeNode — Day du fields

```python
{
  # ── IDENTITY ──────────────────────────────────────────
  "id":             str,      # UUID tu dong tao, khong thay doi
  "title":          str,      # Tieu de ngan, ro rang, < 100 chars
  "content":        str,      # Noi dung chinh da clean (sau wisdom_cleaner)
  "content_hash":   str,      # SHA-256 cua content, dung cho dedup
  "source_url":     str,      # URL nguon goc, None neu tacit knowledge
  "created_at":     str,      # ISO 8601: "2026-05-07T14:30:00+07:00"
  "updated_at":     str,      # ISO 8601, cap nhat moi lan chinh sua

  # ── TRUST & DECAY ─────────────────────────────────────
  "trust_score":    float,    # 0.0 → 1.0, tinh theo RULE-C
  "decay_lambda":   float,    # He so suy giam, xem bang o duoi
  "valid_from":     str,      # ISO date, ngay bat dau co hieu luc
  "valid_until":    str|None, # ISO date, None = khong het han

  # ── CLASSIFICATION ────────────────────────────────────
  "epistemic_status": str,    # Xem enum ben duoi
  "cultural_context": str,    # Xem enum ben duoi
  "source_type":      str,    # Xem enum ben duoi
  "domain":           str,    # vd: "MMO", "KDP", "AI", "Finance"
  "content_type":     str,    # Xem enum ben duoi
  "language":         str,    # "vi", "en", "ja"...

  # ── CADENCE (P-011) ───────────────────────────────────
  "review_cadence":   str,    # Xem enum ben duoi
  "last_reviewed":    str|None,
  "next_review":      str|None,
  "review_count":     int,    # So lan da review, bat dau tu 0
  "retention_score":  float,  # 0.0 → 1.0, SM-2 algorithm
  "decay_on_skip":    bool,   # True = giam trust_score neu bo qua

  # ── TEMPORAL (P-021) ──────────────────────────────────
  "domain_ttl":       int,    # So ngay truoc khi trigger live search

  # ── METADATA ──────────────────────────────────────────
  "tags":           list[str],# ["KDP", "low-content", "Amazon"]
  "author":         str|None, # Ten tac gia neu biet
  "word_count":     int,      # So tu trong content
  "embedding_id":   str|None, # ID trong Qdrant, None truoc khi index
}
```

---

## 2. Enum Values

### epistemic_status
| Value | Y nghia | Khi nao dung |
|-------|---------|--------------|
| `PENDING` | Moi ingest, chua kiem tra | Default khi tao node |
| `VERIFIED` | Da qua Council check | Sau khi Buffett/Jobs/Munger approve |
| `CONTESTED` | Co mau thuan voi node khac | Khi CONTRADICTS relationship ton tai |
| `SHADOW` | Hypothesis, can them bang chung | Suy luan, chua co nguon ro |
| `DEPRECATED` | Het hieu luc, khong xoa | Khi valid_until da qua |

### cultural_context
| Value | Y nghia |
|-------|---------|
| `GLOBAL` | Ap dung toan cau |
| `REGION_VN` | Chi ap dung tai Viet Nam |
| `REGION_SEA` | Dong Nam A |
| `REGION_SPECIFIC` | Vung cu the khac, ghi ro trong tags |

### source_type
| Value | Y nghia | trust_score mac dinh |
|-------|---------|----------------------|
| `ACADEMIC` | Nghien cuu khoa hoc, peer-reviewed | 0.90 |
| `EXPERT` | Chuyen gia co ten tuoi, verified | 0.85 |
| `NEWS` | Bao chi uy tin | 0.75 |
| `COMMUNITY` | FB groups, forum, social | 0.60 |
| `TACIT` | Kinh nghiem ca nhan Sep | 0.80 |
| `SYNTHETIC` | Do AI tao ra, chua verify | 0.50 |
| `BLUEPRINT` | Trich xuat tu Blueprint da ban | 0.85 |

### content_type
| Value | Y nghia |
|-------|---------|
| `CONCEPT` | Khai niem, dinh nghia |
| `STRATEGY` | Chien luoc, phuong phap |
| `TUTORIAL` | Huong dan tung buoc |
| `CASE_STUDY` | Vi du thuc te |
| `DATA` | So lieu, thong ke |
| `OPINION` | Y kien ca nhan |
| `NEWS_EVENT` | Su kien thoi su |
| `TOOL` | Cong cu, phan mem |

### review_cadence
| Value | Tan suat | decay_lambda | Dung cho |
|-------|----------|--------------|---------|
| `daily` | Moi ngay | 0.05 | AI news, social trends, market price |
| `weekly` | Moi tuan | 0.01 | Frameworks, tools, methods |
| `monthly` | Moi thang | 0.003 | Core principles, strategies |
| `archive` | Khong review | ~0 | History, math, timeless knowledge |

---

## 3. decay_lambda Mac dinh Theo Domain

| Domain | decay_lambda | review_cadence | Ly do |
|--------|-------------|----------------|-------|
| AI/Tech news | 0.05 | daily | Thay doi hang ngay |
| Social trends | 0.05 | daily | Xu huong nhanh tan |
| Market price | 0.10 | daily | Thay doi theo gio |
| KDP strategies | 0.02 | weekly | Amazon thay doi thuong xuyen |
| Frameworks/Methods | 0.01 | weekly | Cap nhat theo quy |
| Business principles | 0.003 | monthly | Kha ben vung |
| OPC/MMO strategies | 0.005 | monthly | Thay doi cham |
| Mathematics | 0.0001 | archive | Bat bien |
| Historical facts | 0.0001 | archive | Bat bien |
| Core principles | 0.001 | monthly | Rat ben vung |
| Government policy VN | 0.03 | monthly | Thay doi theo chinh sach |

---

## 4. Neo4j Relationships

```cypher
# Lien ket tri thuc
(:KnowledgeNode)-[:SUPPORTS {confidence: 0.85}]->(:KnowledgeNode)
(:KnowledgeNode)-[:CONTRADICTS {confidence_diff: 0.02}]->(:KnowledgeNode)
(:KnowledgeNode)-[:DERIVED_FROM {method: "synthesis"}]->(:KnowledgeNode)
(:KnowledgeNode)-[:RELATED_TO {strength: 0.7}]->(:KnowledgeNode)

# Blueprint
(:KnowledgeNode)-[:COMPILED_INTO {order: 1}]->(:Blueprint)
(:Blueprint)-[:REQUIRES]->(:KnowledgeNode)

# Council
(:KnowledgeNode)-[:INTERROGATED_BY {result: "PASS", score: 0.9}]->(:PersonaAgent)
(:PersonaAgent)-[:FLAGGED {reason: "moat_weak"}]->(:KnowledgeNode)

# User
(:User)-[:REVIEWED {rating: "easy", date: "2026-05-07"}]->(:KnowledgeNode)
(:User)-[:CREATED]->(:KnowledgeNode)
(:User)-[:BOOKMARKED]->(:KnowledgeNode)

# Temporal
(:KnowledgeNode)-[:SUPERSEDES]->(:KnowledgeNode)
(:KnowledgeNode)-[:UPDATED_FROM]->(:KnowledgeNode)
```

---

## 5. Trust Score Calculation

```python
import math

def calc_trust_score(
    base_score: float,
    age_days: int,
    decay_lambda: float,
    review_count: int = 0,
    retention_score: float = 0.5
) -> float:
    """
    RULE-C: trust_score(t) = base * exp(-lambda * age_days)
    Bonus: review_count va retention_score tang trust
    """
    # Base decay
    decayed = base_score * math.exp(-decay_lambda * age_days)

    # Review bonus: moi lan review tang 2% trust, toi da 20%
    review_bonus = min(review_count * 0.02, 0.20)

    # Retention bonus: retention cao -> trust ben hon
    retention_bonus = retention_score * 0.05

    final = min(decayed + review_bonus + retention_bonus, 1.0)
    return round(final, 4)

# Vi du:
# Node moi (0 ngay): trust = 0.85
# Sau 30 ngay, lambda=0.01: trust = 0.85 * exp(-0.3) = 0.629
# Sau 30 ngay + 3 reviews: trust = 0.629 + 0.06 = 0.689
```

---

## 6. Node Creation Template

```python
from datetime import datetime, timedelta
import uuid

def create_node(
    title: str,
    content: str,
    source_url: str = None,
    source_type: str = "COMMUNITY",
    domain: str = "GENERAL",
    content_type: str = "CONCEPT",
    cultural_context: str = "GLOBAL",
    language: str = "vi"
) -> dict:
    """
    Template tao KnowledgeNode moi.
    Luon goi ham nay thay vi tao dict thu cong.
    """
    # Lay decay_lambda tu domain
    DECAY_MAP = {
        "AI": 0.05, "KDP": 0.02, "MMO": 0.005,
        "Finance": 0.03, "General": 0.01
    }
    decay_lambda = DECAY_MAP.get(domain, 0.01)

    # Lay review_cadence tu decay_lambda
    if decay_lambda >= 0.05:
        cadence = "daily"
    elif decay_lambda >= 0.01:
        cadence = "weekly"
    elif decay_lambda >= 0.001:
        cadence = "monthly"
    else:
        cadence = "archive"

    # Trust score mac dinh theo source_type
    TRUST_MAP = {
        "ACADEMIC": 0.90, "EXPERT": 0.85, "NEWS": 0.75,
        "COMMUNITY": 0.60, "TACIT": 0.80, "SYNTHETIC": 0.50
    }
    base_trust = TRUST_MAP.get(source_type, 0.60)

    now = datetime.now()
    next_review = {
        "daily": now + timedelta(days=1),
        "weekly": now + timedelta(weeks=1),
        "monthly": now + timedelta(days=30),
        "archive": None
    }.get(cadence)

    return {
        "id": str(uuid.uuid4()),
        "title": title,
        "content": content,
        "content_hash": None,  # wisdom_dedup.py tu tinh
        "source_url": source_url,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "trust_score": base_trust,
        "decay_lambda": decay_lambda,
        "valid_from": now.date().isoformat(),
        "valid_until": None,
        "epistemic_status": "PENDING",
        "cultural_context": cultural_context,
        "source_type": source_type,
        "domain": domain,
        "content_type": content_type,
        "language": language,
        "review_cadence": cadence,
        "last_reviewed": None,
        "next_review": next_review.isoformat() if next_review else None,
        "review_count": 0,
        "retention_score": 0.5,
        "decay_on_skip": True,
        "domain_ttl": 30,
        "tags": [],
        "author": None,
        "word_count": len(content.split()),
        "embedding_id": None,
    }
```

---

## 7. Validation Rules

```python
# Bat buoc check truoc khi ghi Neo4j
def validate_node(node: dict) -> tuple[bool, list[str]]:
    errors = []

    if not node.get("title") or len(node["title"]) > 100:
        errors.append("title: bat buoc, < 100 chars")

    if not node.get("content") or len(node["content"]) < 10:
        errors.append("content: bat buoc, > 10 chars")

    if not 0.0 <= node.get("trust_score", -1) <= 1.0:
        errors.append("trust_score: phai tu 0.0 den 1.0")

    if node.get("epistemic_status") not in [
        "PENDING", "VERIFIED", "CONTESTED", "SHADOW", "DEPRECATED"
    ]:
        errors.append("epistemic_status: gia tri khong hop le")

    if node.get("source_type") not in [
        "ACADEMIC", "EXPERT", "NEWS", "COMMUNITY", "TACIT", "SYNTHETIC", "BLUEPRINT"
    ]:
        errors.append("source_type: gia tri khong hop le")

    return len(errors) == 0, errors
```

---

## 8. Lien ket Quan trong

- RULE-B trong CLAUDE.md — bat buoc co du fields
- RULE-C trong CLAUDE.md — cong thuc decay
- P-011 — Cadence + Spaced Repetition (SM-2)
- P-020 — Council Logic (INTERROGATED_BY relationship)
- P-021 — Temporal Axis (domain_ttl field)
- wisdom_schema.py — Python class implementation
- wisdom_decay.py — Decay function implementation
- wisdom_dedup.py — content_hash calculation

---
*wisdom_node_schema.md — Doc truoc khi tao bat ky node nao*
*Generated: 2026-05-07 | P-026 COMPLETED*