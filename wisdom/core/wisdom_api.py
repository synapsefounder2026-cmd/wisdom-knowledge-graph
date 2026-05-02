"""
Wisdom API Server
Nhan URL tu bookmarklet -> trigger ingest pipeline tu dong

Usage:
    python wisdom/core/wisdom_api.py
    Server chay tai http://localhost:8000
"""

import json
import subprocess
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

PORT = 8000
BASH_EXE = "C:/Program Files/Git/bin/bash.exe"
PROJECT_ROOT = "C:/Users/LENOVO/wisdom-knowledge-graph"


class WisdomHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        print("  [%s] %s" % (datetime.now().strftime('%H:%M:%S'), format % args))

    def send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        if self.path == '/health':
            self.send_json({"status": "ok", "wisdom": "running", "time": datetime.now().isoformat()})
        elif self.path == '/stats':
            self.send_json(self.get_stats())
        else:
            self.send_json({"error": "Not found"}, 404)

    def do_POST(self):
        if self.path == '/ingest':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body)
                result = self.handle_ingest(data)
                self.send_json(result)
            except json.JSONDecodeError:
                self.send_json({"status": "error", "message": "Invalid JSON"}, 400)
        else:
            self.send_json({"error": "Not found"}, 404)

    def handle_ingest(self, data):
        url = data.get('url', '').strip()
        title = data.get('title', '')
        platform = data.get('platform', 'unknown')

        if not url:
            return {"status": "error", "message": "No URL provided"}

        print("\n  [IN] New capture from bookmarklet:")
        print("     Platform : %s" % platform)
        print("     Title    : %s" % title[:60])
        print("     URL      : %s" % url[:80])

        if self.is_video_url(url, platform):
            return self.ingest_video(url, platform)
        else:
            return self.ingest_webpage(url, platform, title)

    def is_video_url(self, url, platform):
        video_platforms = ['youtube', 'facebook', 'tiktok', 'twitter']
        video_patterns = ['youtube.com/watch', 'youtu.be/', 'fb.watch', 'tiktok.com/@', '/video/', '/reel/']
        if platform in video_platforms:
            return True
        return any(p in url for p in video_patterns)

    def ingest_video(self, url, platform):
        print("  [VIDEO] Routing to video ingest pipeline...")
        try:
            ingest_script = os.path.join(PROJECT_ROOT, 'wisdom', 'core', 'wisdom_ingest.py')
            cmd = "python '%s' '%s'" % (ingest_script, url)
            print("  [DEBUG] Running: %s" % cmd)

            result = subprocess.run(
                [BASH_EXE, "-c", cmd],
                capture_output=True, text=True, encoding='utf-8',
                timeout=300
            )

            print("  [DEBUG] returncode: %s" % result.returncode)
            print("  [DEBUG] stdout: %s" % result.stdout[:500])
            print("  [DEBUG] stderr: %s" % result.stderr[:500])

            if result.returncode == 0:
                print("  [OK] Video ingested successfully!")
                return {
                    "status": "ok",
                    "type": "video",
                    "platform": platform,
                    "message": "Video from %s ingested into Wisdom!" % platform,
                }
            else:
                print("  [ERROR] %s" % result.stderr[:500])
                return {"status": "error", "message": result.stderr[:300] or "Ingest failed"}

        except subprocess.TimeoutExpired:
            return {"status": "error", "message": "Timeout - video too long or network slow"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def ingest_webpage(self, url, platform, title):
        print("  [WEB] Routing to webpage ingest pipeline...")
        try:
            import requests as req
            from bs4 import BeautifulSoup
            import tempfile, hashlib

            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            response = req.get(url, headers=headers, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')

            for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                tag.decompose()
            text = soup.get_text(separator='\n', strip=True)
            text = '\n'.join(line for line in text.split('\n') if len(line) > 30)

            if len(text) < 100:
                return {"status": "error", "message": "Could not extract content from page"}

            temp_path = os.path.join(
                tempfile.gettempdir(),
                "wisdom_web_%s.txt" % hashlib.md5(url.encode()).hexdigest()[:8]
            )
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write("Source: %s\nTitle: %s\n\n%s" % (url, title, text[:10000]))

            upload_script = os.path.join(PROJECT_ROOT, 'wisdom', 'core', 'wisdom_upload.py')
            result = subprocess.run(
                [sys.executable, upload_script, temp_path],
                capture_output=True, text=True, encoding='utf-8',
                timeout=120
            )
            os.remove(temp_path)

            if result.returncode == 0:
                print("  [OK] Webpage ingested successfully!")
                return {"status": "ok", "type": "webpage", "platform": platform, "message": "Page ingested into Wisdom!"}
            else:
                return {"status": "error", "message": result.stderr[:300]}

        except ImportError:
            return {"status": "error", "message": "Install: pip install beautifulsoup4 requests"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_stats(self):
        try:
            from qdrant_client import QdrantClient
            client = QdrantClient(host="localhost", port=6333)
            collections = client.get_collections().collections
            stats = {}
            for col in collections:
                info = client.get_collection(col.name)
                stats[col.name] = info.points_count
            return {"status": "ok", "collections": stats}
        except Exception as e:
            return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    print("=" * 50)
    print("  WISDOM API SERVER")
    print("=" * 50)
    print("  Listening on http://localhost:" + str(PORT))
    print("  Endpoints:")
    print("    GET  /health - check status")
    print("    GET  /stats  - knowledge stats")
    print("    POST /ingest - receive URL from bookmarklet")
    print("=" * 50)

    server = HTTPServer(('localhost', PORT), WisdomHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Wisdom API Server stopped.")