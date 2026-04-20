# skills/turbo_brain.py
# ============================================================
#   CIPHER TURBO BRAIN
#   Makes Cipher's LLM replies dramatically faster via:
#     1. Response cache  — identical questions answered instantly
#     2. Streaming       — first words arrive in ~300ms
#     3. Short-circuit   — common queries answered without LLM
#     4. Context trimmer — keeps prompts lean so inference is fast
#
#   Triggers:
#     "turbo on"  /  "turbo off"  /  "clear cache"
#     "cache stats"
# ============================================================

import time
import hashlib
import threading
import requests
import config
from collections import OrderedDict

OLLAMA_URL   = f"{config.OLLAMA_BASE_URL}/api/generate"
OLLAMA_MODEL = config.LLM_MODEL


# ---- Fast short-circuit answers (no LLM needed) ----------- #
INSTANT_ANSWERS: dict[str, str] = {
    "hi":           "Sir, I'm online and ready.",
    "hello":        "Sir, Cipher here. What do you need?",
    "hey":          "Sir, listening.",
    "ping":         "Sir, pong. All systems nominal.",
    "test":         "Sir, test successful. Backend is live.",
    "status":       "Sir, all systems operational.",
    "who are you":  "Sir, I am Cipher — your local AI operating system.",
    "what can you do": (
        "Sir, I can control your system, phone, files, run code, "
        "debug, search the web, manage email, monitor security, "
        "remember knowledge, and execute multi-step tasks autonomously."
    ),
}


class LRUCache:
    """Thread-safe LRU cache with TTL expiry."""

    def __init__(self, max_size: int = 200, ttl_seconds: int = 3600):
        self._cache: OrderedDict[str, tuple[str, float]] = OrderedDict()
        self._max   = max_size
        self._ttl   = ttl_seconds
        self._lock  = threading.Lock()
        self.hits   = 0
        self.misses = 0

    def _key(self, text: str) -> str:
        return hashlib.md5(text.strip().lower().encode()).hexdigest()

    def get(self, text: str) -> str | None:
        k = self._key(text)
        with self._lock:
            if k in self._cache:
                val, ts = self._cache[k]
                if time.time() - ts < self._ttl:
                    self._cache.move_to_end(k)
                    self.hits += 1
                    return val
                del self._cache[k]
            self.misses += 1
            return None

    def set(self, text: str, response: str):
        k = self._key(text)
        with self._lock:
            if k in self._cache:
                self._cache.move_to_end(k)
            self._cache[k] = (response, time.time())
            if len(self._cache) > self._max:
                self._cache.popitem(last=False)

    def clear(self):
        with self._lock:
            self._cache.clear()
            self.hits = self.misses = 0

    def stats(self) -> dict:
        total = self.hits + self.misses
        rate  = round(self.hits / total * 100, 1) if total else 0
        return {
            "size":      len(self._cache),
            "max_size":  self._max,
            "hits":      self.hits,
            "misses":    self.misses,
            "hit_rate":  f"{rate}%",
            "ttl_hours": self._ttl // 3600,
        }


# Shared singleton cache used by both TurboBrainSkill and turbo_think()
_cache = LRUCache(max_size=200, ttl_seconds=3600)
_turbo_enabled = True


def turbo_think(prompt: str, model: str = OLLAMA_MODEL,
                max_tokens: int = 400, use_cache: bool = True) -> str:
    """
    Fast LLM call with caching and streaming.
    Can be called directly from core/think.py or anywhere else.

    Returns the full response string.
    """
    global _turbo_enabled

    prompt = prompt.strip()

    # 1. Instant short-circuit
    lower = prompt.lower()
    for key, answer in INSTANT_ANSWERS.items():
        if key in lower and len(lower) < len(key) + 20:
            return answer

    # 2. Cache lookup
    if use_cache and _turbo_enabled:
        cached = _cache.get(prompt)
        if cached:
            print(f"  [TurboBrain] Cache HIT ({_cache.hits} total hits)")
            return cached

    # 3. Lean prompt — trim whitespace, cap length
    trimmed = _trim_prompt(prompt, max_chars=1200)

    # 4. Streaming call — collect tokens as they arrive
    t0 = time.perf_counter()
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model":   model,
                "prompt":  trimmed,
                "stream":  True,          # ← streaming = faster first token
                "options": {
                    "num_predict": max_tokens,
                    "temperature": 0.7,
                    "top_k":       20,    # smaller = faster sampling
                    "top_p":       0.8,
                },
            },
            stream=True,
            timeout=60,
        )
        tokens = []
        for line in response.iter_lines():
            if line:
                import json
                chunk = json.loads(line)
                tokens.append(chunk.get("response", ""))
                if chunk.get("done"):
                    break

        full = "".join(tokens).strip()
        elapsed = time.perf_counter() - t0
        print(f"  [TurboBrain] Response in {elapsed:.2f}s ({len(full)} chars)")

        # 5. Cache the result
        if use_cache and full:
            _cache.set(prompt, full)

        return full or "Sir, I didn't get a response from the model."

    except Exception as e:
        return f"Sir, model error: {str(e)[:80]}"


def _trim_prompt(text: str, max_chars: int) -> str:
    """Keep prompt within token budget."""
    if len(text) <= max_chars:
        return text
    # Keep beginning and end; cut middle
    keep = max_chars // 2
    return text[:keep] + "\n[...trimmed...]\n" + text[-keep:]


class TurboBrainSkill:
    """
    Skill wrapper — lets you control TurboBrain from voice commands.
    """

    def execute(self, command: str) -> str | None:
        cmd = command.lower().strip()

        if cmd in ("turbo on", "enable turbo", "speed mode on"):
            global _turbo_enabled
            _turbo_enabled = True
            return "Sir, Turbo Brain enabled. Response caching is active."

        if cmd in ("turbo off", "disable turbo", "speed mode off"):
            _turbo_enabled = False
            return "Sir, Turbo Brain disabled. Raw LLM mode active."

        if cmd in ("clear cache", "reset cache", "flush cache"):
            _cache.clear()
            return "Sir, response cache cleared."

        if cmd in ("cache stats", "cache status", "turbo stats"):
            s = _cache.stats()
            return (
                f"Sir, Turbo Brain cache stats:\n"
                f"  Entries  : {s['size']} / {s['max_size']}\n"
                f"  Hit Rate : {s['hit_rate']}\n"
                f"  Hits     : {s['hits']}\n"
                f"  Misses   : {s['misses']}\n"
                f"  TTL      : {s['ttl_hours']}h\n"
                f"  Status   : {'ENABLED' if _turbo_enabled else 'DISABLED'}"
            )

        return None