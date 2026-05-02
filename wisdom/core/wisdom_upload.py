"""
Wisdom Manual Upload Pipeline
Hỗ trợ: PDF, Word, PPT, Excel, TXT, MD, Audio, Video, Image, EPUB

Usage:
    python wisdom_upload.py <file_path>
    python wisdom_upload.py "C:/Users/LENOVO/Documents/report.pdf"
    python wisdom_upload.py "C:/Users/LENOVO/Downloads/lecture.mp3"
"""

import os
import sys
import hashlib
import json
import requests
from datetime import datetime
from pathlib import Path

# ── Optional imports (graceful fallback) ─────────────────────────────────────
try:
    from PyPDF2 import PdfReader
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

try:
    from docx import Document
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

try:
    from pptx import Presentation
    HAS_PPTX = True
except ImportError:
    HAS_PPTX = False

try:
    import openpyxl
    HAS_XLSX = True
except ImportError:
    HAS_XLSX = False

try:
    from PIL import Image
    import pytesseract
    HAS_OCR = True
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
except ImportError:
    HAS_OCR = False

try:
    import ebooklib
    from ebooklib import epub
    from html.parser import HTMLParser
    HAS_EPUB = True
except ImportError:
    HAS_EPUB = False

from neo4j import GraphDatabase
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance

# ── Config ───────────────────────────────────────────────────────────────────
OLLAMA_BASE  = "http://localhost:11434"
OLLAMA_MODEL = "llama3.1:8b"
EMBED_MODEL  = "nomic-embed-text"
NEO4J_URI    = "bolt://localhost:7687"
NEO4J_USER   = "neo4j"
NEO4J_PASS   = "password123"
QDRANT_HOST  = "localhost"
QDRANT_PORT  = 6333
COLLECTION   = "wisdom_knowledge"
VECTOR_SIZE  = 768

# Supported extensions
SUPPORTED = {
    "document": [".pdf", ".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls", ".txt", ".md"],
    "audio":    [".mp3", ".wav", ".m4a", ".ogg", ".flac"],
    "video":    [".mp4", ".mov", ".avi", ".mkv", ".webm"],
    "image":    [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"],
    "ebook":    [".epub"],
}

# ── Text Extractors ───────────────────────────────────────────────────────────

def extract_pdf(path: str) -> str:
    if not HAS_PDF:
        return "[PyPDF2 not installed]"
    
    # Thử text-based trước
    reader = PdfReader(path)
    text = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            text.append(t)
    
    if text and len(" ".join(text).strip()) > 50:
        return "\n".join(text)
    
    # Fallback: OCR cho scanned PDF
    print("  🔍  Text-based failed, trying OCR...")
    try:
        from pdf2image import convert_from_path
        poppler_path = r"C:\poppler\poppler-25.12.0\Library\bin"
        images = convert_from_path(path, poppler_path=poppler_path)
        ocr_text = []
        for i, img in enumerate(images):
            print(f"  📖  OCR page {i+1}/{len(images)}...")
            t = pytesseract.image_to_string(img, lang="eng")
            if t.strip():
                ocr_text.append(t)
        return "\n".join(ocr_text)
    except Exception as e:
        return f"[OCR failed: {e}]"

def extract_docx(path: str) -> str:
    if not HAS_DOCX:
        return "[python-docx not installed]"
    doc = Document(path)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])


def extract_pptx(path: str) -> str:
    if not HAS_PPTX:
        return "[python-pptx not installed]"
    prs = Presentation(path)
    text = []
    for i, slide in enumerate(prs.slides):
        slide_text = []
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                slide_text.append(shape.text.strip())
        if slide_text:
            text.append(f"[Slide {i+1}] " + " | ".join(slide_text))
    return "\n".join(text)


def extract_xlsx(path: str) -> str:
    if not HAS_XLSX:
        return "[openpyxl not installed]"
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    text = []
    for sheet in wb.sheetnames:
        ws = wb[sheet]
        text.append(f"[Sheet: {sheet}]")
        for row in ws.iter_rows(values_only=True):
            row_text = " | ".join([str(c) for c in row if c is not None])
            if row_text.strip():
                text.append(row_text)
    return "\n".join(text)


def extract_txt(path: str) -> str:
    for enc in ["utf-8", "utf-16", "latin-1"]:
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except:
            continue
    return "[Could not read text file]"


def extract_image_ocr(path: str) -> str:
    if not HAS_OCR:
        return "[pytesseract/Pillow not installed]"
    try:
        img = Image.open(path)
        return pytesseract.image_to_string(img, lang="eng+vie")
    except Exception as e:
        return f"[OCR failed: {e}]"


