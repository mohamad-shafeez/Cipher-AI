# skills/clipboard_sync.py
# ============================================================
#   CIPHER CLIPBOARD SYNC
#   Sync clipboard content between laptop and Android phone
#   via ADB, plus local clipboard utilities.
#
#   Triggers:
#     "clipboard send"        → push laptop clipboard → phone
#     "clipboard receive"     → pull phone clipboard → laptop
#     "clipboard show"        → display current laptop clipboard
#     "clipboard clear"       → clear laptop clipboard
#     "clipboard save"        → save clipboard to file
#     "clipboard history"     → show saved clipboard items
# ============================================================

import subprocess
import os
import json
from pathlib import Path
from datetime import datetime

try:
    import pyperclip
    _HAS_PYPERCLIP = True
except ImportError:
    _HAS_PYPERCLIP = False

HISTORY_FILE = Path("data/clipboard_history.json")
MAX_HISTORY  = 20


class ClipboardSyncSkill:

    TRIGGERS = [
        "clipboard send", "clipboard receive", "clipboard show",
        "clipboard clear", "clipboard save", "clipboard history",
        "copy to phone", "paste from phone",
    ]

    def execute(self, command: str) -> str | None:
        cmd = command.lower().strip()
        if "clipboard" not in cmd and "copy to phone" not in cmd and "paste from phone" not in cmd:
            return None

        if "send" in cmd or "copy to phone" in cmd:
            return self._send_to_phone()
        if "receive" in cmd or "paste from phone" in cmd:
            return self._receive_from_phone()
        if "show" in cmd:
            return self._show()
        if "clear" in cmd:
            return self._clear()
        if "save" in cmd:
            return self._save()
        if "history" in cmd:
            return self._history()

        return None

    # ------------------------------------------------------------------ #
    #  LAPTOP → PHONE                                                      #
    # ------------------------------------------------------------------ #

    def _send_to_phone(self) -> str:
        text = self._get_clipboard()
        if not text:
            return "Sir, clipboard is empty. Nothing to send."

        # Escape for ADB shell
        escaped = text.replace("'", "\\'").replace("\n", " ")[:500]

        ok, msg = self._adb(
            "shell", "am", "broadcast",
            "-a", "clipper.set",
            "--es", "text", escaped
        )
        if ok:
            return f"Sir, clipboard sent to phone. ({len(text)} chars)"

        # Fallback: use input text (simulates paste)
        ok2, msg2 = self._adb("shell", "input", "text", escaped)
        if ok2:
            return "Sir, text sent to phone via input injection."
        return f"Sir, could not send clipboard to phone: {msg}"

    # ------------------------------------------------------------------ #
    #  PHONE → LAPTOP                                                      #
    # ------------------------------------------------------------------ #

    def _receive_from_phone(self) -> str:
        # Method: ADB shell clipboard via content provider
        ok, out = self._adb(
            "shell", "content", "query",
            "--uri", "content://com.android.providers.settings/system",
            "--where", "name='clipboard'"
        )
        if ok and out:
            self._set_clipboard(out)
            return f"Sir, phone clipboard received: {out[:80]}..."

        # Fallback: read from phone input buffer (limited)
        return "Sir, could not read phone clipboard. Ensure USB debugging is enabled."

    # ------------------------------------------------------------------ #
    #  LOCAL CLIPBOARD UTILS                                               #
    # ------------------------------------------------------------------ #

    def _show(self) -> str:
        text = self._get_clipboard()
        if not text:
            return "Sir, laptop clipboard is empty."
        preview = text[:300]
        return (
            f"Sir, clipboard content ({len(text)} chars):\n"
            f"─────────────────────────\n"
            f"{preview}"
            f"{'...' if len(text) > 300 else ''}"
        )

    def _clear(self) -> str:
        self._set_clipboard("")
        return "Sir, clipboard cleared."

    def _save(self) -> str:
        text = self._get_clipboard()
        if not text:
            return "Sir, clipboard is empty. Nothing to save."

        HISTORY_FILE.parent.mkdir(exist_ok=True)
        history = self._load_history()
        history.insert(0, {
            "timestamp": datetime.now().isoformat(),
            "text":      text[:2000],
            "length":    len(text),
        })
        history = history[:MAX_HISTORY]
        HISTORY_FILE.write_text(json.dumps(history, indent=2), encoding="utf-8")
        return f"Sir, clipboard saved to history. ({len(text)} chars)"

    def _history(self) -> str:
        history = self._load_history()
        if not history:
            return "Sir, clipboard history is empty."
        lines = [f"Sir, last {len(history)} clipboard saves:\n"]
        for i, item in enumerate(history[:10], 1):
            ts      = item.get("timestamp", "")[:16]
            preview = item.get("text", "")[:60].replace("\n", " ")
            lines.append(f"  {i}. [{ts}] {preview}...")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    #  HELPERS                                                             #
    # ------------------------------------------------------------------ #

    def _get_clipboard(self) -> str:
        if _HAS_PYPERCLIP:
            try:
                return pyperclip.paste() or ""
            except Exception:
                pass
        # Windows fallback
        try:
            import subprocess
            r = subprocess.run(
                ["powershell", "-command", "Get-Clipboard"],
                capture_output=True, text=True, timeout=5
            )
            return r.stdout.strip()
        except Exception:
            return ""

    def _set_clipboard(self, text: str):
        if _HAS_PYPERCLIP:
            try:
                pyperclip.copy(text)
                return
            except Exception:
                pass
        try:
            subprocess.run(
                ["powershell", "-command",
                 f"Set-Clipboard -Value '{text}'"],
                capture_output=True, timeout=5
            )
        except Exception:
            pass

    def _adb(self, *args) -> tuple[bool, str]:
        try:
            r = subprocess.run(
                ["adb"] + list(args),
                capture_output=True, text=True, timeout=10
            )
            return r.returncode == 0, (r.stdout + r.stderr).strip()
        except FileNotFoundError:
            return False, "ADB not found."
        except Exception as e:
            return False, str(e)

    def _load_history(self) -> list:
        if HISTORY_FILE.exists():
            try:
                return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return []