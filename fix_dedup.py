import sys
from datetime import datetime

def fix_file(path):
    with open(path, encoding='utf-8') as f:
        content = f.read()

    content = content.replace(
        '_dedup.check_duplicate(url_hash).get("is_duplicate", False)',
        '_dedup.check_duplicate(url_hash).get("is_duplicate", False)'
    )
    content = content.replace(
        '_dedup.is_duplicate(url_hash)',
        '_dedup.check_duplicate(url_hash).get("is_duplicate", False)'
    )
    content = content.replace(
        '_dedup.is_duplicate(transcript_hash)',
        '_dedup.check_duplicate(transcript_hash).get("is_duplicate", False)'
    )
    content = content.replace(
        '_dedup.is_duplicate(content_hash)',
        '_dedup.check_duplicate(content_hash).get("is_duplicate", False)'
    )
    content = content.replace(
        '_dedup.is_duplicate(h)',
        '_dedup.check_duplicate(h).get("is_duplicate", False)'
    )
    content = content.replace(
        '_dedup.register(url_hash)',
        '_dedup.register_checksum(str(neo4j_node_id), url_hash, url, datetime.now().isoformat())'
    )
    content = content.replace(
        '_dedup.register(transcript_hash)',
        '_dedup.register_checksum(str(neo4j_node_id), transcript_hash, data["url"], datetime.now().isoformat())'
    )
    content = content.replace(
        '_dedup.register(content_hash)',
        '_dedup.register_checksum(str(neo4j_node_id), content_hash, path, datetime.now().isoformat())'
    )
    content = content.replace(
        '_dedup.register(file_hash)',
        '_dedup.register_checksum(str(neo4j_node_id), file_hash, path, datetime.now().isoformat())'
    )
    content = content.replace(
        '_dedup.register(hashlib.sha256(key.encode()).hexdigest())',
        '_dedup.register_checksum("", hashlib.sha256(key.encode()).hexdigest(), key, datetime.now().isoformat())'
    )

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Fixed: {path}")

for p in sys.argv[1:]:
    fix_file(p)
