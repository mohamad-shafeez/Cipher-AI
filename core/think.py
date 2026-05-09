import ollama
import config
import psutil
import datetime
import os
import re
import threading
import time # <--- Added for safety
from dotenv import load_dotenv

load_dotenv()

# ── Gemini import — new non-deprecated SDK ─────────────────────
try:
    # This is the correct pattern for the new google-genai library
    from google import genai as google_genai
    from google.genai import types as genai_types
    _GENAI_AVAILABLE = True
except ImportError:
    _GENAI_AVAILABLE = False


class Brain:
    def __init__(self):
        self.model   = config.LLM_MODEL
        self.history = []

        # ── Interrupt flag (shared with Listener) ──────────────
        self.interrupt_flag = threading.Event()

        # ── Gemini fallback (new SDK) ──────────────────────────
        self.gemini_client = None
        if _GENAI_AVAILABLE:
            gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
            if gemini_key:
                try:
                    self.gemini_client = google_genai.Client(api_key=gemini_key)
                    print(">> Neural Brain: Gemini Cloud Fallback ACTIVE (google.genai SDK)")
                except Exception as e:
                    print(f">> Neural Brain: Gemini init failed — {e}")
            else:
                print(">> Neural Brain: No GEMINI_API_KEY in .env — Gemini fallback DISABLED")
        else:
            print(">> Neural Brain: google-genai not installed — Gemini fallback DISABLED")
            print("   Install with: pip install google-genai")

    # ── System context ─────────────────────────────────────────

    def get_system_context(self) -> str:
        battery = psutil.sensors_battery()
        battery_info = (
            f"{battery.percent:.0f}% "
            f"{'charging' if battery.power_plugged else 'not charging'}"
            if battery else "unavailable"
        )
        now = datetime.datetime.now()
        return (
            f"Current time: {now.strftime('%I:%M %p')}. "
            f"Today: {now.strftime('%A, %B %d, %Y')}. "
            f"Battery: {battery_info}."
        )

    def _build_system_prompt(self) -> str:
        return (
            f"You are {config.ASSISTANT_NAME}, a voice assistant on a Windows PC. "
            "Answer in 1-2 short sentences. English only. "
            "Never make up information. Never roleplay. "
            "If you don't know something, say 'I don't know.' "
            "Never use special characters like semicolons, colons, dashes, asterisks, or hashes. "
            f"{self.get_system_context()}"
        )

    def _trim_history(self):
        """Keep only the last 8 turns (16 messages) to prevent context bloat."""
        if len(self.history) > 16:
            self.history = self.history[-16:]

    # ── Standard (blocking) think ──────────────────────────────

    def think(self, user_text: str) -> str:
        """
        Blocking think — used by skills and agent for non-streaming responses.
        Returns complete reply string.
        """
        self.interrupt_flag.clear()
        self._trim_history()

        system_prompt = self._build_system_prompt()
        self.history.append({'role': 'user', 'content': user_text})
        recent = self.history[-8:]

        options = {
            'num_predict': 120,   # was 30 — was cutting sentences in half
            'temperature': 0.2,
            'top_k':       20,
            'top_p':       0.5,
        }

        # ── Try Ollama (local) ─────────────────────────────────
        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    *recent
                ],
                options=options
            )
            reply = response['message']['content']

        except Exception as e:
            print(f">> [Brain] Ollama error: {e}")
            reply = self._gemini_fallback(user_text, system_prompt, recent)

        reply = self._clean(reply)
        self.history.append({'role': 'assistant', 'content': reply})
        return reply

    # ── Streaming think — yields tokens as they arrive ─────────

    def think_stream(self, user_text: str):
        """
        Generator that yields text chunks as the LLM produces them.
        Use this for voice output so Cipher starts speaking immediately.

        Usage:
            for chunk in brain.think_stream("what is AI"):
                speaker.speak_chunk(chunk)
                if brain.interrupt_flag.is_set():
                    break
        """
        self.interrupt_flag.clear()
        self._trim_history()

        system_prompt = self._build_system_prompt()
        self.history.append({'role': 'user', 'content': user_text})
        recent = self.history[-8:]

        options = {
            'num_predict': 120,
            'temperature': 0.2,
            'top_k':       20,
            'top_p':       0.5,
        }

        full_reply = ""

        try:
            # Ollama streaming — yields message chunks
            stream = ollama.chat(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    *recent
                ],
                options=options,
                stream=True,        # ← KEY: streaming enabled
            )

            buffer = ""
            for chunk in stream:
                # 1. Check if we should stop
                if self.interrupt_flag.is_set():
                    print(">> [Brain] Stream interrupted.")
                    break

                # 2. THE CRITICAL FIX: Use the new Ollama object pattern
                try:
                    # Modern Ollama returns an object with attributes
                    token = chunk.message.content
                except AttributeError:
                    # Fallback if your library version is different
                    token = chunk.get('message', {}).get('content', '')
                
                if not token:
                    continue

                buffer     += token
                full_reply += token

                # 3. Yield words for natural speech
                if any(c in buffer for c in (' ', '.', ',', '!', '?', '\n')):
                    clean = self._clean(buffer)
                    if clean:
                        yield clean
                    buffer = ""

            # Yield any remaining buffer
            if buffer.strip():
                clean = self._clean(buffer)
                if clean:
                    yield clean

        except Exception as e:
            print(f">> [Brain] Ollama streaming error: {e}")
            # Fall back to Gemini (non-streaming) if Ollama fails
            reply = self._gemini_fallback(user_text, system_prompt, recent)
            reply = self._clean(reply)
            full_reply = reply
            yield reply

        # Store complete reply in history
        if full_reply:
            self.history.append({
                'role':    'assistant',
                'content': self._clean(full_reply)
            })

    # ── Gemini fallback (google.genai — new SDK) ───────────────

    def _gemini_fallback(self, user_text: str, system_prompt: str, recent: list) -> str:
        if not self.gemini_client:
            return "Brain Error: Ollama is offline and no Gemini key is configured."

        try:
            print(">> [Brain] Routing to Gemini Neural Link...")

            # Build a single prompt for Gemini
            history_str = "\n".join(
                f"{m['role'].upper()}: {m['content']}"
                for m in recent[-4:]   # last 4 turns only for Gemini
            )
            full_prompt = (
                f"{system_prompt}\n\n"
                f"Recent conversation:\n{history_str}\n\n"
                f"User: {user_text}"
            )

            response = self.gemini_client.models.generate_content(
                model="gemini-1.5-flash",
                contents=full_prompt,
            )
            return response.text or "I couldn't generate a response."

        except Exception as g_err:
            print(f">> [Brain] Gemini error: {g_err}")
            return f"Both Ollama and Gemini are unreachable. Error: {g_err}"

    # ── Interrupt API ──────────────────────────────────────────

    def interrupt(self):
        """Stop an active think_stream() from another thread."""
        self.interrupt_flag.set()

    def clear_history(self):
        """Reset conversation history."""
        self.history = []

    # ── Text cleaner ───────────────────────────────────────────

    @staticmethod
    def _clean(text: str) -> str:
        """Strip special chars that sound bad in TTS."""
        text = re.sub(r'[;:\-\*\#\|\`\_\~\^]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text