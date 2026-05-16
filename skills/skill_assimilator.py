# skills/skill_assimilator.py
# ============================================================
#   CIPHER OS — Skill Assimilation Pipeline
#   Translates foreign Python scripts into native Cipher skills.
#
#   Pipeline:  learn_skill/*.py  →  Gemini API  →  skills/*.py
#   Fallback:  Gemini timeout/error  →  qwen2.5-coder:7b (local)
#
#   Trigger:   "assimilate skills" / "learn new skill" / "absorb skills"
#   Auto-wires into fast_loader.py registry on success.
# ============================================================

import os
import re
import time
import shutil
import requests
from datetime import datetime
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────
BASE_DIR         = Path(__file__).resolve().parent.parent
LEARN_DIR        = BASE_DIR / "learn_skill"
SKILLS_DIR       = BASE_DIR / "skills"
ARCHIVE_DIR      = LEARN_DIR / "_assimilated"
LEDGER_PATH      = BASE_DIR / "cipher_data" / "assimilation_state.md"
FAST_LOADER_PATH = BASE_DIR / "core" / "fast_loader.py"
README_PATH      = BASE_DIR / "README.md"

# ── Gemini config ─────────────────────────────────────────────
GEMINI_TIMEOUT   = 30  # seconds — strict ceiling
GEMINI_MODEL     = "gemini-2.0-flash"

# ── Local fallback config ─────────────────────────────────────
LOCAL_MODEL      = "qwen2.5-coder:7b"
LOCAL_URL        = "http://localhost:11434/api/generate"
LOCAL_TIMEOUT    = 120  # seconds — local models are slower

# ── The translation prompt (shared between Gemini & local) ────
TRANSLATION_PROMPT = """You are Cipher OS's Skill Compiler. Your job is to translate a foreign Python script into a native Cipher OS skill class.

=== CIPHER SKILL CONTRACT ===
1. The file MUST define exactly ONE class named `{class_name}`.
2. The class MUST have an `__init__(self)` method that prints `">> {class_name}: ONLINE"`.
3. The class MUST have an `execute(self, command: str) -> str | None` method.
4. Inside `execute()`:
   - Define a list of TRIGGER phrases (lowercase strings the user might say).
   - If the user's command matches any trigger, run the skill logic and return a response string starting with "Sir, ...".
   - If no trigger matches, return `None` (so Cipher passes to the next skill).
5. All imports must be at the top of the file.
6. Include a module-level docstring describing the skill.
7. The skill must be FULLY SELF-CONTAINED — no external class dependencies.
8. Do NOT wrap the output in markdown code fences. Return ONLY valid Python code.

=== FOREIGN SCRIPT TO TRANSLATE ===
Filename: {filename}

```python
{source_code}
```

=== OUTPUT ===
Return the complete, production-ready Python file for `skills/{output_filename}`. Nothing else."""