def extract_epub(path: str) -> str:
    if not HAS_EPUB:
        return "[ebooklib not installed]"

    class MLStripper(HTMLParser):
        def __init__(self):
            super().__init__()
            self.reset()
            self.fed = []
        def handle_data(self, d):
            self.fed.append(d)
        def get_data(self):
            return " ".join(self.fed)

    book = epub.read_epub(path)
    text = []
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            s = MLStripper()
            s.feed(item.get_content().decode("utf-8", errors="ignore"))
            t = s.get_data().strip()
            if t:
                text.append(t)
    return "\n".join(text)


def transcribe_audio(path: str) -> str:
    """Dùng Groq API để transcribe audio (giống watch-cli)."""
    print(f"  🎙️  Transcribing audio via Groq...")
    groq_key = os.environ.get("GROQ_API_KEY", "")
    if not groq_key:
        # Try read từ watch-cli config
        env_path = os.path.expanduser("~/.config/watch-cli/env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    if line.startswith("GROQ_API_KEY="):
                        groq_key = line.split("=", 1)[1].strip()
                        break

    if not groq_key:
        return "[No GROQ_API_KEY found]"

    with open(path, "rb") as f:
        response = requests.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {groq_key}"},
            files={"file": (os.path.basename(path), f)},
            data={"model": "whisper-large-v3-turbo", "response_format": "text"},
            timeout=120
        )
    if response.status_code == 200:
        return response.text.strip()
    return f"[Transcription failed: {response.text}]"


def transcribe_video(path: str) -> str:
    """Extract audio từ video rồi transcribe."""
    import subprocess
    import tempfile
    print(f"  🎬  Extracting audio from video...")
    audio_path = path.rsplit(".", 1)[0] + "_audio.mp3"
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", path, "-vn", "-ac", "1", "-ar", "16000",
             "-b:a", "32k", "-f", "mp3", audio_path],
            capture_output=True, check=True
        )
        text = transcribe_audio(audio_path)
        os.remove(audio_path)
        return text
    except Exception as e:
        return f"[Video transcription failed: {e}]"

# ── File Type Detector ────────────────────────────────────────────────────────

def detect_type(path: str) -> tuple[str, str]:
    """Returns (category, extension)"""
    ext = Path(path).suffix.lower()
    for category, exts in SUPPORTED.items():
        if ext in exts:
            return category, ext
    return "unknown", ext


def extract_content(path: str) -> str:
    """Extract text content từ bất kỳ file nào."""
    category, ext = detect_type(path)

    print(f"  📄  Extracting content [{category}|{ext}]...")

    if ext == ".pdf":
        return extract_pdf(path)
    elif ext in [".docx", ".doc"]:
        return extract_docx(path)
    elif ext in [".pptx", ".ppt"]:
        return extract_pptx(path)
    elif ext in [".xlsx", ".xls"]:
        return extract_xlsx(path)
    elif ext in [".txt", ".md"]:
        return extract_txt(path)
    elif ext == ".epub":
        return extract_epub(path)
    elif category == "image":
        return extract_image_ocr(path)
    elif category == "audio":
        return transcribe_audio(path)
    elif category == "video":
        return transcribe_video(path)
    else:
        return f"[Unsupported format: {ext}]"

# ── AI Analysis ───────────────────────────────────────────────────────────────

def analyze_with_ollama(content: str, filename: str) -> dict:
    print(f"  🧠  Analyzing with {OLLAMA_MODEL}...")
    prompt = f"""Analyze this document and extract structured knowledge.
Return ONLY valid JSON, no markdown, no explanation.

Filename: {filename}
Content (first 3000 chars): {content[:3000]}

Return this exact JSON structure:
{{
  "title": "document title or topic",
  "summary": "2-3 sentence summary",
  "key_concepts": ["concept1", "concept2", "concept3"],
  "insights": ["insight1", "insight2"],
  "tags": ["tag1", "tag2", "tag3"],
  "language": "vi or en",
  "document_type": "book/article/report/lecture/note/data/other",
  "value_flywheel": "learning/experience/earning/contribution/growth"
}}"""

    response = requests.post(
        f"{OLLAMA_BASE}/api/generate",
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=120
    )
    raw = response.json().get("response", "{}").strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        return json.loads(raw)
    except:
        return {
            "title": filename,
            "summary": content[:200],
            "key_concepts": [],
            "insights": [],
            "tags": [],
            "language": "en",
            "document_type": "other",
            "value_flywheel": "learning"
        }

# ── Storage ───────────────────────────────────────────────────────────────────

def get_embedding(text: str) -> list:
    response = requests.post(
        f"{OLLAMA_BASE}/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=60
    )
    return response.json().get("embedding", [])


