# wisdom_node_schema.md
> Doc truoc khi tao bat ky node nao | Updated: 2026-05-11 | P-026

---

## NGUYEN TAC COT LOI

**RULE-A**: Neo4j = SOURCE OF TRUTH. Qdrant = SEARCH INDEX.  
Moi node phai ton tai trong Neo4j truoc, lay `elementId()` roi moi write Qdrant.

**RULE-B**: Moi KnowledgeNode phai co du 7 fields bat buoc:  
`trust_score` · `decay_lambda` · `valid_from` · `valid_until` · `epistemic_status` · `cultural_context` · `source_type`

**RULE-C**: Decay formula: `trust_score(t) = base * exp(-lambda * age_days)`

---

## 4-LAYER ARCHITECTURE

```
INBOX (InboxItem)
    ↓ [:PROMOTED_TO]
RAW (RawSource / Video / Document / SocialPost)
    ↓ [:DISTILLED_TO]
WIKI (Concept / Rule / CaseStudy / Framework / Insight)
    ↓ [:COMPILED_INTO]
OUTBOX (Blueprint)
```

---

## LAYER 1 — INBOX

### InboxItem
Diem vao duy nhat cho moi nguon du lieu chua xu ly.

| Field | Type | Required | Default | Mo ta |
|---|---|---|---|---|
| id | String | ✅ | UUID | Unique identifier |
| raw_content | String | ✅ | — | Noi dung thu |
| source_url | String | ✅ | — | Nguon goc |
| sha256_checksum | String | ✅ | — | Dedup hash |
| ingested_at | DateTime | ✅ | now() | Thoi gian nhan |
| epistemic_status | String | ✅ | UNVERIFIED | UNVERIFIED / PENDING / VERIFIED |
| urgency | String | ✅ | med | low / med / high |
| niche | String | ❌ | GLOBAL | Domain/topic |
| auto_tags | List[String] | ❌ | [] | Tags tu dong |

**Relationships:**
- `(InboxItem)-[:PROMOTED_TO]->(RawSource)` — sau khi qua validation

---

## LAYER 2 — RAW

### RawSource
Node chuan hoa cho moi nguon du lieu sau khi promote tu Inbox.

| Field | Type | Required | Default | Mo ta |
|---|---|---|---|---|
| id | String | ✅ | — | Unique ID |
| content_hash | String | ✅ | SHA-256 | Dedup — UNIQUE constraint |
| ingested_timestamp | DateTime | ✅ | now() | Thoi gian ingest |
| source_url | String | ✅ | — | URL hoac path |
| raw_content | String | ✅ | — | Noi dung (toi da 500 chars) |
| qdrant_vector_id | String | ✅ | — | Bridge sang Qdrant (P-004) |
| epistemic_status | String | ✅ | PENDING | PENDING / VERIFIED / REJECTED |
| source_type | String | ✅ | — | VIDEO / DOCUMENT / SOCIAL / WEB |
| migrated_from | String | ❌ | — | Ten node goc neu migrate |

**Relationships:**
- `(RawSource)-[:DISTILLED_TO]->(Concept|Rule|CaseStudy|Framework|Insight)`

### Video *(subtype cua RawSource)*
Tao boi `wisdom_ingest.py`. Bridge sang RawSource qua `[:PROMOTED_TO]`.

| Field | Type | Required | Default | Mo ta |
|---|---|---|---|---|
| id | String | ✅ | MD5(url)[:12] | Content ID |
| url | String | ✅ | — | YouTube/video URL |
| title | String | ✅ | — | Tieu de video |
| summary | String | ✅ | — | Tom tat 2-3 cau |
| duration | Int | ❌ | 0 | Thoi luong (giay) |
| language | String | ✅ | en | vi / en |
| value_flywheel | String | ✅ | learning | learning/experience/earning/contribution/growth |
| ingested_at | DateTime | ✅ | now() | — |
| trust_score | Float | ✅ | 0.8 | RULE-B |
| decay_lambda | Float | ✅ | 0.003 | RULE-B |
| valid_from | DateTime | ✅ | now() | RULE-B |
| valid_until | DateTime | ✅ | null | RULE-B |
| epistemic_status | String | ✅ | PENDING | RULE-B |
| cultural_context | String | ✅ | GLOBAL | RULE-B |
| source_type | String | ✅ | VIDEO | RULE-B |

### Document *(subtype cua RawSource)*
Tao boi `wisdom_upload.py`. Ho tro PDF, DOCX, PPTX, XLSX, TXT, MD, EPUB, Audio, Video, Image.

| Field | Type | Required | Default | Mo ta |
|---|---|---|---|---|
| id | String | ✅ | MD5(path+mtime)[:12] | Content ID |
| filename | String | ✅ | — | Ten file |
| path | String | ✅ | — | Duong dan day du |
| title | String | ✅ | — | Tieu de doc |
| summary | String | ✅ | — | Tom tat |
| document_type | String | ✅ | other | book/article/report/lecture/note/data/other |
| language | String | ✅ | en | vi / en |
| value_flywheel | String | ✅ | learning | — |
| ingested_at | DateTime | ✅ | now() | — |
| trust_score | Float | ✅ | 0.8 | RULE-B |
| decay_lambda | Float | ✅ | 0.003 | RULE-B |
| valid_from | DateTime | ✅ | now() | RULE-B |
| valid_until | DateTime | ✅ | null | RULE-B |
| epistemic_status | String | ✅ | PENDING | RULE-B |
| cultural_context | String | ✅ | GLOBAL | RULE-B |
| source_type | String | ✅ | DOCUMENT | RULE-B |

