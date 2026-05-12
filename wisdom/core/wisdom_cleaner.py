"""
wisdom_cleaner.py
==================
P-023: Web Content Cleaner — trafilatura-based, local, MIT license.
Khong can API key, khong gui data ra ngoai.

Chuc nang:
- Remove: ads, nav, footer, cookie banners, scripts
- Extract: main content, title, author, publish date
- Convert: HTML -> clean Markdown
- Output: structured dict {title, content, url, date, word_count, language}

Tich hop vao:
- wisdom_ingest.py (webpage mode)
- wisdom_fb_ingest.py (post content cleaning)
- POST /api/clip (Wisdom Lens P-043)

Usage:
    from wisdom_cleaner import WisdomCleaner
    cleaner = WisdomCleaner()
    result = cleaner.clean_url("https://example.com/article")
    result = cleaner.clean_html(html_string, url="https://example.com")

    python wisdom/core/wisdom_cleaner.py --url "https://vnexpress.net/..."
    python wisdom/core/wisdom_cleaner.py --test
"""

import os
import re
import sys
import argparse
import hashlib
from datetime import datetime

try:
    import trafilatura
    from trafilatura.settings import use_config
    HAS_TRAFILATURA = True
except ImportError:
    HAS_TRAFILATURA = False
    print("  WARNING: trafilatura chua cai — pip install trafilatura")

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ── Strip emoji ───────────────────────────────────────────────────────────────
def strip_emoji(text: str) -> str:
    if not isinstance(text, str):
        return str(text) if text else ""
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        u"\U00002600-\U000027BF"
        u"\U0001F900-\U0001F9FF"
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub("", text).strip()


# ── Config ────────────────────────────────────────────────────────────────────
MIN_CONTENT_LENGTH = 100  # chars — bo qua neu qua ngan
MAX_CONTENT_LENGTH = 50000  # chars — cap o 50k chars


