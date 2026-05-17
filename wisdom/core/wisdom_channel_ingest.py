"""
Wisdom Channel/Playlist Ingest
Ho tro: YouTube channel, playlist, TikTok channel, single video.

Usage:
    python wisdom_channel_ingest.py "https://youtube.com/@channel" --limit 20
    python wisdom_channel_ingest.py "https://youtube.com/playlist?list=xxx"
    python wisdom_channel_ingest.py "https://tiktok.com/@user" --limit 10
    python wisdom_channel_ingest.py "https://youtube.com/watch?v=xxx"  # single video
    python wisdom_channel_ingest.py "https://youtube.com/@channel" --dry-run  # preview only
"""

import sys
import os
import re
import json
import time
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ── URL type detection ────────────────────────────────────────────────────────

def detect_url_type(url: str) -> str:
    """
    Phan loai URL thanh: single | channel | playlist | tiktok_channel | tiktok_video
    """
    url = url.strip()

    # TikTok
    if "tiktok.com" in url:
        if re.search(r'tiktok\.com/@[\w.]+/video/', url):
            return "tiktok_video"
        if re.search(r'tiktok\.com/@[\w.]+/?$', url):
            return "tiktok_channel"
        return "tiktok_channel"

    # YouTube playlist
    if "playlist?list=" in url or "list=" in url:
        return "playlist"

    # YouTube channel
    if re.search(r'youtube\.com/@[\w.-]+/?$', url):
        return "channel"
    if re.search(r'youtube\.com/c/[\w.-]+/?$', url):
        return "channel"
    if re.search(r'youtube\.com/channel/[\w-]+/?$', url):
        return "channel"
    if re.search(r'youtube\.com/user/[\w-]+/?$', url):
        return "channel"

    # YouTube single video
    if "youtube.com/watch" in url or "youtu.be/" in url:
        return "single"

    return "unknown"


def get_video_urls(url: str, limit: int = 20, url_type: str = None) -> list[dict]:
    """
    Lay danh sach video URLs tu channel/playlist/single.
    Returns: list of {url, title, duration, upload_date}
    """
    if url_type is None:
        url_type = detect_url_type(url)

    print(f"  URL type: {url_type}")

    if url_type == "single":
        return [{"url": url, "title": "", "duration": 0, "upload_date": ""}]

    if url_type == "tiktok_video":
        return [{"url": url, "title": "", "duration": 0, "upload_date": ""}]

    # Channel / Playlist / TikTok channel → dung yt-dlp de lay danh sach
    print(f"  Fetching video list (limit: {limit})...")

    if url_type == "channel":
        # Them /videos de chi lay videos, khong lay shorts
        if "youtube.com/@" in url and not url.endswith("/videos"):
            fetch_url = url.rstrip("/") + "/videos"
        else:
            fetch_url = url
    else:
        fetch_url = url

    # TikTok can cookies tu browser de tranh block
    cookies_args = ["--cookies-from-browser", "chrome"] if "tiktok.com" in url else []

    cmd = [
        "yt-dlp",
        "--flat-playlist",           # Chi lay metadata, khong download
        "--playlist-end", str(limit),
        "--print", "%(url)s\t%(title)s\t%(duration)s\t%(upload_date)s",
        "--no-warnings",
        "--quiet",
        *cookies_args,
        fetch_url,
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=60, encoding="utf-8"
        )
        if result.returncode != 0:
            print(f"  yt-dlp error: {result.stderr[:200]}")
            return []

        videos = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split("\t")
            video_url = parts[0] if len(parts) > 0 else ""
            if not video_url or video_url == "NA":
                continue

            # Ensure full URL
            if not video_url.startswith("http"):
                if "tiktok.com" in url:
                    video_url = f"https://www.tiktok.com{video_url}"
                else:
                    video_url = f"https://www.youtube.com/watch?v={video_url}"

            videos.append({
                "url":         video_url,
                "title":       parts[1] if len(parts) > 1 else "",
                "duration":    int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0,
                "upload_date": parts[3] if len(parts) > 3 else "",
            })

        print(f"  Found {len(videos)} videos")
        return videos

    except subprocess.TimeoutExpired:
        print("  Timeout fetching video list")
        return []
    except FileNotFoundError:
        print("  yt-dlp not found. Install: pip install yt-dlp --break-system-packages")
        return []


