"""
wisdom_cleaner.py — P-023 / P-051
Clean web content + convert any file to Markdown
Powered by: Microsoft markitdown (MIT license)
"""

import os
import re
import hashlib
from pathlib import Path
from datetime import datetime

try:
    from markitdown import MarkItDown
    md_converter = MarkItDown()
    print("✓ markitdown ready")
except ImportError:
    md_converter = None
    print("⚠ markitdown not installed: pip install markitdown")

try:
    import requests
    requests_available = True
except ImportError:
    requests_available = False


# ── CLEAN TEXT ─────────────────────────────────────────────
def clean_text(text: str) -> str:
    """Remove noise, normalize whitespace"""
    if not text:
        return ""
    # Remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {3,}', ' ', text)
    # Remove common web noise patterns
    noise = [
        r'Cookie Policy.*?\n',
        r'Accept All Cookies.*?\n',
        r'Subscribe to.*?newsletter.*?\n',
        r'Follow us on.*?\n',
    ]
    for pattern in noise:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    return text.strip()


# ── CONVERT FILE ───────────────────────────────────────────
def convert_file(file_path: str) -> dict:
    """
    Convert any file to Markdown using markitdown.
    Supports: PDF, DOCX, PPTX, XLSX, HTML, TXT, MD, audio
    """
    if not md_converter:
        return {"error": "markitdown not installed", "content": ""}

    path = Path(file_path)
    if not path.exists():
        return {"error": f"File not found: {file_path}", "content": ""}

    try:
        result = md_converter.convert(file_path)
        content = clean_text(result.text_content or "")
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        return {
            "title": result.title or path.stem,
            "content": content,
            "content_hash": content_hash,
            "source_url": str(path),
            "word_count": len(content.split()),
            "file_type": path.suffix.lower(),
            "converted_at": datetime.now().isoformat(),
            "error": None
        }
    except Exception as e:
        return {"error": str(e), "content": "", "title": path.stem}


# ── CONVERT URL ────────────────────────────────────────────
def convert_url(url: str) -> dict:
    """
    Fetch URL and convert to clean Markdown.
    """
    if not md_converter:
        return {"error": "markitdown not installed", "content": ""}

    if not url.startswith("http"):
        return {"error": "Invalid URL", "content": ""}

    try:
        result = md_converter.convert_url(url)
        content = clean_text(result.text_content or "")
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        # Extract domain for metadata
        from urllib.parse import urlparse
        domain = urlparse(url).netloc

        return {
            "title": result.title or url[:80],
            "content": content,
            "content_hash": content_hash,
            "source_url": url,
            "domain": domain,
            "word_count": len(content.split()),
            "converted_at": datetime.now().isoformat(),
            "error": None
        }
    except Exception as e:
        return {"error": str(e), "content": "", "title": url[:80], "source_url": url}


# ── CONVERT TEXT ───────────────────────────────────────────
def convert_text(text: str, title: str = "", source_url: str = "") -> dict:
    """
    Clean raw text content (from FB clips, paste, etc.)
    """
    content = clean_text(text)
    content_hash = hashlib.sha256(content.encode()).hexdigest()

    return {
        "title": title or content[:60] + "...",
        "content": content,
        "content_hash": content_hash,
        "source_url": source_url,
        "word_count": len(content.split()),
        "converted_at": datetime.now().isoformat(),
        "error": None
    }


# ── MAIN ENTRY POINT ───────────────────────────────────────
def clean(source: str, title: str = "") -> dict:
    """
    Universal cleaner — auto-detect input type.
    source: URL, file path, or raw text
    """
    if source.startswith("http://") or source.startswith("https://"):
        return convert_url(source)
    elif Path(source).exists():
        return convert_file(source)
    else:
        return convert_text(source, title=title)


# ── CLI TEST ───────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python wisdom_cleaner.py <url|file|text>")
        print("Examples:")
        print("  python wisdom_cleaner.py https://example.com")
        print("  python wisdom_cleaner.py document.pdf")
        sys.exit(1)

    source = sys.argv[1]
    print(f"\n🌿 Wisdom Cleaner — Processing: {source[:60]}")
    print("─" * 50)

    result = clean(source)

    if result.get("error"):
        print(f"❌ Error: {result['error']}")
    else:
        print(f"✓ Title:      {result.get('title', '—')}")
        print(f"✓ Words:      {result.get('word_count', 0)}")
        print(f"✓ Hash:       {result.get('content_hash', '—')[:16]}...")
        print(f"✓ Converted:  {result.get('converted_at', '—')}")
        print(f"\n── Content preview ──")
        print(result.get('content', '')[:500])
        print("...")

    # Save full result
    out_file = "wisdom_cleaner_output.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n✓ Full output saved: {out_file}")
