import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "gemma3:4b"

def call_gemini(prompt, model=DEFAULT_MODEL, max_retries=3):
    """
    Gọi Ollama local thay thế Gemini API.
    Local-first, không cần API key, không bị rate limit.
    """
    for attempt in range(max_retries):
        try:
            response = requests.post(OLLAMA_URL, json={
                "model": model,
                "prompt": prompt,
                "stream": False
            })
            response.raise_for_status()
            return response.json()["response"]

        except Exception as e:
            print(f"[Ollama] Attempt {attempt+1} lỗi: {e}")
            if attempt == max_retries - 1:
                raise

    raise Exception("Ollama thất bại sau nhiều lần thử.")