"""
test_api_routing.py — Wisdom FreeLLMAPI Test
Kiem tra FreeLLMAPI middleware hoat dong voi $0 chi phi.

Usage:
    python test_api_routing.py
    python test_api_routing.py --wisdom  # Test tich hop voi Wisdom
"""

import requests
import json
import sys
import time

FREELLM_BASE = "http://localhost:3001/v1"
FREELLM_KEY  = "freellmapi-key"  # Lay tu dashboard Keys tab

def test_basic_chat(model: str = "auto") -> dict:
    """Test co ban: gui message, nhan response."""
    print(f"\n[TEST 1] Basic chat — model: {model}")
    try:
        resp = requests.post(
            f"{FREELLM_BASE}/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {FREELLM_KEY}"
            },
            json={
                "messages": [
                    {"role": "user", "content": "Ban la AI nao? Tra loi ngan gon 1 cau."}
                ],
                "max_tokens": 100
            },
            timeout=30
        )
        if resp.status_code == 200:
            data = resp.json()
            answer = data["choices"][0]["message"]["content"]
            provider = data.get("model", "unknown")
            print(f"  OK: {answer[:100]}")
            print(f"  Provider: {provider}")
            return {"success": True, "answer": answer, "provider": provider}
        else:
            print(f"  FAIL: {resp.status_code} — {resp.text[:200]}")
            return {"success": False, "error": resp.text}
    except Exception as e:
        print(f"  ERROR: {e}")
        return {"success": False, "error": str(e)}


def test_wisdom_analysis(text: str = None) -> dict:
    """Test phan tich knowledge theo format Wisdom."""
    print(f"\n[TEST 2] Wisdom analysis format")
    if not text:
        text = """Dan Koe is a one-person business owner who makes $2M+ per year.
He teaches that focus, writing, and building systems are the keys to OPC success.
His core insight: specialize deeply, teach what you know, sell your knowledge."""

    prompt = f"""Analyze this text and extract structured knowledge.
Return ONLY valid JSON, no markdown.

Text: {text}

Return:
{{
  "title": "main topic",
  "summary": "2 sentence summary",
  "key_concepts": ["concept1", "concept2"],
  "opc_applicability": "how OPC owner can apply this",
  "action_steps": ["step1", "step2"]
}}"""

    try:
        resp = requests.post(
            f"{FREELLM_BASE}/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {FREELLM_KEY}"
            },
            json={
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2000
            },
            timeout=30
        )
        if resp.status_code == 200:
            raw = resp.json()["choices"][0]["message"]["content"]
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"): raw = raw[4:]
            parsed = json.loads(raw.strip())
            print(f"  OK: Title = {parsed.get('title')}")
            print(f"  Concepts: {parsed.get('key_concepts')}")
            print(f"  OPC: {parsed.get('opc_applicability','')[:80]}")
            return {"success": True, "analysis": parsed}
        else:
            print(f"  FAIL: {resp.status_code}")
            return {"success": False}
    except (json.JSONDecodeError, Exception) as e:
        # Aggressive clean: bo markdown, lay phan JSON thuan
        try:
            import re as _re
            # Xoa markdown code blocks
            cleaned = _re.sub(r"```[a-z]*", "", raw).replace("```", "").strip()
            # Neu van fail, tim JSON object trong text
            match = _re.search(r'\{.*\}', cleaned, _re.DOTALL)
            if match:
                cleaned = match.group(0)
            parsed = json.loads(cleaned)
            print(f"  OK (cleaned): title={parsed.get('title','?')[:40]}")
            print(f"  Concepts: {parsed.get('key_concepts', [])}")
            return {"success": True, "analysis": parsed}
        except Exception as e2:
            print(f"  JSON parse failed: {e2}")
            print(f"  Raw response: {raw[:300]}")
            return {"success": False, "error": "JSON parse failed"}
    except Exception as e:
        print(f"  ERROR: {e}")
        return {"success": False, "error": str(e)}


def test_routing_failover() -> dict:
    """Test auto-routing: FreeLLM tu chon provider tot nhat."""
    print(f"\n[TEST 3] Auto-routing failover")
    models = ["auto-route"]
    results = []
    for model in models:
        try:
            start = time.time()
            resp = requests.post(
                f"{FREELLM_BASE}/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {FREELLM_KEY}"
                },
                json={
                    "messages": [{"role": "user", "content": "Say OK only."}],
                    "max_tokens": 10
                },
                timeout=20
            )
            elapsed = round(time.time() - start, 2)
            if resp.status_code == 200:
                provider = resp.json().get("model", "unknown")
                print(f"  [{model}] OK — {elapsed}s — provider: {provider}")
                results.append({"model": model, "ok": True, "time": elapsed})
            else:
                print(f"  [{model}] FAIL {resp.status_code}")
                results.append({"model": model, "ok": False})
        except Exception as e:
            print(f"  [{model}] ERROR: {e}")
            results.append({"model": model, "ok": False, "error": str(e)})
    return {"results": results}


def test_wisdom_integration() -> dict:
    """Test tich hop vao Wisdom ingest pipeline."""
    print(f"\n[TEST 4] Wisdom integration — replace Ollama")
    print("  Gia lap: FreeLLMAPI thay Ollama trong wisdom_ingest.py")

    # Mock transcript nhu wisdom_ingest.py gui
    mock_transcript = """In this video I explain how to build a one-person business.
The key is to pick one skill, go deep, and monetize through teaching.
Most people fail because they try to do too many things at once.
Focus on one thing for 12 months. That's the secret."""

    result = test_wisdom_analysis(mock_transcript)
    if result.get("success"):
        print(f"\n  Wisdom Integration: READY")
        print(f"  Thay OLLAMA_BASE bang FREELLM_BASE trong .env la xong")
        print(f"  Chi phi: $0")
    else:
        print(f"\n  Wisdom Integration: Can debug them")
    return result


def main():
    print("="*60)
    print("  WISDOM FREELLMAPI TEST SUITE")
    print(f"  Endpoint: {FREELLM_BASE}")
    print("="*60)

    # Kiem tra server chay chua
    try:
        resp = requests.get("http://localhost:3001", timeout=5)
        print(f"\n  FreeLLMAPI server: ONLINE")
    except:
        print(f"\n  FreeLLMAPI server: OFFLINE")
        print(f"  Hay chay: cd freellmapi && npm run dev")
        sys.exit(1)

    results = {}
    results["basic"]    = test_basic_chat()
    results["routing"]  = test_routing_failover()

    if "--wisdom" in sys.argv:
        results["wisdom"] = test_wisdom_integration()

    # Summary
    print(f"\n{'='*60}")
    print("  SUMMARY")
    print(f"{'='*60}")
    passed = sum(1 for k, v in results.items()
                 if isinstance(v, dict) and v.get("success", False))
    print(f"  Tests passed: {passed}/{len(results)}")
    print(f"  Cost: $0.00")
    print(f"  Status: {'ALL GOOD' if passed == len(results) else 'Some tests failed'}")

    if results["basic"].get("success"):
        print(f"\n  NEXT STEP: Them vao .env cua Wisdom:")
        print(f"  FREELLM_BASE=http://localhost:3001/v1")
        print(f"  FREELLM_KEY=freellmapi-key")
        print(f"  Sau do sua wisdom_ingest.py dung FreeLLMAPI thay Ollama")


if __name__ == "__main__":
    main()
