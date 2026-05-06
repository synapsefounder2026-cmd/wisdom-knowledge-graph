"""
wisdom_dedup.py
================
Module dung chung cho tat ca ingest pipelines.
Chuc nang:
- SHA-256 checksum cho moi content
- Auto-deduplication truoc khi insert vao Neo4j/Qdrant
- Provenance tracking (chung minh ban quyen)

Usage:
    from wisdom_dedup import WisdomDedup
    dedup = WisdomDedup()
    result = dedup.check_and_register(url, content)
    if result["is_duplicate"]:
        print(f"Da co: {result['existing_id']}")
    else:
        # Tien hanh ingest binh thuong
        pass
"""

import os
import re
import hashlib
from datetime import datetime
from neo4j import GraphDatabase

# ── EP-001 Fix ────────────────────────────────────────────────────────────────
def strip_emoji(text: str) -> str:
    if not isinstance(text, str):
        return str(text) if text else ""
    p = re.compile(
        '[' + u'\U0001F600-\U0001F64F' + u'\U0001F300-\U0001F5FF'
        + u'\U0001F680-\U0001F6FF' + u'\U0001F1E0-\U0001F1FF'
        + u'\U00002600-\U000027BF' + u'\U0001F900-\U0001F9FF' + ']+',
        flags=re.UNICODE)
    return p.sub('', text).strip()

# ── Config ────────────────────────────────────────────────────────────────────
NEO4J_URI  = os.environ.get("NEO4J_URI",  "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASS = os.environ.get("NEO4J_PASS", "password123")


class WisdomDedup:

    def __init__(self):
        try:
            self.driver = GraphDatabase.driver(
                NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
            print("WisdomDedup: Connected")
        except Exception as e:
            print(f"WisdomDedup: Connection failed: {e}")
            self.driver = None

    def close(self):
        if self.driver:
            self.driver.close()

    def compute_checksum(self, url: str, content: str) -> str:
        """
        Tinh SHA-256 checksum tu url + content.
        Dung de:
        1. Detect duplicate truoc khi ingest
        2. Provenance tracking / IP protection
        """
        raw = f"{url.strip()}{content.strip()[:500]}"
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()

    def check_duplicate(self, checksum: str) -> dict:
        """
        Kiem tra checksum da ton tai trong Neo4j chua.
        Return: {is_duplicate, existing_id, existing_title}
        """
        if not self.driver:
            return {"is_duplicate": False}
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (n)
                    WHERE n.sha256_checksum = $checksum
                    RETURN n.id AS id, n.title AS title, n.ingested_at AS ingested_at
                    LIMIT 1
                """, checksum=checksum).single()

                if result:
                    return {
                        "is_duplicate": True,
                        "existing_id":    result["id"],
                        "existing_title": result["title"],
                        "ingested_at":    result["ingested_at"]
                    }
                return {"is_duplicate": False}
        except Exception as e:
            print(f"  Dedup check ERROR: {e}")
            return {"is_duplicate": False}

    def register_checksum(self, node_id: str, checksum: str,
                          url: str, ingested_at: str = None):
        """
        Ghi checksum vao node sau khi ingest thanh cong.
        Goi ham nay SAU KHI da save_to_neo4j() xong.
        """
        if not self.driver:
            return
        try:
            with self.driver.session() as session:
                session.run("""
                    MATCH (n {id: $node_id})
                    SET n.sha256_checksum = $checksum,
                        n.source_url      = $url,
                        n.ingested_at     = $ingested_at,
                        n.epistemic_status = 'PENDING'
                """, node_id=node_id, checksum=checksum,
                     url=url,
                     ingested_at=ingested_at or datetime.now().isoformat())
            print(f"  Checksum registered: {checksum[:16]}...")
        except Exception as e:
            print(f"  Register checksum ERROR: {e}")

    def check_and_register(self, url: str, content: str,
                           node_id: str = None) -> dict:
        """
        Ham tong hop — goi 1 lan duy nhat trong moi ingest pipeline.

        Truoc ingest:
            result = dedup.check_and_register(url, content)
            if result["is_duplicate"]: return  # bo qua

        Sau ingest (co node_id):
            dedup.check_and_register(url, content, node_id=video_id)
        """
        content = strip_emoji(content)
        checksum = self.compute_checksum(url, content)

        # Neu co node_id -> dang o buoc SAU ingest -> chi register
        if node_id:
            self.register_checksum(node_id, checksum, url)
            return {"is_duplicate": False, "checksum": checksum}

        # Khong co node_id -> dang o buoc TRUOC ingest -> check duplicate
        result = self.check_duplicate(checksum)
        result["checksum"] = checksum
        return result


# ── Quick Test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    dedup = WisdomDedup()

    print("\n--- Test checksum ---")
    cs = dedup.compute_checksum(
        "https://youtube.com/watch?v=abc123",
        "This is test content about AI"
    )
    print(f"SHA-256: {cs}")
    print(f"Length: {len(cs)} chars")

    print("\n--- Test duplicate check (chua co data) ---")
    result = dedup.check_and_register(
        "https://youtube.com/watch?v=abc123",
        "This is test content about AI"
    )
    print(result)

    dedup.close()