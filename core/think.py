import ollama
import config
import psutil
import datetime
import os
import re
import threading
import time

class Brain:
    def __init__(self):
        self.model   = config.LLM_MODEL
        self.history = []

        # ── Interrupt flag (shared with Listener) ──────────────
        self.interrupt_flag = threading.Event()
        print(f">> Neural Brain: LOCAL ONLY MODE ACTIVE ({self.model})")

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
            "If the user asks about a complex, academic, scientific, or unfamiliar topic "
            "and you are NOT confident in your answer, respond with: "
            "'Sir, I do not have reliable knowledge on this topic. "
            "Shall I initiate a deep research session to learn about it?' "
            "NEVER fabricate facts about topics you are uncertain about. "
            "Never use special characters like semicolons, colons, dashes, asterisks, or hashes. "
            "If the user is asking to fix a file, generate code, or perform a system action, do NOT just give advice. "
            "Instead, return a structured response starting with 'COMMAND: [SkillName] [Instruction]'. "
            "Example: 'COMMAND: AutonomousCoder fix the ZeroDivisionError in generated_code/test.py'. "
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
            'num_predict': 120,   
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
            reply = f"Local Neural Brain offline. Error: {e}"

        reply = self._clean(reply)
        self.history.append({'role': 'assistant', 'content': reply})
        return reply

    # ── Streaming think — yields tokens as they arrive ─────────

    def think_stream(self, user_text: str):
        """
        Generator that yields text chunks as the LLM produces them.
        Use this for voice output so Cipher starts speaking immediately.
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

                # 2. Extract token safely
                try:
                    token = chunk.message.content
                except AttributeError:
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
            reply = f"Local Neural Brain offline. Error: {e}"
            reply = self._clean(reply)
            full_reply = reply
            yield reply

        # Store complete reply in history
        if full_reply:
            self.history.append({
                'role':    'assistant',
                'content': self._clean(full_reply)
            })

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
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        text = re.sub(r'[;:\-\*\#\|\`\_\~\^]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text