def save_to_neo4j(file_id: str, path: str, analysis: dict):
    print(f"  🗄️   Saving to Neo4j...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    filename = Path(path).name

    with driver.session() as session:
        session.run("""
            MERGE (d:Document {id: $id})
            SET d.filename = $filename,
                d.path = $path,
                d.title = $title,
                d.summary = $summary,
                d.document_type = $doc_type,
                d.language = $language,
                d.value_flywheel = $flywheel,
                d.ingested_at = $ingested_at
        """, id=file_id, filename=filename, path=path,
             title=analysis.get("title", ""),
             summary=analysis.get("summary", ""),
             doc_type=analysis.get("document_type", "other"),
             language=analysis.get("language", "en"),
             flywheel=analysis.get("value_flywheel", "learning"),
             ingested_at=datetime.now().isoformat())

        for concept in analysis.get("key_concepts", []):
            session.run("""
                MERGE (c:Concept {name: $name})
                WITH c
                MATCH (d:Document {id: $doc_id})
                MERGE (d)-[:HAS_CONCEPT]->(c)
            """, name=concept, doc_id=file_id)

        for tag in analysis.get("tags", []):
            session.run("""
                MERGE (t:Tag {name: $name})
                WITH t
                MATCH (d:Document {id: $doc_id})
                MERGE (d)-[:HAS_TAG]->(t)
            """, name=tag, doc_id=file_id)

    driver.close()
    print(f"  ✅  Neo4j: Document node + {len(analysis.get('key_concepts', []))} concepts saved")


def save_to_qdrant(file_id: str, path: str, content: str, analysis: dict):
    print(f"  🔍  Saving to Qdrant...")
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION not in existing:
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
        )

    text_to_embed = f"{analysis.get('title', '')} {analysis.get('summary', '')} {content[:1000]}"
    embedding = get_embedding(text_to_embed)

    if len(embedding) != VECTOR_SIZE:
        print(f"  ⚠️   Embedding size mismatch, skipping Qdrant")
        return

    point_id = int(hashlib.md5(file_id.encode()).hexdigest()[:8], 16)
    client.upsert(
        collection_name=COLLECTION,
        points=[PointStruct(
            id=point_id,
            vector=embedding,
            payload={
                "file_id": file_id,
                "filename": Path(path).name,
                "path": path,
                "title": analysis.get("title", ""),
                "summary": analysis.get("summary", ""),
                "tags": analysis.get("tags", []),
                "key_concepts": analysis.get("key_concepts", []),
                "document_type": analysis.get("document_type", "other"),
                "value_flywheel": analysis.get("value_flywheel", "learning"),
                "source": "manual_upload",
                "ingested_at": datetime.now().isoformat()
            }
        )]
    )
    print(f"  ✅  Qdrant: Vector saved to '{COLLECTION}'")

# ── Main ──────────────────────────────────────────────────────────────────────

def upload(path: str):
    path = os.path.abspath(path)

    print(f"\n{'='*60}")
    print(f"  WISDOM MANUAL UPLOAD")
    print(f"{'='*60}")
    print(f"  File: {Path(path).name}")

    # Validate
    if not os.path.exists(path):
        print(f"❌ File not found: {path}")
        return

    category, ext = detect_type(path)
    if category == "unknown":
        print(f"❌ Unsupported format: {ext}")
        print(f"   Supported: {[e for exts in SUPPORTED.values() for e in exts]}")
        return

    print(f"  Type: {category} ({ext})")
    print(f"  Size: {os.path.getsize(path) / 1024:.1f} KB\n")

    # Step 1: Extract content
    content = extract_content(path)
    if not content or len(content.strip()) < 10:
        print("❌ Could not extract content from file.")
        return
    print(f"  📝  Extracted: {len(content)} chars")

    # Step 2: Analyze
    filename = Path(path).name
    analysis = analyze_with_ollama(content, filename)
    print(f"  💡  Title: {analysis.get('title')}")
    print(f"  🏷️   Concepts: {', '.join(analysis.get('key_concepts', []))}")
    print(f"  📚  Type: {analysis.get('document_type')} | Flywheel: {analysis.get('value_flywheel')}")

    # Step 3: Generate ID
    file_id = hashlib.md5(f"{path}{os.path.getmtime(path)}".encode()).hexdigest()[:12]

    # Step 4: Save
    save_to_neo4j(file_id, path, analysis)
    save_to_qdrant(file_id, path, content, analysis)

    print(f"\n{'='*60}")
    print(f"  ✅  UPLOAD COMPLETE")
    print(f"  File ID: {file_id}")
    print(f"  Now searchable via: python wisdom_query.py \"<question>\"")
    print(f"{'='*60}\n")

    return {"file_id": file_id, "analysis": analysis}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python wisdom_upload.py <file_path>")
        print("Example: python wisdom_upload.py report.pdf")
        sys.exit(1)
    upload(sys.argv[1])