class SkillAssimilatorSkill:
    """
    Cipher OS Skill Assimilation Pipeline.
    Watches 'learn_skill/' for foreign .py scripts, translates them
    into native Cipher skills using Gemini (cloud) with a local LLM fallback.
    """

    def __init__(self):
        # Ensure directories exist
        LEARN_DIR.mkdir(parents=True, exist_ok=True)
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
        self._gemini_key = self._load_gemini_key()
        print(">> SkillAssimilatorSkill: ONLINE")

    # ── API key loader ────────────────────────────────────────
    def _load_gemini_key(self) -> str:
        """Load GEMINI_API_KEY from .env file."""
        env_path = BASE_DIR / ".env"
        if not env_path.exists():
            return ""
        try:
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("GEMINI_API_KEY="):
                    return line.split("=", 1)[1].strip()
        except Exception:
            pass
        return ""

    # ── Trigger detection ─────────────────────────────────────
    def execute(self, command: str) -> str | None:
        cmd = command.lower().strip()
        triggers = [
            "assimilate skill", "assimilate skills",
            "learn new skill", "learn skill",
            "absorb skill", "absorb skills",
            "import skill", "convert skill",
        ]
        if not any(t in cmd for t in triggers):
            return None

        return self.run_pipeline()

    # ══════════════════════════════════════════════════════════
    #  CORE PIPELINE
    # ══════════════════════════════════════════════════════════

    def run_pipeline(self) -> str:
        """Scan learn_skill/, translate each .py file, wire it in."""
        foreign_files = list(LEARN_DIR.glob("*.py"))
        if not foreign_files:
            return "Sir, the learn_skill/ folder is empty. Drop a .py file there and try again."

        results = []
        for fpath in foreign_files:
            result = self._assimilate_one(fpath)
            results.append(result)

        successes = [r for r in results if r["status"] == "complete"]
        failures  = [r for r in results if r["status"] != "complete"]

        summary_parts = []
        if successes:
            names = ", ".join(r["class_name"] for r in successes)
            summary_parts.append(f"Successfully assimilated {len(successes)} skill(s): {names}")
        if failures:
            names = ", ".join(r["filename"] for r in failures)
            summary_parts.append(f"Failed to assimilate: {names}")

        return f"Sir, {'. '.join(summary_parts)}. They will be active on next boot."

    def _assimilate_one(self, fpath: Path) -> dict:
        """Full pipeline for a single foreign script."""
        filename    = fpath.name
        source_code = fpath.read_text(encoding="utf-8", errors="replace")
        timestamp   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Derive class name from filename: my_cool_tool.py → MyCoolToolSkill
        stem = fpath.stem  # e.g. "my_cool_tool"
        class_name = "".join(word.capitalize() for word in stem.split("_")) + "Skill"
        output_filename = stem + ".py"

        # ── Step 1: Log plan to ledger ────────────────────────
        self._ledger_write(timestamp, filename, "pending", class_name, "", "")

        # ── Step 2: Try Gemini (cloud) ────────────────────────
        engine_used = ""
        translated_code = None
        error_msg = ""

        prompt = TRANSLATION_PROMPT.format(
            class_name=class_name,
            filename=filename,
            source_code=source_code,
            output_filename=output_filename,
        )

        if self._gemini_key:
            self._ledger_update(timestamp, filename, "translating (gemini)")
            translated_code, error_msg = self._call_gemini(prompt)
            if translated_code:
                engine_used = GEMINI_MODEL
            else:
                # ── Step 3: Fallback to local LLM ─────────────
                self._ledger_update(timestamp, filename,
                    f"gemini_fail → local_fallback | Error: {error_msg}")
                print(f">> [Assimilator] Gemini failed for {filename}, handing to local model...")
                translated_code, local_err = self._call_local(prompt)
                if translated_code:
                    engine_used = LOCAL_MODEL
                else:
                    error_msg += f" | Local also failed: {local_err}"
        else:
            # No Gemini key — go straight to local
            print(f">> [Assimilator] No Gemini key found, using local model for {filename}...")
            self._ledger_update(timestamp, filename, "translating (local — no gemini key)")
            translated_code, local_err = self._call_local(prompt)
            if translated_code:
                engine_used = LOCAL_MODEL
            else:
                error_msg = f"Local failed: {local_err}"

        # ── Step 4: Validate & save ───────────────────────────
        if not translated_code:
            self._ledger_update(timestamp, filename, f"FAILED | {error_msg}")
            return {"status": "failed", "filename": filename, "class_name": class_name}

        # Strip markdown fences if present
        translated_code = self._strip_code_fences(translated_code)

        # Validate that the class exists in the output
        if f"class {class_name}" not in translated_code:
            self._ledger_update(timestamp, filename,
                f"FAILED | Generated code missing class {class_name}")
            return {"status": "failed", "filename": filename, "class_name": class_name}

        # Save the new skill
        output_path = SKILLS_DIR / output_filename
        output_path.write_text(translated_code, encoding="utf-8")
        print(f">> [Assimilator] Saved native skill: {output_path}")

        # ── Step 5: Wire into fast_loader.py ──────────────────
        self._wire_fast_loader(stem, class_name)

        # ── Step 6: Append to README.md ───────────────────────
        triggers = self._extract_triggers(translated_code)
        self._append_readme(class_name, stem, triggers)

        # ── Step 7: Archive the foreign script ────────────────
        archive_dest = ARCHIVE_DIR / f"{stem}_{int(time.time())}.py"
        shutil.move(str(fpath), str(archive_dest))
        print(f">> [Assimilator] Archived original: {archive_dest.name}")

        # ── Step 8: Final ledger entry ────────────────────────
        self._ledger_update(timestamp, filename,
            f"complete | Engine: {engine_used} | Output: skills/{output_filename} "
            f"| Triggers: {', '.join(triggers[:5])}")

        return {"status": "complete", "filename": filename, "class_name": class_name}

    # ══════════════════════════════════════════════════════════
    #  API CALLS
    # ══════════════════════════════════════════════════════════

    def _call_gemini(self, prompt: str) -> tuple[str | None, str]:
        """
        Call Gemini API with strict timeout.
        Returns (code_string, error_string).
        """
        try:
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"{GEMINI_MODEL}:generateContent?key={self._gemini_key}"
            )
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.2,
                    "maxOutputTokens": 8192,
                }
            }
            print(f">> [Assimilator] Calling Gemini ({GEMINI_MODEL})...")
            resp = requests.post(url, json=payload, timeout=GEMINI_TIMEOUT)

            if resp.status_code != 200:
                return None, f"HTTP {resp.status_code}: {resp.text[:200]}"

            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                return None, "No candidates in Gemini response"

            text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            if not text.strip():
                return None, "Empty response from Gemini"

            return text.strip(), ""

        except requests.exceptions.Timeout:
            return None, f"Gemini timed out after {GEMINI_TIMEOUT}s"
        except Exception as e:
            return None, str(e)

    def _call_local(self, prompt: str) -> tuple[str | None, str]:
        """
        Fallback: call local Ollama model.
        Returns (code_string, error_string).
        """
        try:
            print(f">> [Assimilator] Calling local model ({LOCAL_MODEL})...")
            resp = requests.post(
                LOCAL_URL,
                json={
                    "model": LOCAL_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "keep_alive": "2m",
                },
                timeout=LOCAL_TIMEOUT,
            )

            if resp.status_code != 200:
                return None, f"Ollama HTTP {resp.status_code}"

            text = resp.json().get("response", "").strip()
            if not text:
                return None, "Empty response from local model"

            return text, ""

        except requests.exceptions.Timeout:
            return None, f"Local model timed out after {LOCAL_TIMEOUT}s"
        except Exception as e:
            return None, str(e)

    # ══════════════════════════════════════════════════════════
    #  AUTO-WIRING
    # ══════════════════════════════════════════════════════════

    def _wire_fast_loader(self, module_stem: str, class_name: str):
        """Append the new skill to SKILL_REGISTRY in fast_loader.py."""
        entry_line = f'    ("skills.{module_stem}",{" " * max(1, 24 - len(module_stem))}"{class_name}"),\n'
        marker = "# ── Phase 4 Skills"

        try:
            content = FAST_LOADER_PATH.read_text(encoding="utf-8")

            # Check if already registered
            if f'"skills.{module_stem}"' in content:
                print(f">> [Assimilator] {class_name} already in fast_loader registry.")
                return

            # Insert before the Phase 4 marker, or at the end of the registry
            if marker in content:
                # Add a new section header on first assimilated skill
                section_header = "    # ── Assimilated Skills ─────────────────────────────\n"
                if "# ── Assimilated Skills" not in content:
                    content = content.replace(
                        f"\n    {marker}",
                        f"\n{section_header}{entry_line}\n    {marker}",
                    )
                else:
                    # Append after the Assimilated Skills header
                    content = content.replace(
                        f"\n    {marker}",
                        f"{entry_line}\n    {marker}",
                    )
            else:
                # Fallback: append before the closing bracket of SKILL_REGISTRY
                content = content.replace("\n]\n", f"\n{entry_line}]\n", 1)

            FAST_LOADER_PATH.write_text(content, encoding="utf-8")
            print(f">> [Assimilator] Wired {class_name} into fast_loader.py")

        except Exception as e:
            print(f">> [Assimilator] Warning: Could not wire fast_loader.py: {e}")

    def _append_readme(self, class_name: str, module_stem: str, triggers: list[str]):
        """Append a brief skill summary to the PROJECT ROOT README.md."""
        try:
            trigger_str = ", ".join(f'*"{t}"*' for t in triggers[:3]) if triggers else "*N/A*"
            entry = (
                f"- **{class_name}** — Auto-assimilated skill "
                f"(`{module_stem}.py`). Voice triggers: {trigger_str}\n"
            )

            if not README_PATH.exists():
                print(f">> [Assimilator] README.md not found at {README_PATH}. Skipping.")
                return

            content = README_PATH.read_text(encoding="utf-8")

            # Check if entry already exists
            if class_name in content:
                print(f">> [Assimilator] {class_name} already documented in README.md.")
                return

            section_header = "### 🧬 Auto-Assimilated Skills\n\n"

            if section_header.strip() in content:
                # Section already exists — find the end of it and append
                idx = content.index(section_header.strip())
                # Move past the header line
                after_header = idx + len(section_header.strip())
                # Find next section boundary (## or --- or EOF)
                rest = content[after_header:]
                boundary = len(rest)
                for marker in ["\n## ", "\n---"]:
                    pos = rest.find(marker)
                    if pos != -1 and pos < boundary:
                        boundary = pos
                insert_pos = after_header + boundary
                content = content[:insert_pos] + "\n" + entry + content[insert_pos:]
            else:
                # Create the section — append before the last "---" or at EOF
                last_divider = content.rfind("\n---")
                if last_divider > 0:
                    content = (
                        content[:last_divider]
                        + f"\n\n{section_header}{entry}\n"
                        + content[last_divider:]
                    )
                else:
                    content += f"\n\n{section_header}{entry}"

            README_PATH.write_text(content, encoding="utf-8")
            print(f">> [Assimilator] Documented {class_name} in README.md")

        except Exception as e:
            print(f">> [Assimilator] Warning: Could not update README.md: {e}")

    # ══════════════════════════════════════════════════════════
    #  UTILITIES
    # ══════════════════════════════════════════════════════════

    def _extract_triggers(self, code: str) -> list[str]:
        """Extract trigger phrases from the generated skill code."""
        triggers = []
        # Look for string literals in lists that look like trigger arrays
        pattern = r'["\']([a-z][a-z\s]{3,40})["\']'
        matches = re.findall(pattern, code)
        # Filter to likely trigger phrases (not imports, not class names)
        for m in matches:
            if " " in m and not m.startswith(">>") and len(m) < 40:
                triggers.append(m)
        return triggers[:5]

    def _strip_code_fences(self, text: str) -> str:
        """Remove markdown code fences from LLM output."""
        text = text.strip()
        if text.startswith("```python"):
            text = text[len("```python"):].strip()
        elif text.startswith("```"):
            text = text[3:].strip()
        if text.endswith("```"):
            text = text[:-3].strip()
        return text

    def _ledger_write(self, timestamp: str, filename: str, status: str,
                      class_name: str, engine: str, error: str):
        """Write a new entry to the assimilation ledger."""
        try:
            entry = f"""
### [{timestamp}] — {filename}
- **Status**: {status}
- **Target Class**: {class_name}
- **Engine**: {engine or 'pending'}
- **Error**: {error or 'none'}
"""
            with open(LEDGER_PATH, "a", encoding="utf-8") as f:
                f.write(entry)
        except Exception as e:
            print(f">> [Assimilator] Ledger write error: {e}")

    def _ledger_update(self, timestamp: str, filename: str, new_status: str):
        """Update the latest status for a filename in the ledger."""
        try:
            entry = f"- **[{timestamp}] {filename}**: {new_status}\n"
            with open(LEDGER_PATH, "a", encoding="utf-8") as f:
                f.write(entry)
        except Exception as e:
            print(f">> [Assimilator] Ledger update error: {e}")
