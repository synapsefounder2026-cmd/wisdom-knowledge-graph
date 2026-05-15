"""
Wisdom Whisper Pipeline — YouTube → Faster-Whisper → Wisdom
Thay the watch-cli bang local transcription mien phi, on dinh hon.

Features:
  - yt-dlp download audio (khong can ffmpeg rieng)
  - faster-whisper transcribe local (CPU ok, GPU nhanh hon)
  - Tu dong detect ngon ngu (vi/en)
  - Tich hop vao wisdom_ingest.py nhu drop-in replacement

Install (1 lan):
  pip install faster-whisper yt-dlp --break-system-packages

Usage:
  python wisdom_whisper.py <youtube_url>
  python wisdom_whisper.py <youtube_url> --model small
  python wisdom_whisper.py <youtube_url> --model medium  # chinh xac hon
"""

import sys
import os
import re
import subprocess
import tempfile
import argparse
from pathlib import Path

# Model size guide (sep chon phu hop RAM):
# tiny   : ~1GB RAM, nhanh nhat, du cho video don gian
# base   : ~1GB RAM, can bang tot (DEFAULT)
# small  : ~2GB RAM, chinh xac hon cho tieng Viet
# medium : ~5GB RAM, rat tot cho tieng Viet co accent
# large-v3: ~10GB RAM, tot nhat nhung can nhieu RAM
DEFAULT_MODEL = "base"
AUDIO_DIR = tempfile.gettempdir()


