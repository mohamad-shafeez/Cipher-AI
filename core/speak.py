import pyttsx3
import config
import re
import threading
import queue


class Speaker:
    def __init__(self):
        print(f">> Loading Neural Voice for {config.ASSISTANT_NAME}...")
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 170)

        # ── Streaming TTS state ─────────────────────────────────
        self._stream_queue = queue.Queue()
        self._stream_active = threading.Event()
        self._stream_thread = None
        print(f">> Voice: OFFLINE LOCAL (pyttsx3) — streaming enabled")

    def clean_text(self, text):
        text = re.sub(r'[;:\-\*\#\|]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def speak(self, text):
        """Standard blocking speak — says the full text at once."""
        if not text:
            return

        print(f"\n>> {config.ASSISTANT_NAME} speaking: {text}")

        try:
            cleaned = self.clean_text(text)
            self.engine.say(cleaned)
            self.engine.runAndWait()
        except Exception as e:
            print(f">> Speech Error: {e}")

    # ══════════════════════════════════════════════════════════
    #  STREAMING TTS — speak sentence by sentence as they arrive
    # ══════════════════════════════════════════════════════════

    def speak_streamed(self, text_chunk: str):
        """
        Feed text chunks into the streaming pipeline.
        The speaker will voice each chunk as soon as it arrives,
        while the LLM continues generating the rest in the background.
        """
        if not text_chunk or not text_chunk.strip():
            return
        self._stream_queue.put(text_chunk)

        # Start the consumer thread if not already running
        if not self._stream_active.is_set():
            self._stream_active.set()
            self._stream_thread = threading.Thread(
                target=self._stream_consumer, daemon=True
            )
            self._stream_thread.start()

    def end_stream(self):
        """Signal that no more chunks will arrive for this response."""
        self._stream_queue.put(None)  # Sentinel

    def _stream_consumer(self):
        """Background thread: pulls chunks from the queue and voices them."""
        try:
            while True:
                chunk = self._stream_queue.get(timeout=30)
                if chunk is None:
                    break  # End-of-stream sentinel

                cleaned = self.clean_text(chunk)
                if cleaned:
                    print(f">> {config.ASSISTANT_NAME} (stream): {cleaned}")
                    try:
                        self.engine.say(cleaned)
                        self.engine.runAndWait()
                    except Exception as e:
                        print(f">> Stream Speech Error: {e}")
                        # Reinitialize engine on failure
                        try:
                            self.engine = pyttsx3.init()
                            self.engine.setProperty('rate', 170)
                        except Exception:
                            pass

        except queue.Empty:
            pass  # Timeout — no more chunks
        finally:
            self._stream_active.clear()
            # Drain any leftover items
            while not self._stream_queue.empty():
                try:
                    self._stream_queue.get_nowait()
                except queue.Empty:
                    break

    def interrupt_stream(self):
        """Stop the current streaming speech immediately."""
        # Drain queue
        while not self._stream_queue.empty():
            try:
                self._stream_queue.get_nowait()
            except queue.Empty:
                break
        # Push sentinel to stop consumer
        self._stream_queue.put(None)
        try:
            self.engine.stop()
        except Exception:
            pass


_global_speaker = None
def speak(text: str):
    global _global_speaker
    if _global_speaker is None:
        _global_speaker = Speaker()
    _global_speaker.speak(text)