# ── Dedup check ───────────────────────────────────────────────────────────────

def is_already_ingested(url: str) -> bool:
    """Kiem tra URL da duoc ingest vao Neo4j chua."""
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(
            os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
            auth=(
                os.environ.get("NEO4J_USER", "neo4j"),
                os.environ.get("NEO4J_PASS", "password123"),
            )
        )
        with driver.session() as s:
            r = s.run(
                "MATCH (v:Video {url: $url}) RETURN count(v) AS n",
                url=url
            ).single()
            exists = r["n"] > 0 if r else False
        driver.close()
        return exists
    except Exception:
        return False


# ── Main ingest loop ──────────────────────────────────────────────────────────

def ingest_channel(
    url: str,
    limit: int = 20,
    model_size: str = "base",
    delay: float = 2.0,
    dry_run: bool = False,
    skip_existing: bool = True,
    min_duration: int = 60,    # Bo qua video < 60 giay (Shorts)
    max_duration: int = 7200,  # Bo qua video > 2 tieng
):
    """
    Ingest toan bo channel/playlist vao Wisdom.

    Args:
        url          : Channel/playlist/video URL
        limit        : So video toi da (default 20)
        model_size   : Whisper model (tiny/base/small/medium)
        delay        : Giay cho giua moi video (tranh bi ban)
        dry_run      : Chi hien thi danh sach, khong ingest
        skip_existing: Bo qua video da ingest
        min_duration : Bo qua video ngan hon N giay
        max_duration : Bo qua video dai hon N giay
    """
    url_type = detect_url_type(url)

    print(f"\n{'='*60}")
    print("  WISDOM CHANNEL INGEST")
    print(f"  URL:    {url}")
    print(f"  Type:   {url_type}")
    print(f"  Limit:  {limit}")
    print(f"  Model:  {model_size}")
    print(f"  Mode:   {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"{'='*60}\n")

    if url_type == "unknown":
        print("  Khong nhan dien duoc URL type. Ho tro: YouTube channel/playlist/video, TikTok channel/video")
        return

    # Lay danh sach videos
    videos = get_video_urls(url, limit, url_type)
    if not videos:
        print("  Khong lay duoc danh sach video.")
        return

    # Filter theo duration
    filtered = []
    skipped_duration = 0
    for v in videos:
        dur = v.get("duration", 0)
        if dur > 0 and dur < min_duration:
            skipped_duration += 1
            continue
        if dur > 0 and dur > max_duration:
            skipped_duration += 1
            continue
        filtered.append(v)

    if skipped_duration:
        print(f"  Skipped {skipped_duration} videos (duration filter: {min_duration}s-{max_duration}s)")

    # Dry run: chi hien thi
    if dry_run:
        print(f"\n[DRY RUN] Se ingest {len(filtered)} videos:\n")
        for i, v in enumerate(filtered, 1):
            dur = f"{v['duration']//60}m{v['duration']%60}s" if v['duration'] else "?"
            print(f"  {i:2}. [{dur}] {v['title'][:60] or v['url'][:60]}")
        print(f"\nChay lai khong co --dry-run de ingest thuc te.")
        return

    # Ingest tung video
    success, skipped_exist, failed = 0, 0, 0
    total = len(filtered)

    for i, video in enumerate(filtered, 1):
        video_url   = video["url"]
        video_title = video.get("title", "")[:50] or video_url[:50]

        print(f"\n[{i}/{total}] {video_title}")

        # Skip neu da ingest
        if skip_existing and is_already_ingested(video_url):
            print(f"  SKIP: Da ton tai trong Wisdom")
            skipped_exist += 1
            continue

        try:
            # Tim scripts theo nhieu duong dan
            base_dir = os.path.dirname(os.path.abspath(__file__))
            repo_dir = os.path.dirname(base_dir)

            whisper_script = None
            ingest_script  = None
            for d in [base_dir, repo_dir, os.path.join(repo_dir, "wisdom", "core")]:
                w = os.path.join(d, "wisdom_whisper.py")
                i = os.path.join(d, "wisdom_ingest.py")
                if os.path.exists(w): whisper_script = w
                if os.path.exists(i): ingest_script  = i

            timeout_sec = 1200  # 20 phut cho video dai

            if whisper_script and ingest_script:
                print(f"  Using whisper pipeline...")
                result = subprocess.run(
                    [sys.executable, whisper_script,
                     video_url, "--model", model_size, "--ingest"],
                    capture_output=True, text=True,
                    timeout=timeout_sec, encoding="utf-8", errors="replace",
                )
                if result.returncode == 0:
                    print(f"  OK: Ingested via whisper")
                    success += 1
                else:
                    print(f"  Whisper fail, trying ingest direct...")
                    result2 = subprocess.run(
                        [sys.executable, ingest_script, video_url],
                        capture_output=True, text=True,
                        timeout=timeout_sec, encoding="utf-8", errors="replace",
                    )
                    if result2.returncode == 0:
                        print(f"  OK: Ingested via ingest.py")
                        success += 1
                    else:
                        print(f"  FAIL: {result2.stderr[-150:]}")
                        failed += 1
            elif ingest_script:
                print(f"  Using ingest.py directly...")
                result = subprocess.run(
                    [sys.executable, ingest_script, video_url],
                    capture_output=True, text=True,
                    timeout=timeout_sec, encoding="utf-8",
                )
                if result.returncode == 0:
                    print(f"  OK: Ingested")
                    success += 1
                else:
                    print(f"  FAIL: {result.stderr[-150:]}")
                    failed += 1
            else:
                print(f"  FAIL: Khong tim thay wisdom_ingest.py")
                failed += 1

        except subprocess.TimeoutExpired:
            print(f"  TIMEOUT (600s)")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            failed += 1

        # Delay giua cac video
        if isinstance(i, int) and i < total and delay > 0:
            print(f"  Waiting {delay}s...")
            time.sleep(delay)

    # Summary
    print(f"\n{'='*60}")
    print("  CHANNEL INGEST COMPLETE")
    print(f"  Total:    {total}")
    print(f"  Success:  {success}")
    print(f"  Skipped:  {skipped_exist} (already existed)")
    print(f"  Failed:   {failed}")
    print(f"{'='*60}\n")


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Wisdom Channel Ingest — YouTube/TikTok channel, playlist, single video"
    )
    parser.add_argument("url", help="YouTube channel/playlist/video URL hoac TikTok channel URL")
    parser.add_argument("--limit",    type=int,   default=20,    help="So video toi da (default: 20)")
    parser.add_argument("--model",    default="base",
                        choices=["tiny", "base", "small", "medium", "large-v3"],
                        help="Whisper model size (default: base)")
    parser.add_argument("--delay",    type=float, default=2.0,   help="Giay cho giua moi video (default: 2)")
    parser.add_argument("--dry-run",  action="store_true",       help="Xem danh sach video, khong ingest")
    parser.add_argument("--no-skip",  action="store_true",       help="Ingest lai ca video da ton tai")
    parser.add_argument("--min-dur",  type=int,   default=60,    help="Bo qua video ngan hon N giay (default: 60)")
    parser.add_argument("--max-dur",  type=int,   default=7200,  help="Bo qua video dai hon N giay (default: 7200)")
    args = parser.parse_args()

    ingest_channel(
        url          = args.url,
        limit        = args.limit,
        model_size   = args.model,
        delay        = args.delay,
        dry_run      = args.dry_run,
        skip_existing= not args.no_skip,
        min_duration = args.min_dur,
        max_duration = args.max_dur,
    )