def download_audio(url: str) -> tuple[str, dict]:
    """
    Download audio tu YouTube bang yt-dlp.
    Returns: (audio_path, metadata)
    """
    print(f"[1/3] Downloading audio: {url}")
    audio_path = os.path.join(AUDIO_DIR, "wisdom_audio.m4a")

    # Xoa file cu neu co
    if os.path.exists(audio_path):
        os.remove(audio_path)

    # Download audio only (nhanh hon video)
    cmd = [
        "yt-dlp",
        "--format", "bestaudio[ext=m4a]/bestaudio/best",
        "--output", audio_path,
        "--no-playlist",
        "--write-info-json",
        "--quiet",
        "--no-warnings",
        url
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if result.returncode != 0:
            print(f"  yt-dlp error: {result.stderr[:200]}")
            return "", {}
    except subprocess.TimeoutExpired:
        print("  yt-dlp timeout (180s)")
        return "", {}
    except FileNotFoundError:
        print("  yt-dlp not found. Install: pip install yt-dlp --break-system-packages")
        return "", {}

    # Doc metadata tu JSON neu co
    meta = {}
    info_path = audio_path.replace(".m4a", ".info.json") + ".info.json"
    alt_info = audio_path + ".info.json"
    for p in [info_path, alt_info, audio_path.replace(".m4a", "") + ".info.json"]:
        if os.path.exists(p):
            import json
            try:
                with open(p, encoding="utf-8") as f:
                    raw = json.load(f)
                    meta = {
                        "title": raw.get("title", ""),
                        "duration": raw.get("duration", 0),
                        "uploader": raw.get("uploader", ""),
                        "description": raw.get("description", "")[:500],
                        "view_count": raw.get("view_count", 0),
                    }
            except Exception:
                pass
            break

    # Tim file audio (yt-dlp co the them extension khac)
    actual_path = audio_path
    if not os.path.exists(actual_path):
        for ext in [".webm", ".opus", ".mp3", ".wav"]:
            alt = audio_path.replace(".m4a", ext)
            if os.path.exists(alt):
                actual_path = alt
                break

    if not os.path.exists(actual_path):
        print("  Audio file not found after download")
        return "", meta

    size_mb = os.path.getsize(actual_path) / 1024 / 1024
    print(f"  Downloaded: {size_mb:.1f} MB | Title: {meta.get('title', 'unknown')[:60]}")
    return actual_path, meta


def transcribe_audio(audio_path: str, model_size: str = DEFAULT_MODEL) -> dict:
    """
    Transcribe audio bang faster-whisper local.
    Returns: {"transcript": str, "language": str, "segments": list}
    """
    print(f"[2/3] Transcribing with faster-whisper ({model_size})...")
    print(f"  (Lan dau chay se download model ~{_model_size_mb(model_size)}MB)")

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("  faster-whisper chua cai. Chay: pip install faster-whisper --break-system-packages")
        return {}

    # Auto-detect GPU, fallback CPU
    try:
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute = "float16" if device == "cuda" else "int8"
    except ImportError:
        device = "cpu"
        compute = "int8"

    print(f"  Device: {device} | Compute: {compute}")

    try:
        model = WhisperModel(model_size, device=device, compute_type=compute)

        # Transcribe — tu dong detect ngon ngu, uu tien vi va en
        segments_iter, info = model.transcribe(
            audio_path,
            beam_size=5,
            language=None,          # auto-detect
            vad_filter=True,        # bo silence, giam hallucination
            vad_parameters=dict(min_silence_duration_ms=500),
        )

        print(f"  Detected language: {info.language} "
              f"(confidence: {info.language_probability:.0%})")

        # Collect segments
        segments = []
        full_text_parts = []
        for seg in segments_iter:
            text = seg.text.strip()
            if text:
                segments.append({
                    "start": round(seg.start, 2),
                    "end": round(seg.end, 2),
                    "text": text
                })
                full_text_parts.append(text)

        full_transcript = " ".join(full_text_parts)
        print(f"  Transcript: {len(full_transcript):,} chars | {len(segments)} segments")

        return {
            "transcript": full_transcript,
            "language": info.language,
            "segments": segments,
        }

    except Exception as e:
        print(f"  Transcription error: {e}")
        return {}


def _model_size_mb(model_size: str) -> str:
    sizes = {
        "tiny": "~150", "base": "~290", "small": "~970",
        "medium": "~3000", "large-v3": "~6000"
    }
    return sizes.get(model_size, "?")


def wisdom_whisper_ingest(url: str, model_size: str = DEFAULT_MODEL) -> dict:
    """
    Full pipeline: YouTube URL → transcript + metadata.
    Drop-in replacement cho run_watch_cli() trong wisdom_ingest.py.

    Returns dict compatible voi wisdom_ingest.py data format:
    {
        "url": str,
        "video": str,      # title
        "duration": int,   # seconds
        "transcript": str, # full text
        "language": str,   # vi/en
        "segments": list,  # timed segments
        "frames": []       # empty (khong download frames)
    }
    """
    print(f"\n{'='*60}")
    print("  WISDOM WHISPER PIPELINE")
    print(f"  URL: {url}")
    print(f"  Model: {model_size}")
    print(f"{'='*60}\n")

    # Step 1: Download
    audio_path, meta = download_audio(url)
    if not audio_path:
        return {"url": url, "video": "", "duration": 0,
                "transcript": "", "language": "", "segments": [], "frames": []}

    # Step 2: Transcribe
    result = transcribe_audio(audio_path, model_size)

    # Step 3: Cleanup audio
    try:
        os.remove(audio_path)
        print(f"[3/3] Cleaned up audio file")
    except Exception:
        pass

    if not result:
        return {"url": url, "video": meta.get("title", ""), "duration": meta.get("duration", 0),
                "transcript": "", "language": "", "segments": [], "frames": []}

    print(f"\n  Transcript length: {len(result['transcript']):,} chars")
    print(f"  Language: {result['language']}")
    print(f"  Duration: {meta.get('duration', 0)}s")

    return {
        "url": url,
        "video": meta.get("title", ""),
        "duration": meta.get("duration", 0),
        "transcript": result["transcript"],
        "language": result["language"],
        "segments": result["segments"],
        "frames": [],
        # Bonus metadata
        "uploader": meta.get("uploader", ""),
        "description": meta.get("description", ""),
        "view_count": meta.get("view_count", 0),
    }


# ── CLI standalone ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Wisdom Whisper — YouTube transcriber")
    parser.add_argument("url", help="YouTube URL")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        choices=["tiny", "base", "small", "medium", "large-v3"],
                        help="Whisper model size (default: base)")
    parser.add_argument("--ingest", action="store_true",
                        help="Pipe output to wisdom_ingest.py")
    args = parser.parse_args()

    data = wisdom_whisper_ingest(args.url, args.model)

    if data["transcript"]:
        print("\n" + "="*60)
        print("TRANSCRIPT PREVIEW (first 500 chars):")
        print(data["transcript"][:500])
        print("="*60)

        if args.ingest:
            # Pipe vao wisdom_ingest
            import sys
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            try:
                from wisdom_ingest import analyze_with_ollama, save_to_neo4j, save_to_qdrant
                import hashlib
                from datetime import datetime

                print("\nPiping to Wisdom ingest pipeline...")
                analysis = analyze_with_ollama(
                    data["transcript"], args.url, data["duration"]
                )
                content_id, neo4j_id = save_to_neo4j(data, analysis)
                save_to_qdrant(content_id, neo4j_id, data, analysis)
                print(f"\nIngested! content_id={content_id}")
            except Exception as e:
                print(f"Ingest error: {e}")
    else:
        print("\nNo transcript generated. Check URL or try --model small")
        sys.exit(1)