class WisdomCleaner:

    def __init__(self):
        if not HAS_TRAFILATURA:
            raise ImportError("pip install trafilatura")
        # Config trafilatura: tat logging nhieu
        self.config = use_config()
        self.config.set("DEFAULT", "EXTRACTION_TIMEOUT", "30")

    def clean_url(self, url: str, language: str = None) -> dict:
        """
        Download va clean noi dung tu URL.
        Returns: {title, content, url, date, word_count, language, content_hash}
        """
        url = strip_emoji(url.strip())
        print(f"  [Cleaner] Fetching: {url[:80]}...")

        try:
            # Download
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                return self._empty_result(url, "Fetch failed")

            return self._extract(downloaded, url, language)

        except Exception as e:
            return self._empty_result(url, f"Error: {e}")

    def clean_html(self, html: str, url: str = "", language: str = None) -> dict:
        """
        Clean HTML string da co san (tu Wisdom Lens P-043 hoac FB ingest).
        Returns: {title, content, url, date, word_count, language, content_hash}
        """
        url = strip_emoji(url.strip()) if url else ""
        return self._extract(html, url, language)

    def _extract(self, downloaded: str, url: str, language: str = None) -> dict:
        """Core extraction logic dung trafilatura."""
        try:
            # Extract metadata
            metadata = trafilatura.extract_metadata(downloaded, default_url=url)

            # Extract main content -> Markdown
            content = trafilatura.extract(
                downloaded,
                url=url,
                include_comments=False,
                include_tables=True,
                no_fallback=False,
                favor_precision=True,
                output_format="markdown",
            )

            if not content or len(content.strip()) < MIN_CONTENT_LENGTH:
                # Fallback: thu voi favor_recall
                content = trafilatura.extract(
                    downloaded,
                    url=url,
                    include_comments=False,
                    favor_precision=False,
                    output_format="markdown",
                )

            if not content:
                return self._empty_result(url, "No content extracted")

            # Clean content
            content = strip_emoji(content.strip())
            content = content[:MAX_CONTENT_LENGTH]

            # Extract fields tu metadata
            title = ""
            date  = ""
            author = ""
            detected_lang = language or "en"

            if metadata:
                title  = strip_emoji(metadata.title or "")
                date   = str(metadata.date or "")
                author = strip_emoji(str(metadata.author or ""))
                if metadata.language:
                    detected_lang = metadata.language

            # Word count
            word_count = len(content.split())

            # Content hash (dung cho dedup)
            content_hash = hashlib.sha256(
                f"{url}{content[:500]}".encode("utf-8")
            ).hexdigest()

            result = {
                "title":        title or self._extract_title_fallback(content),
                "content":      content,
                "url":          url,
                "date":         date or datetime.now().isoformat(),
                "author":       author,
                "word_count":   word_count,
                "language":     detected_lang,
                "content_hash": content_hash,
                "success":      True,
                "error":        None,
            }

            print(f"  [Cleaner] OK: {word_count} words | lang={detected_lang} | {title[:50]}")
            return result

        except Exception as e:
            return self._empty_result(url, f"Extraction error: {e}")

    def _extract_title_fallback(self, content: str) -> str:
        """Lay dong dau tien lam title neu metadata khong co."""
        lines = [l.strip() for l in content.split("\n") if l.strip()]
        if lines:
            # Bo markdown heading markers
            first = re.sub(r"^#+\s*", "", lines[0])
            return first[:100]
        return "Untitled"

    def _empty_result(self, url: str, error: str) -> dict:
        print(f"  [Cleaner] FAIL: {error}")
        return {
            "title":        "",
            "content":      "",
            "url":          url,
            "date":         datetime.now().isoformat(),
            "author":       "",
            "word_count":   0,
            "language":     "en",
            "content_hash": "",
            "success":      False,
            "error":        error,
        }

    def batch_clean(self, urls: list[str]) -> list[dict]:
        """Clean nhieu URLs, bo qua loi."""
        results = []
        for i, url in enumerate(urls):
            print(f"\n  [{i+1}/{len(urls)}] {url[:60]}...")
            result = self.clean_url(url)
            results.append(result)
        successful = sum(1 for r in results if r["success"])
        print(f"\n  [Cleaner] Batch done: {successful}/{len(urls)} successful")
        return results


# ── Quick Test ────────────────────────────────────────────────────────────────

TEST_URLS = [
    "https://vnexpress.net/kinh-doanh",
    "https://techcrunch.com",
    "https://arxiv.org/abs/1512.06808",
]

def run_test():
    print("\n" + "="*60)
    print("  WISDOM CLEANER — Test Mode")
    print("="*60)

    cleaner = WisdomCleaner()

    for url in TEST_URLS:
        print(f"\n  Testing: {url}")
        result = cleaner.clean_url(url)
        print(f"  Title:      {result['title'][:60]}")
        print(f"  Words:      {result['word_count']}")
        print(f"  Language:   {result['language']}")
        print(f"  Success:    {result['success']}")
        if result['content']:
            print(f"  Preview:    {result['content'][:150]}...")
        print(f"  Hash:       {result['content_hash'][:16]}...")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Wisdom Web Content Cleaner")
    parser.add_argument("--url",  type=str, help="URL can clean")
    parser.add_argument("--test", action="store_true", help="Chay test voi 3 URLs mau")
    args = parser.parse_args()

    if args.test:
        run_test()
    elif args.url:
        cleaner = WisdomCleaner()
        result = cleaner.clean_url(args.url)
        print(f"\n  Title:    {result['title']}")
        print(f"  Words:    {result['word_count']}")
        print(f"  Language: {result['language']}")
        print(f"  Success:  {result['success']}")
        if result['content']:
            print(f"\n  Content preview:\n{result['content'][:500]}")
    else:
        parser.print_help()
        print("\n  Quick test:")
        print("  python wisdom/core/wisdom_cleaner.py --test")
        print("  python wisdom/core/wisdom_cleaner.py --url https://vnexpress.net")


if __name__ == "__main__":
    main()
