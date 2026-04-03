# core/context.py
# ============================================================
#   CIPHER SESSION CONTEXT
#   Manages per-session conversational memory and injects
#   it into every LLM call so Cipher remembers the thread.
# ============================================================

from datetime import datetime


class SessionContext:
    """
    Tracks the last N turns of a conversation and provides
    a formatted prefix string to inject into brain.think().

    Usage:
        ctx = SessionContext(max_turns=6)
        ctx.add("user",   "what is my flask port")
        ctx.add("cipher", "Sir, your Flask port is 5500.")

        # Later, in process_command:
        reply = brain.think(ctx.build_prompt_prefix() + command)
        ctx.add("user",   command)
        ctx.add("cipher", reply)
    """

    def __init__(self, max_turns: int = 6):
        self.max_turns = max_turns          # number of exchanges to keep
        self.history: list[dict] = []       # list of {role, text, time}
        self.meta: dict = {                 # session-level metadata
            "started":   datetime.now().isoformat(),
            "msg_count": 0,
            "topics":    [],
        }

    # ------------------------------------------------------------------ #
    #  ADD TURN                                                            #
    # ------------------------------------------------------------------ #

    def add(self, role: str, text: str):
        """
        Add one turn to the history.
        role: "user" or "cipher"
        text: the message content
        """
        self.history.append({
            "role":      role,
            "text":      str(text)[:600],   # cap length
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        })
        self.meta["msg_count"] += 1

        # Rolling window: keep only last max_turns * 2 entries
        max_entries = self.max_turns * 2
        if len(self.history) > max_entries:
            self.history = self.history[-max_entries:]

    # ------------------------------------------------------------------ #
    #  BUILD PREFIX                                                        #
    # ------------------------------------------------------------------ #

    def build_prompt_prefix(self) -> str:
        """
        Returns a formatted string of recent turns to prepend to any
        LLM prompt, giving Cipher conversational continuity.
        Returns empty string if no history yet.
        """
        if not self.history:
            return ""

        recent = self.history[-self.max_turns * 2:]
        lines  = ["[CONVERSATION CONTEXT — most recent first]"]

        for turn in reversed(recent):
            tag = "User" if turn["role"] == "user" else "Cipher"
            lines.append(f"  [{turn['timestamp']}] {tag}: {turn['text'][:200]}")

        lines.append("[END CONTEXT]\n\nCurrent user input: ")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    #  INTROSPECTION                                                       #
    # ------------------------------------------------------------------ #

    def last_user_input(self) -> str | None:
        """Return the most recent user message, if any."""
        for turn in reversed(self.history):
            if turn["role"] == "user":
                return turn["text"]
        return None

    def last_cipher_reply(self) -> str | None:
        """Return the most recent Cipher reply, if any."""
        for turn in reversed(self.history):
            if turn["role"] == "cipher":
                return turn["text"]
        return None

    def turn_count(self) -> int:
        return self.meta["msg_count"]

    def get_history(self) -> list:
        """Return a copy of the full history list."""
        return list(self.history)

    # ------------------------------------------------------------------ #
    #  RESET                                                               #
    # ------------------------------------------------------------------ #

    def reset(self):
        """Clear all history (call on new chat session)."""
        self.history.clear()
        self.meta = {
            "started":   datetime.now().isoformat(),
            "msg_count": 0,
            "topics":    [],
        }

    def __repr__(self):
        return (
            f"<SessionContext turns={self.turn_count()} "
            f"window={self.max_turns} started={self.meta['started'][:16]}>"
        )