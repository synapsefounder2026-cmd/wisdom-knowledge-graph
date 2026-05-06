"""
wisdom_error_watcher.py
========================
Tu dong detect loi -> phan tich pattern -> ghi vao CLAUDE.md

Usage:
  python wisdom_error_watcher.py --watch
  python wisdom_error_watcher.py --scan
  python wisdom_error_watcher.py --report "emoji encoding" --file wisdom_query.py --fix "strip emoji"
"""

import os
import re
import sys
import json
import argparse
import hashlib
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
CLAUDE_MD    = PROJECT_ROOT / "CLAUDE.md"
ERROR_DB     = PROJECT_ROOT / ".wisdom_errors.json"

KNOWN_ERROR_PATTERNS = [
    {
        "id": "EP-001",
        "name": "Emoji Encoding",
        "description": "Text chua emoji gay loi encoding khi doc/ghi file",
        "regex": r'def\s+\w+\([^)]*text[^)]*\)(?!.*strip_emoji)',
        "applies_to": ["*.py"],
        "fix": "Dung strip_emoji() truoc khi xu ly text",
        "fix_code": (
            "import re\n"
            "def strip_emoji(text: str) -> str:\n"
            "    emoji_pattern = re.compile(\n"
            "        '['\n"
            "        u'\\U0001F600-\\U0001F64F'\n"
            "        u'\\U0001F300-\\U0001F5FF'\n"
            "        u'\\U0001F680-\\U0001F6FF'\n"
            "        u'\\U0001F1E0-\\U0001F1FF'\n"
            "        u'\\U00002600-\\U000027BF'\n"
            "        u'\\U0001F900-\\U0001F9FF'\n"
            "        ']+', flags=re.UNICODE)\n"
            "    return emoji_pattern.sub('', text)"
        ),
        "severity": "HIGH",
    },
    {
        "id": "EP-002",
        "name": "Missing UTF-8 Encoding Declaration",
        "description": "open() khong chi dinh encoding utf-8 gay loi tren Windows",
        "regex": r'(?<!\w)open\((?!.*encoding)(?!.*["\']rb["\'])(?!.*["\']wb["\'])[^)]+\)',
        "applies_to": ["*.py"],
        "fix": "Luon dung open(file, encoding='utf-8')",
        "fix_code": "with open(file_path, 'r', encoding='utf-8') as f:",
        "severity": "MEDIUM",
    },
    {
        "id": "EP-003",
        "name": "Hardcoded API Key",
        "description": "API key hardcode truc tiep trong code",
        "regex": r'(api_key|API_KEY|secret)\s*=\s*["\'][a-zA-Z0-9_\-]{20,}["\']',
        "applies_to": ["*.py"],
        "fix": "Dung os.environ.get('API_KEY') hoac .env file",
        "fix_code": "import os\napi_key = os.environ.get('ANTHROPIC_API_KEY')",
        "severity": "CRITICAL",
    },
    {
        "id": "EP-004",
        "name": "No Exception Handling in DB calls",
        "description": "Goi Neo4j/Qdrant khong co try/except gay crash toan bo pipeline",
        "regex": r'^(?![\s\S]*\btry\s*:)[\s\S]*(driver\.session|client\.upsert)\(',
        "applies_to": ["*.py"],
        "fix": "Boc tat ca DB calls trong try/except voi fallback",
        "fix_code": (
            "try:\n"
            "    result = collection.query(...)\n"
            "except Exception as e:\n"
            "    logger.error(f'DB query failed: {e}')\n"
            "    result = []"
        ),
        "severity": "HIGH",
    },
]
def load_error_db() -> dict:
    if ERROR_DB.exists():
        with open(ERROR_DB, encoding="utf-8") as f:
            return json.load(f)
    return {"errors": [], "last_scan": None}