### SocialPost *(subtype cua RawSource)*
Tao boi `wisdom_fb_ingest.py`.

| Field | Type | Required | Default | Mo ta |
|---|---|---|---|---|
| id | String | ✅ | MD5(url)[:12] | Content ID |
| url | String | ✅ | — | Post URL |
| title | String | ✅ | — | Tieu de ngan |
| summary | String | ✅ | — | Tom tat |
| platform | String | ✅ | facebook | facebook / facebook_saved |
| content_type | String | ✅ | unknown | educational/news/opinion/entertainment/promotion |
| language | String | ✅ | vi | vi / en |
| value_flywheel | String | ✅ | learning | — |
| ingested_at | DateTime | ✅ | now() | — |
| trust_score | Float | ✅ | 0.7 | RULE-B — thap hon Video/Doc |
| decay_lambda | Float | ✅ | 0.003 | RULE-B |
| valid_from | DateTime | ✅ | now() | RULE-B |
| valid_until | DateTime | ✅ | null | RULE-B |
| epistemic_status | String | ✅ | PENDING | RULE-B |
| cultural_context | String | ✅ | GLOBAL | RULE-B |
| source_type | String | ✅ | SOCIAL | RULE-B |

---

## LAYER 3 — WIKI

Fields chung cho tat ca WIKI nodes (Concept, Rule, CaseStudy, Framework, Insight):

| Field | Type | Required | Default | Mo ta |
|---|---|---|---|---|
| id | String | ✅ | MD5(name)[:12] | Unique ID |
| name / title | String | ✅ | — | Ten node |
| content | String | ✅ | — | Noi dung chinh |
| trust_score | Float | ✅ | 0.7 | RULE-B — base trust |
| decay_lambda | Float | ✅ | 0.003 | RULE-B — toc do decay |
| valid_from | DateTime | ✅ | now() | RULE-B |
| valid_until | DateTime | ✅ | null | RULE-B — null = khong het han |
| epistemic_status | String | ✅ | PENDING | RULE-B: PENDING/VERIFIED/CONTRADICTED |
| cultural_context | String | ✅ | GLOBAL | RULE-B: GLOBAL/VN/STARTUP/... |
| source_type | String | ✅ | CONCEPT | RULE-B |
| review_cadence | String | ❌ | weekly | daily/weekly/monthly/quarterly |
| last_reviewed | DateTime | ❌ | now() | — |
| next_review | DateTime | ❌ | — | Computed tu review_cadence |
| red_team_score | Float | ❌ | null | Devil's Advocate score (P-020) |
| ripeness_score | Float | ❌ | null | Do chin muoi de dua vao Blueprint |

### Concept
Node kien thuc co ban. Duoc tao tu key_concepts cua Ollama analysis.

`source_type = 'CONCEPT'` | `trust_score default = 0.7`

### Rule
Nguyen tac / quy tac co the ap dung. Higher trust than raw Concept.

`source_type = 'RULE'` | `trust_score default = 0.85`

### CaseStudy
Vi du thuc te. Gan voi cultural_context cu the.

`source_type = 'CASE'` | `trust_score default = 0.75`

### Framework
Mo hinh tu duy / khung phan tich.

`source_type = 'FRAMEWORK'` | `trust_score default = 0.8`

### Insight
Ket luan rut ra tu nhieu nguon. Ephemeral — decay nhanh hon.

`source_type = 'INSIGHT'` | `decay_lambda default = 0.01`

---

## LAYER 4 — OUTBOX

### Blueprint
San pham dau ra — ban do tu duy, framework, product.

| Field | Type | Required | Default | Mo ta |
|---|---|---|---|---|
| id | String | ✅ | UUID | Unique ID |
| title | String | ✅ | — | Tieu de |
| description | String | ✅ | — | Mo ta ngan |
| wiki_nodes | List[String] | ✅ | [] | IDs cua WIKI nodes lien quan |
| price | Float | ✅ | 0.0 | Gia ban (USD) |
| status | String | ✅ | draft | draft / published / archived |
| created_at | DateTime | ✅ | now() | — |
| downloads | Int | ❌ | 0 | So luot tai |
| rating | Float | ❌ | 0.0 | Diem danh gia |

**Relationships:**
- `(Blueprint)-[:DERIVED_FROM]->(Rule|Concept|Framework)`
- `(Rule|Concept)-[:COMPILED_INTO]->(Blueprint)`

---

## QDRANT BRIDGE (P-004)

Moi node trong Neo4j co vector tuong ung trong Qdrant.  
Key bridge field trong Qdrant payload:

