import os
import time
import threading
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

class GeminiKeyManager:
    def __init__(self):
        self.keys = [
            k for k in [
                os.getenv("GEMINI_KEY_1"),
                os.getenv("GEMINI_KEY_2"),
                os.getenv("GEMINI_KEY_3"),
                os.getenv("GEMINI_KEY_4"),
                os.getenv("GEMINI_KEY_5"),
            ] if k
        ]
        if not self.keys:
            raise ValueError("Không tìm thấy Gemini API key nào trong .env")
        self._index = 0
        self._lock = threading.Lock()
        self._usage = defaultdict(list)
        self._cooldown = {}
        self.RPM_LIMIT = 14

    def _clean_old_requests(self, key):
        now = time.time()
        self._usage[key] = [t for t in self._usage[key] if now - t < 60]

    def _is_available(self, key):
        now = time.time()
        if key in self._cooldown and now < self._cooldown[key]:
            return False
        self._clean_old_requests(key)
        return len(self._usage[key]) < self.RPM_LIMIT

    def get_key(self):
        with self._lock:
            for _ in range(len(self.keys)):
                key = self.keys[self._index % len(self.keys)]
                self._index += 1
                if self._is_available(key):
                    self._usage[key].append(time.time())
                    return key
            raise Exception("Tất cả keys đang bị rate-limit, thử lại sau!")

    def mark_rate_limited(self, key, cooldown_seconds=65):
        with self._lock:
            self._cooldown[key] = time.time() + cooldown_seconds
            print(f"[KeyManager] Key ...{key[-6:]} cooldown {cooldown_seconds}s")

    def status(self):
        now = time.time()
        result = {}
        for key in self.keys:
            self._clean_old_requests(key)
            in_cooldown = key in self._cooldown and now < self._cooldown[key]
            result[f"...{key[-6:]}"] = {
                "rpm_used": len(self._usage[key]),
                "rpm_remaining": self.RPM_LIMIT - len(self._usage[key]),
                "in_cooldown": in_cooldown,
            }
        return result

key_manager = GeminiKeyManager()