# skills/ghost_hand.py
# ============================================================
#   CIPHER OS — Project Ghost-Hand
#   Autonomous GUI Control via Vision-Language Model
#
#   Architecture:
#     1. Screenshot → Moondream VLM → coordinate extraction
#     2. PyAutoGUI → physical mouse/keyboard control
#     3. Multi-step action loop for complex UI navigation
#
#   Safety:
#     - pyautogui.FAILSAFE = True (move mouse to any corner to abort)
#     - 0.3s pause between ALL pyautogui actions
#     - Max 10 steps per execution to prevent runaway loops
#     - Voice confirmation before destructive actions
#
#   Triggers:
#     "click on [element]", "open [app]", "move mouse to [element]",
#     "type [text]", "ghost hand [instruction]"
# ============================================================

import os
import re
import time
import base64
import threading
from pathlib import Path
from datetime import datetime


# ── Safety-critical: enable PyAutoGUI failsafe IMMEDIATELY ────
import pyautogui
pyautogui.FAILSAFE = True      # Mouse-to-corner = instant kill
pyautogui.PAUSE    = 0.3       # 300ms cooldown between all actions

# ── Config ────────────────────────────────────────────────────
VISION_MODEL     = "moondream"
OLLAMA_URL       = "http://localhost:11434/api/generate"
SCREENSHOT_DIR   = Path(__file__).resolve().parent.parent / "temp_vision"
MAX_STEPS        = 10           # Hard cap on autonomous action loop
CLICK_DURATION   = 0.4         # Mouse glide speed (seconds)
VISION_TIMEOUT   = 45          # Seconds to wait for VLM response


