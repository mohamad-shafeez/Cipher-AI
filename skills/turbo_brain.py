import time, hashlib, threading, requests, json, config
from collections import OrderedDict

OLLAMA_URL = f"{config.OLLAMA_BASE_URL}/api/generate"
OLLAMA_MODEL = config.LLM_MODEL
INSTANT_ANSWERS = {"hi": "Sir, I am online.", "status": "All systems nominal."}

class LRUCache:
    def __init__(self, max_size=200, ttl_seconds=3600):
        self._cache = OrderedDict(); self._max = max_size; self._ttl = ttl_seconds
        self._lock = threading.Lock(); self.hits = 0; self.misses = 0
    def _key(self, text): return hashlib.md5(text.strip().lower().encode()).hexdigest()
    def get(self, text):
        k = self._key(text)
        with self._lock:
            if k in self._cache:
                val, ts = self._cache[k]
                if time.time() - ts < self._ttl:
                    self._cache.move_to_end(k); self.hits += 1; return val
                del self._cache[k]
            self.misses += 1; return None
    def set(self, text, response):
        k = self._key(text)
        with self._lock:
            if k in self._cache: self._cache.move_to_end(k)
            self._cache[k] = (response, time.time())
            if len(self._cache) > self._max: self._cache.popitem(last=False)

_cache = LRUCache()
_turbo_enabled = True

def turbo_think(prompt, model=OLLAMA_MODEL, max_tokens=400, use_cache=True):
    global _turbo_enabled
    p = prompt.strip()
    if p.lower() in INSTANT_ANSWERS: return INSTANT_ANSWERS[p.lower()]
    if use_cache and _turbo_enabled:
        cached = _cache.get(p)
        if cached: return cached
    try:
        res = requests.post(OLLAMA_URL, json={"model": model, "prompt": p, "stream": True}, stream=True, timeout=60)
        full = ""
        for line in res.iter_lines():
            if line:
                chunk = json.loads(line)
                full += chunk.get("response", "")
                if chunk.get("done"): break
        if use_cache and full: _cache.set(p, full)
        return full.strip()
    except Exception as e: return f"Error: {e}"

class TurboBrainSkill:
    def execute(self, command):
        if "turbo stats" in command.lower(): return str(_cache.hits)
        return None
