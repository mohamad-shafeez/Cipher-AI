# core/speak.py — CIPHER OS (Isolated TTS Engine)
# ============================================================

import pyttsx3
import config
import re
import threading
import queue
import multiprocessing

def tts_subprocess_worker(text):
    """Module-level pickleable function to run pyttsx3 in an isolated process."""
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 170)
        engine.say(text)
        engine.runAndWait()
    except Exception:
        pass

class Speaker:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Speaker, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        print(f">> Loading Neural Voice for {config.ASSISTANT_NAME}...")
        self.busy = False  # Synchronously initialize to prevent race conditions
        self._queue = queue.Queue()
        self._active_process = None
        self._lock = threading.Lock() # 🔒 Physical lock for thread safety
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()
        self._initialized = True
        print(f">> Voice: OFFLINE LOCAL (pyttsx3 Process-Isolated) — dedicated loop active")

    def _worker(self):
        while True:
            text = self._queue.get()
            if text is None:
                break
            try:
                with self._lock:
                    self.busy = True
                    self._active_process = multiprocessing.Process(
                        target=tts_subprocess_worker, 
                        args=(text,), 
                        daemon=True
                    )
                    self._active_process.start()
                
                # Wait for the child process to finish speaking
                self._active_process.join()
            except Exception as e:
                print(f">> Speech Runtime Error: {e}")
            finally:
                self.busy = False
                self._queue.task_done()

    def clean_text(self, text):
        # 1. Strip DeepSeek reasoning blocks
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        # 2. Strip ANSI color sequences (ESC [ ... m)
        text = re.sub(r'\x1b\[[0-9;]*m', '', text)
        text = re.sub(r'\033\[[0-9;]*m', '', text)
        # 3. Strip raw residue character patterns like '92m' or '0m'
        text = re.sub(r'\b\d+m\b', '', text)
        # 4. Strip emojis and non-pronounceable symbols
        text = re.sub(r'[^\x00-\x7F]+', ' ', text) # Strip non-ASCII (emojis etc)
        # 5. Strip rogue symbols and normalize spacing
        text = re.sub(r'[;:\-\*\#\|]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def speak(self, text):
        """Queues the text to be spoken by the background thread."""
        if not text:
            return

        cleaned = self.clean_text(text)
        
        # ── INTERCEPTION FILTER ─────────────────────────────────────
        if "COMMAND REFERENCE" in cleaned or "════" in cleaned:
            cleaned = "I have displayed the requested information on your dashboard."
        elif len(cleaned) > 300:
            # Prevent reading massive text walls
            cleaned = "Sir, I have generated the response. Please check the interface."

        if not cleaned:
            return
            
        self._queue.put(cleaned)

    def speak_streamed(self, text_chunk: str):
        """Falls back to queuing the text chunk."""
        self.speak(text_chunk)

    def end_stream(self):
        """No-op"""
        pass

    def interrupt_stream(self):
        """Clears pending queue and instantly terminates active speaking process."""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                self._queue.task_done()
            except queue.Empty:
                break
        
        with self._lock:
            if self._active_process and self._active_process.is_alive():
                print("🗣️ [SPEECH INTERRUPT]: Terminating active speech process instantly!")
                try:
                    self._active_process.terminate()
                    self._active_process.join(0.1)
                except Exception:
                    pass
                self.busy = False

_global_speaker = None
def speak(text: str):
    global _global_speaker
    if _global_speaker is None:
        _global_speaker = Speaker()
    _global_speaker.speak(text)