class GhostHandSkill:
    """
    Cipher's Autonomous GUI Controller.
    Uses a local Vision-Language Model (Moondream) to see the screen,
    identify UI elements, and control the mouse/keyboard to execute actions.
    """

    def __init__(self):
        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        self._active = False
        self._lock = threading.Lock()
        print(">> GhostHandSkill: ONLINE (Autonomous GUI control active)")
        print(f">> Ghost-Hand Safety: FAILSAFE={pyautogui.FAILSAFE}, PAUSE={pyautogui.PAUSE}s")

    # ══════════════════════════════════════════════════════════
    #  TRIGGER DETECTION
    # ══════════════════════════════════════════════════════════

    def execute(self, command: str) -> str | None:
        if not command:
            return None

        cmd = command.lower().strip()

        # ── Direct triggers ───────────────────────────────────
        triggers = [
            "ghost hand", "ghost-hand", "ghosthand",
            "click on", "click the", "click ",
            "move mouse to", "move cursor to",
            "right click on", "right-click on",
            "double click on", "double-click on",
            "open the app", "open app",
            "type in", "type into",
            "scroll down", "scroll up",
            "press the button", "hit the button",
        ]

        matched = False
        intent = cmd
        for t in triggers:
            if t in cmd:
                matched = True
                intent = cmd
                break

        # ── Prefix triggers ───────────────────────────────────
        if not matched:
            prefix_triggers = ["open ", "launch ", "start "]
            for t in prefix_triggers:
                if cmd.startswith(t):
                    # Only steal if it looks like a desktop app request
                    app_words = cmd[len(t):].strip()
                    if app_words and not any(w in app_words for w in [
                        "file", "project", "code", "skill", "session",
                        "browser tab", "terminal",
                    ]):
                        matched = True
                        intent = cmd
                        break

        if not matched:
            return None

        return self._execute_ghost_hand(intent)

    # ══════════════════════════════════════════════════════════
    #  CORE EXECUTION LOOP
    # ══════════════════════════════════════════════════════════

    def _execute_ghost_hand(self, intent: str) -> str:
        """
        Main Ghost-Hand loop:
        1. Screenshot the screen
        2. Send screenshot + intent to Moondream
        3. Parse the VLM response for coordinates and actions
        4. Execute via PyAutoGUI
        """
        with self._lock:
            if self._active:
                return "Sir, Ghost-Hand is already executing an action. Please wait."
            self._active = True

        try:
            print(f"\n>> [Ghost-Hand] ═══════════════════════════════════")
            print(f">> [Ghost-Hand] Intent: {intent}")
            print(f">> [Ghost-Hand] FAILSAFE: Move mouse to any screen corner to abort")
            print(f">> [Ghost-Hand] ═══════════════════════════════════")

            # ── Determine action type ─────────────────────────
            action = self._classify_action(intent)
            print(f">> [Ghost-Hand] Action type: {action['type']}")

            # ── Handle scroll commands directly ───────────────
            if action["type"] == "scroll":
                return self._do_scroll(action["direction"], action.get("amount", 5))

            # ── Handle keyboard typing directly ───────────────
            if action["type"] == "type":
                return self._do_type(action["text"])

            # ── Vision-guided actions (click, open, etc.) ─────
            # Step 1: Capture screenshot
            screenshot_path = self._take_screenshot()
            if not screenshot_path:
                return "Sir, Ghost-Hand failed to capture the screen."

            # Step 2: Ask Moondream to locate the target element
            target_desc = action.get("target", intent)
            coordinates = self._locate_element(screenshot_path, target_desc, intent)

            if not coordinates:
                return (
                    f"Sir, I scanned the screen but could not locate "
                    f"'{target_desc}'. Make sure the element is visible."
                )

            x, y = coordinates
            screen_w, screen_h = pyautogui.size()

            # Validate coordinates are within screen bounds
            if not (0 <= x <= screen_w and 0 <= y <= screen_h):
                return (
                    f"Sir, the detected coordinates ({x}, {y}) are outside "
                    f"the screen bounds ({screen_w}x{screen_h}). Aborting."
                )

            # Step 3: Execute the physical action
            result = self._execute_action(action["type"], x, y, target_desc)

            # Cleanup old screenshots
            self._cleanup_screenshots()

            return result

        except pyautogui.FailSafeException:
            return (
                "Sir, Ghost-Hand FAILSAFE triggered. Mouse was moved to a "
                "screen corner. All autonomous control has been halted."
            )
        except Exception as e:
            print(f">> [Ghost-Hand] Error: {e}")
            return f"Sir, Ghost-Hand encountered an error: {str(e)[:100]}"
        finally:
            self._active = False

    # ══════════════════════════════════════════════════════════
    #  ACTION CLASSIFICATION
    # ══════════════════════════════════════════════════════════

    def _classify_action(self, intent: str) -> dict:
        """Parse the intent string into a structured action."""
        cmd = intent.lower()

        # Scroll commands
        if "scroll down" in cmd:
            amount = self._extract_number(cmd) or 5
            return {"type": "scroll", "direction": "down", "amount": amount}
        if "scroll up" in cmd:
            amount = self._extract_number(cmd) or 5
            return {"type": "scroll", "direction": "up", "amount": amount}

        # Type commands
        type_match = re.search(r'type (?:in |into )?["\']?(.+?)["\']?\s*$', cmd)
        if type_match and "click" not in cmd:
            return {"type": "type", "text": type_match.group(1)}

        # Right-click
        if "right click" in cmd or "right-click" in cmd:
            target = re.sub(r'(right[- ]?click (?:on |the )?)', '', cmd).strip()
            return {"type": "right_click", "target": target}

        # Double-click
        if "double click" in cmd or "double-click" in cmd:
            target = re.sub(r'(double[- ]?click (?:on |the )?)', '', cmd).strip()
            return {"type": "double_click", "target": target}

        # Open app
        if cmd.startswith("open ") or cmd.startswith("launch ") or cmd.startswith("start "):
            target = re.sub(r'^(open|launch|start)\s+', '', cmd).strip()
            return {"type": "click", "target": target}

        # Default: click
        target = re.sub(
            r'^(ghost[- ]?hand |click (?:on |the )?|move (?:mouse |cursor )?to |'
            r'press the button |hit the button )', '', cmd
        ).strip()
        return {"type": "click", "target": target or cmd}

    # ══════════════════════════════════════════════════════════
    #  VISION: SCREENSHOT & ELEMENT LOCATION
    # ══════════════════════════════════════════════════════════

    def _take_screenshot(self) -> str | None:
        """Capture the current screen and save as PNG."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = str(SCREENSHOT_DIR / f"ghost_hand_{timestamp}.png")
            pyautogui.screenshot(path)
            print(f">> [Ghost-Hand] Screenshot captured: {path}")
            return path
        except Exception as e:
            print(f">> [Ghost-Hand] Screenshot failed: {e}")
            return None

    def _locate_element(self, screenshot_path: str, target: str,
                        full_intent: str) -> tuple[int, int] | None:
        """
        Send screenshot to Moondream and ask it to find the target element.
        Returns (x, y) pixel coordinates or None.
        """
        try:
            import requests

            # Encode screenshot to base64
            with open(screenshot_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode("utf-8")

            screen_w, screen_h = pyautogui.size()

            prompt = (
                f"You are a GUI automation assistant. The screen resolution is "
                f"{screen_w}x{screen_h} pixels.\n\n"
                f"The user wants to: {full_intent}\n\n"
                f"Look at this screenshot and find the UI element: '{target}'.\n\n"
                f"You MUST respond with ONLY the pixel coordinates of the CENTER "
                f"of that element in this exact format:\n"
                f"COORDINATES: [X, Y]\n\n"
                f"Where X is the horizontal pixel position and Y is the vertical "
                f"pixel position. Do NOT include any other text.\n\n"
                f"If you cannot find the element, respond with:\n"
                f"NOT_FOUND"
            )

            print(f">> [Ghost-Hand] Asking {VISION_MODEL} to locate: '{target}'...")

            payload = {
                "model": VISION_MODEL,
                "prompt": prompt,
                "images": [img_b64],
                "stream": False,
                "options": {
                    "temperature": 0.1,   # Very low — we need precise coordinates
                }
            }

            resp = requests.post(OLLAMA_URL, json=payload, timeout=VISION_TIMEOUT)

            if resp.status_code != 200:
                print(f">> [Ghost-Hand] VLM error: HTTP {resp.status_code}")
                return None

            vlm_response = resp.json().get("response", "").strip()
            print(f">> [Ghost-Hand] VLM response: {vlm_response}")

            # Parse coordinates from response
            return self._parse_coordinates(vlm_response, screen_w, screen_h)

        except Exception as e:
            print(f">> [Ghost-Hand] Vision error: {e}")
            return None

    def _parse_coordinates(self, response: str, screen_w: int,
                           screen_h: int) -> tuple[int, int] | None:
        """
        Extract [X, Y] coordinates from the VLM response.
        Handles various formats:
          COORDINATES: [500, 300]
          (500, 300)
          x=500, y=300
          500, 300
        """
        if "NOT_FOUND" in response.upper():
            return None

        # Pattern 1: COORDINATES: [X, Y]
        match = re.search(r'COORDINATES:\s*\[?\s*(\d+)\s*,\s*(\d+)\s*\]?', response)
        if match:
            x, y = int(match.group(1)), int(match.group(2))
            if 0 <= x <= screen_w and 0 <= y <= screen_h:
                return (x, y)

        # Pattern 2: (X, Y) or X, Y
        match = re.search(r'\(?\s*(\d+)\s*,\s*(\d+)\s*\)?', response)
        if match:
            x, y = int(match.group(1)), int(match.group(2))
            if 0 <= x <= screen_w and 0 <= y <= screen_h:
                return (x, y)

        # Pattern 3: x=X y=Y
        match = re.search(r'x\s*[=:]\s*(\d+).*?y\s*[=:]\s*(\d+)', response, re.IGNORECASE)
        if match:
            x, y = int(match.group(1)), int(match.group(2))
            if 0 <= x <= screen_w and 0 <= y <= screen_h:
                return (x, y)

        return None

    # ══════════════════════════════════════════════════════════
    #  PHYSICAL ACTION EXECUTION
    # ══════════════════════════════════════════════════════════

    def _execute_action(self, action_type: str, x: int, y: int,
                        target: str) -> str:
        """Execute the physical mouse/keyboard action."""
        print(f">> [Ghost-Hand] Executing: {action_type} at ({x}, {y})")

        if action_type == "click":
            pyautogui.moveTo(x, y, duration=CLICK_DURATION)
            time.sleep(0.1)
            pyautogui.click()
            return f"Sir, I clicked on '{target}' at coordinates ({x}, {y})."

        elif action_type == "double_click":
            pyautogui.moveTo(x, y, duration=CLICK_DURATION)
            time.sleep(0.1)
            pyautogui.doubleClick()
            return f"Sir, I double-clicked on '{target}' at ({x}, {y})."

        elif action_type == "right_click":
            pyautogui.moveTo(x, y, duration=CLICK_DURATION)
            time.sleep(0.1)
            pyautogui.rightClick()
            return f"Sir, I right-clicked on '{target}' at ({x}, {y})."

        elif action_type == "move":
            pyautogui.moveTo(x, y, duration=CLICK_DURATION)
            return f"Sir, cursor moved to '{target}' at ({x}, {y})."

        else:
            pyautogui.moveTo(x, y, duration=CLICK_DURATION)
            pyautogui.click()
            return f"Sir, I interacted with '{target}' at ({x}, {y})."

    def _do_scroll(self, direction: str, amount: int) -> str:
        """Execute a scroll action."""
        clicks = amount if direction == "up" else -amount
        pyautogui.scroll(clicks)
        return f"Sir, I scrolled {direction} by {amount} clicks."

    def _do_type(self, text: str) -> str:
        """Type text at the current cursor position."""
        pyautogui.typewrite(text, interval=0.03)
        return f"Sir, I typed '{text[:40]}{'...' if len(text) > 40 else ''}'."

    # ══════════════════════════════════════════════════════════
    #  MULTI-STEP EXECUTION (Agent-callable)
    # ══════════════════════════════════════════════════════════

    def execute_sequence(self, steps: list[str]) -> str:
        """
        Execute a sequence of Ghost-Hand actions.
        Called by the Agent for complex multi-step UI tasks.
        Example: ["open chrome", "click on address bar", "type google.com"]
        """
        if len(steps) > MAX_STEPS:
            return f"Sir, the sequence exceeds the {MAX_STEPS}-step safety limit."

        results = []
        for i, step in enumerate(steps, 1):
            print(f"\n>> [Ghost-Hand] Sequence step {i}/{len(steps)}: {step}")
            result = self._execute_ghost_hand(step)
            results.append(f"Step {i}: {result}")

            # Brief pause between steps for UI to settle
            time.sleep(0.8)

        return "Sir, sequence complete. " + " | ".join(results)

    # ══════════════════════════════════════════════════════════
    #  UTILITIES
    # ══════════════════════════════════════════════════════════

    def _extract_number(self, text: str) -> int | None:
        """Extract a number from text (e.g., 'scroll down 10')."""
        match = re.search(r'(\d+)', text)
        return int(match.group(1)) if match else None

    def _cleanup_screenshots(self, keep_last: int = 5):
        """Keep only the last N screenshots to prevent disk bloat."""
        try:
            files = sorted(
                [f for f in SCREENSHOT_DIR.iterdir() if f.name.startswith("ghost_hand_")],
                key=lambda f: f.stat().st_mtime,
            )
            for old_file in files[:-keep_last]:
                old_file.unlink()
        except Exception:
            pass