```json
{
  "neo4j_node_id": "4:f237db68-...:39",  // elementId() tu Neo4j
  "content_id":    "927477c89f3c",        // MD5 hash
  "source_type":   "DOCUMENT",
  "epistemic_status": "PENDING"
}
```

**Collection mapping:**
- `wisdom_knowledge` — default, tat ca public nodes
- `wisdom_private_{uid}` — tacit knowledge cua Sep (RULE-E)
- `wisdom_shadow` — nodes chua verified

---

## DEDUP (P-012) — wisdom_dedup.py

### Checksum formula
```python
# KHONG phai SHA-256 cua url hoac content rieng le
# MA LA SHA-256 cua (url + content[:500]) gop lai
raw      = f"{url.strip()}{content.strip()[:500]}"
checksum = hashlib.sha256(raw.encode('utf-8')).hexdigest()
```

### Flow chuan
```python
# BUOC 1 — Truoc ingest: check duplicate
result = _dedup.check_and_register(url, content)
if result["is_duplicate"]:
    print(f"Da co: {result['existing_id']}")
    return  # bo qua

# ... ingest binh thuong, lay neo4j_node_id ...

# BUOC 2 — Sau ingest: register checksum
_dedup.check_and_register(url, content, node_id=str(neo4j_node_id))
# -> ghi sha256_checksum vao node trong Neo4j
```

### Field duoc ghi vao node
`sha256_checksum` — field bat buoc sau khi ingest thanh cong.  
`check_duplicate()` tim kiem qua field nay: `WHERE n.sha256_checksum = $checksum`

### Return format
```python
# Chua ton tai:
{"is_duplicate": False, "checksum": "abc123..."}

# Da ton tai:
{"is_duplicate": True, "existing_id": "...", "existing_title": "...", "ingested_at": "..."}
```

---

## DECAY FUNCTION (RULE-C) — wisdom_decay.py

```python
import math

def compute_decay(base_score: float, decay_lambda: float, age_days: float) -> float:
    return round(base_score * math.exp(-decay_lambda * age_days), 4)

# Vi du:
# base=0.8, lambda=0.003, age=365 days -> trust = 0.8 * e^(-1.095) = 0.267
# base=0.8, lambda=0.003, age=30  days -> trust = 0.8 * e^(-0.09)  = 0.731
```

### Nguong trang thai
| Score | Status | Action |
|---|---|---|
| >= 0.5 | Healthy | Giu nguyen |
| 0.3 - 0.5 | Warning | Flag — can review |
| < 0.3 | DEPRECATED | Tu dong set epistemic_status = DEPRECATED |

### decay_lambda theo domain (DOMAIN_DECAY)
| Domain | lambda | Half-life | Vi du |
|---|---|---|---|
| tech_news | 0.05 | ~14 ngay | Tin tuc cong nghe |
| mmo | 0.05 | ~14 ngay | MMO/kinh doanh online |
| market | 0.05 | ~14 ngay | Gia ca, thi truong |
| framework | 0.01 | ~69 ngay | Phuong phap luan |
| methodology | 0.01 | ~69 ngay | Quy trinh |
| principle | 0.003 | ~231 ngay | Nguyen tac nen tang |
| science | 0.001 | ~693 ngay | Khoa hoc |
| math | 0.0001 | ~6931 ngay | Toan hoc — vinh vien |
| default | 0.003 | ~231 ngay | Mac dinh |

### Scheduled job
```bash
# Chay hang ngay
python wisdom/core/wisdom_decay.py --run

# Xem bao cao khong update
python wisdom/core/wisdom_decay.py --report

# Test truoc khi chay that
python wisdom/core/wisdom_decay.py --dry-run
```

### Fields duoc update boi decay job
- `trust_score` — gia tri moi sau decay
- `epistemic_status` — co the chuyen sang DEPRECATED
- `last_decay_at` — timestamp lan decay gan nhat

---

## EPISTEMIC STATUS FLOW

```
UNVERIFIED (InboxItem moi)
    ↓ auto-promote sau basic check
PENDING (RawSource / Wiki nodes moi tao)
    ↓ background validation job (RULE-D)
VERIFIED (vao Global Pool)
    ↓ neu xuat hien contradiction (RULE-F)
CONTRADICTED (tao CONTRADICTS node, khong xoa)
```

**RULE-F**: Mau thuan → tao `[:CONTRADICTS]` relationship.  
**Khong bao gio xoa node**. Chi them CONTRADICTED status.

---

## CHECKLIST TRUOC KHI TAO NODE

- [ ] `strip_emoji()` cho moi text field
- [ ] `encoding='utf-8'` cho moi `open()`
- [ ] `try/except` cho moi DB call
- [ ] Write Neo4j TRUOC — lay `elementId()` — THEN write Qdrant
- [ ] Du 7 RULE-B fields
- [ ] `check_duplicate()` TRUOC khi ingest
- [ ] `register_checksum()` SAU khi ingest thanh cong

---

*Xem them: docs/WISDOM_ARCHITECTURE.md | docs/WISDOM_VOICE.md | CLAUDE.md*
