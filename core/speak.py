import pyttsx3
import config
import re
import threading
import queue


class Speaker:
    def __init__(self):
        print(f">> Loading Neural Voice for {config.ASSISTANT_NAME}...")
        self._queue = queue.Queue()
        self._lock  = threading.Lock() # 🔒 Physical lock for thread safety
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()
        print(f">> Voice: OFFLINE LOCAL (pyttsx3) — dedicated thread active")

    def _worker(self):
        # Initialize pyttsx3 inside the dedicated thread
        engine = pyttsx3.init()
        engine.setProperty('rate', 170)
        while True:
            text = self._queue.get()
            if text is None:
                break
            try:
                # Use lock to prevent concurrent engine access
                with self._lock:
                    engine.say(text)
                    engine.runAndWait()
            except RuntimeError as re:
                # Silently handle "run loop already started"
                if "run loop already started" in str(re).lower():
                    pass
                else:
                    print(f">> Speech Runtime Error: {re}")
            except Exception as e:
                print(f">> Speech Error: {e}")
            finally:
                self._queue.task_done()

    def clean_text(self, text):
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        text = re.sub(r'[;:\-\*\#\|]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def speak(self, text):
        """Queues the text to be spoken by the background thread."""
        if not text:
            return

        cleaned = self.clean_text(text)
        if not cleaned:
            return
            
        print(f"\n>> {config.ASSISTANT_NAME} speaking: {cleaned}")
        self._queue.put(cleaned)

    # ══════════════════════════════════════════════════════════
    #  STREAMING TTS (Disabled to prevent thread collisions)
    # ══════════════════════════════════════════════════════════

    def speak_streamed(self, text_chunk: str):
        """Falls back to queuing the text chunk."""
        self.speak(text_chunk)

    def end_stream(self):
        """No-op"""
        pass

    def interrupt_stream(self):
        """Drains the queue to cancel pending speech."""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                self._queue.task_done()
            except queue.Empty:
                break


_global_speaker = None
def speak(text: str):
    global _global_speaker
    if _global_speaker is None:
        _global_speaker = Speaker()
    _global_speaker.speak(text)