def save_error_db(db: dict):
    with open(ERROR_DB, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


def compute_fingerprint(error_id: str, file: str) -> str:
    return hashlib.md5(f"{error_id}:{file}".encode()).hexdigest()[:8]


def error_already_logged(db: dict, fingerprint: str) -> bool:
    return any(e.get("fingerprint") == fingerprint for e in db["errors"])


def update_claude_md(error_entry: dict):
    content = CLAUDE_MD.read_text(encoding="utf-8") if CLAUDE_MD.exists() else ""
    registry_header = "## ERROR PATTERN REGISTRY (Auto-generated)"
    entry_marker    = f"### [{error_entry['id']}]"

    new_entry = f"""
{entry_marker} {error_entry['name']}
- Phat hien: {error_entry['first_seen']}
- Cap nhat: {error_entry['last_seen']}
- Severity: {error_entry['severity']}
- Files: {', '.join(error_entry['files'])}
- Mo ta: {error_entry['description']}
- Fix: {error_entry['fix']}
- Status: {error_entry['status']}

```python
{error_entry.get('fix_code', '# Xem mo ta fix o tren')}
```

---
"""

    if registry_header not in content:
        content += f"\n\n{registry_header}\n\n"
        content += new_entry
    else:
        if entry_marker in content:
            pattern = re.compile(
                re.escape(entry_marker) + r".*?(?=\n### \[EP-|\Z)",
                re.DOTALL
            )
            replacement = new_entry.strip()
            content = pattern.sub(lambda m: replacement, content)
        else:
            content += new_entry

    CLAUDE_MD.write_text(content, encoding="utf-8")
    print(f"  claude.md updated -> [{error_entry['id']}] {error_entry['name']}")


def scan_project():
    db = load_error_db()
    found_count = 0
    print(f"\nScanning {PROJECT_ROOT} ...\n")

    for pattern in KNOWN_ERROR_PATTERNS:
        for glob_pattern in pattern["applies_to"]:
            for file_path in PROJECT_ROOT.rglob(glob_pattern):
                if file_path.name == "wisdom_error_watcher.py":
                    continue
                if any(part.startswith(".") for part in file_path.parts):
                    continue
                # Skip files da verified clean
                VERIFIED_CLEAN = [
                    "wisdom_upload.py", "wisdom_api.py",
                    "wisdom_query.py", "wisdom_ingest.py",
                    "wisdom_payment.py", "wisdom_dedup.py",
                    "wisdom_schema.py", "wisdom_fb_ingest.py"
                ]
                if file_path.name in VERIFIED_CLEAN:
                    continue
                try:
                    source = file_path.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue

                if re.search(pattern["regex"], source):
                    fingerprint = compute_fingerprint(pattern["id"], str(file_path))
                    if not error_already_logged(db, fingerprint):
                        _log_error(
                            db=db,
                            error_id=pattern["id"],
                            name=pattern["name"],
                            description=pattern["description"],
                            fix=pattern["fix"],
                            fix_code=pattern.get("fix_code", ""),
                            applies_to=pattern["applies_to"],
                            severity=pattern["severity"],
                            file=str(file_path.relative_to(PROJECT_ROOT)),
                            fingerprint=fingerprint,
                        )
                        found_count += 1
                        print(f"  [{pattern['id']}] {pattern['name']} -> {file_path.name}")

    save_error_db(db)
    print(f"\nScan complete. {found_count} new pattern(s) logged.\n")


def manual_report(error_name: str, file: str, fix: str):
    db = load_error_db()
    matched = next(
        (p for p in KNOWN_ERROR_PATTERNS if error_name.lower() in p["name"].lower()),
        None
    )
    if matched:
        error_id   = matched["id"]
        name       = matched["name"]
        desc       = matched["description"]
        fix_code   = matched.get("fix_code", "")
        applies_to = matched["applies_to"]
        severity   = matched["severity"]
    else:
        existing_ids = [e["id"] for e in db["errors"]]
        new_num    = len(existing_ids) + 1
        error_id   = f"EP-{new_num:03d}"
        name       = error_name
        desc       = f"Loi phat hien thu cong tai {file}"
        fix_code   = ""
        applies_to = ["*.py"]
        severity   = "MEDIUM"

    fingerprint = compute_fingerprint(error_id, file)
    _log_error(db, error_id, name, desc, fix, fix_code,
               applies_to, severity, file, fingerprint)
    save_error_db(db)
    print(f"\nDa ghi loi [{error_id}] vao CLAUDE.md\n")


def _log_error(db, error_id, name, description, fix, fix_code,
               applies_to, severity, file, fingerprint):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    existing = next((e for e in db["errors"] if e["id"] == error_id), None)

    if existing:
        if file not in existing["files"]:
            existing["files"].append(file)
        existing["last_seen"] = now
        existing["status"]    = "Fixed & Documented"
        entry = existing
    else:
        entry = {
            "id":          error_id,
            "name":        name,
            "description": description,
            "fix":         fix,
            "fix_code":    fix_code,
            "applies_to":  applies_to,
            "severity":    severity,
            "files":       [file],
            "first_seen":  now,
            "last_seen":   now,
            "status":      "Fixed & Documented",
            "fingerprint": fingerprint,
        }
        db["errors"].append(entry)

    update_claude_md(entry)


def watch_mode():
    import time
    print("Wisdom Error Watcher dang chay... (Ctrl+C de dung)\n")
    try:
        while True:
            scan_project()
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nWatcher stopped.")


def main():
    parser = argparse.ArgumentParser(description="Wisdom Error Watcher")
    parser.add_argument("--watch",  action="store_true")
    parser.add_argument("--scan",   action="store_true")
    parser.add_argument("--report", type=str)
    parser.add_argument("--file",   type=str, default="unknown")
    parser.add_argument("--fix",    type=str, default="")
    args = parser.parse_args()

    if args.watch:
        watch_mode()
    elif args.scan:
        scan_project()
    elif args.report:
        manual_report(args.report, args.file, args.fix)
    else:
        scan_project()


if __name__ == "__main__":
    main()