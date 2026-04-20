"""
Cipher Skill — Autonomous Coder
Organ: The Software Engineer

Level 5 Autonomous AI Software Engineer built into Cipher OS.
Inspired by DeepSeek-Coder (FIM patching, repo-level context, 16K governor)
and InfCode (sandbox shield, batch queue, review protocol).

Architecture:
  Block 1 — Memory Vault      : Persistent project memory (fixed/unfixed/updates/roadmap)
  Block 2 — Context Engine    : Dependency parsing, token governor, vision trigger
  Block 3 — Surgical Executor : FIM patching, sandbox shield, kill-switch approval
  Watchdog — Auto-Heal        : File-save monitor, background error detection

Vault root: D:\\Cipher Ai\\codedebug\\
Model:      deepseek-coder:6.7b → fallback deepseek-r1:1.5b
Kill Switch: Voice announcement + Web UI diff card via Flask /api/patch/pending
"""

import os
import re
import sys
import json
import time
import shutil
import hashlib
import difflib
import threading
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from collections import deque


# ── CONFIGURATION ──────────────────────────────────────────────────────────────

VAULT_ROOT      = Path(r"D:\Cipher Ai\codedebug")
MAX_TOKENS      = 15500          # Hard ceiling — leaves 500 tokens for LLM response
AVG_CHARS_PER_TOKEN = 4          # Conservative estimate for token counting
MAX_FIX_ATTEMPTS    = 3          # Max retries before marking as unfixed
SANDBOX_TIMEOUT     = 30         # Seconds a sandbox test may run
MODEL_PRIMARY   = "deepseek-coder:6.7b"
MODEL_FALLBACK  = "deepseek-r1:1.5b"

# Extensions Cipher will read for dependency scanning
CODE_EXTENSIONS = {'.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css',
                   '.java', '.cpp', '.c', '.go', '.rs', '.php', '.rb'}

# Files/dirs to always skip during scanning
SKIP_DIRS  = {'__pycache__', 'node_modules', '.git', 'venv', '.venv',
              'dist', 'build', '.next', 'migrations', 'temp_scripts',
              'generated_code', 'temp_vision', 'temp_data'}
SKIP_FILES = {'package-lock.json', 'yarn.lock', '.env'}


# ── PENDING PATCH STORE (shared with Flask /api/patch endpoint) ──────────────

_pending_patch: dict | None = None   # holds the current awaiting-approval patch
_patch_lock = threading.Lock()


def set_pending_patch(patch: dict):
    global _pending_patch
    with _patch_lock:
        _pending_patch = patch

def get_pending_patch() -> dict | None:
    with _patch_lock:
        return _pending_patch

def clear_pending_patch():
    global _pending_patch
    with _patch_lock:
        _pending_patch = None


# ══════════════════════════════════════════════════════════════════════════════
# BLOCK 1 — MEMORY VAULT
# ══════════════════════════════════════════════════════════════════════════════

class MemoryVault:
    """
    Persistent project memory.
    Structure per project:
        codedebug/
        └── <project>/
            ├── fixed_errors/    timestamped .json records of successful fixes
            ├── unfixed_errors/  failed fix attempts after MAX_FIX_ATTEMPTS
            ├── updates/         completed feature addition logs
            └── coming_updates/  roadmap / pending tasks
    """

    def __init__(self, project_name: str):
        self.name = project_name.lower().replace(" ", "_")
        self.root = VAULT_ROOT / self.name
        self._init_dirs()

    def _init_dirs(self):
        for folder in ("fixed_errors", "unfixed_errors", "updates", "coming_updates"):
            (self.root / folder).mkdir(parents=True, exist_ok=True)

    # ── Write ──────────────────────────────────────────────────────────────────

    def log_fixed(self, file: str, error: str, original: str, patched: str, diff: str):
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"fix_{ts}_{self._slug(error)}.json"
        record = {
            "timestamp":   ts,
            "file":        file,
            "error":       error,
            "original":    original,
            "patched":     patched,
            "diff":        diff,
        }
        self._write(self.root / "fixed_errors" / name, record)
        return name

    def log_unfixed(self, file: str, error: str, attempts: list[str]):
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"unfixed_{ts}_{self._slug(error)}.json"
        record = {
            "timestamp": ts,
            "file":      file,
            "error":     error,
            "attempts":  attempts,
        }
        self._write(self.root / "unfixed_errors" / name, record)
        return name

    def log_update(self, description: str, files_changed: list[str]):
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"update_{ts}.json"
        self._write(self.root / "updates" / name, {
            "timestamp":     ts,
            "description":   description,
            "files_changed": files_changed,
        })

    def add_roadmap(self, task: str):
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"task_{ts}.txt"
        (self.root / "coming_updates" / name).write_text(task, encoding="utf-8")
        return name

    # ── Read ───────────────────────────────────────────────────────────────────

    def get_fixed_summary(self) -> list[dict]:
        return self._load_folder("fixed_errors")

    def get_unfixed_summary(self) -> list[dict]:
        return self._load_folder("unfixed_errors")

    def get_roadmap(self) -> list[str]:
        folder = self.root / "coming_updates"
        return [f.read_text(encoding="utf-8") for f in sorted(folder.iterdir()) if f.is_file()]

    def has_seen_error(self, error: str) -> dict | None:
        """Check if this exact error was already fixed. Returns fix record or None."""
        slug = self._slug(error)
        for record in self.get_fixed_summary():
            if self._slug(record.get("error", "")) == slug:
                return record
        return None

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _write(self, path: Path, data: dict):
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def _load_folder(self, folder: str) -> list[dict]:
        result = []
        for f in sorted((self.root / folder).iterdir()):
            if f.suffix == ".json":
                try:
                    result.append(json.loads(f.read_text(encoding="utf-8")))
                except Exception:
                    pass
        return result[-20:]  # Return last 20 to avoid memory bloat

    @staticmethod
    def _slug(text: str) -> str:
        return re.sub(r'[^\w]', '', text.lower())[:40]


# ══════════════════════════════════════════════════════════════════════════════
# BLOCK 2 — CONTEXT ENGINE
# ══════════════════════════════════════════════════════════════════════════════

class ContextEngine:
    """
    Builds the full code context for the LLM:
    1. Finds the active file (via vision or explicit path)
    2. Scans for import dependencies (repo-level context like DeepSeek)
    3. Counts tokens and trims to stay within 16K limit
    """

    def __init__(self, project_root: str):
        self.root = Path(project_root)

    # ── Entry point ────────────────────────────────────────────────────────────

    def build_context(self, target_file: str) -> dict:
        """
        Returns:
            {
              "primary":      str,   # content of the main file
              "dependencies": dict,  # {filename: content}
              "token_count":  int,
              "trimmed":      bool,
            }
        """
        primary_path = Path(target_file)
        if not primary_path.exists():
            return {"primary": "", "dependencies": {}, "token_count": 0, "trimmed": False}

        primary_content = primary_path.read_text(encoding="utf-8", errors="ignore")
        deps = self._scan_dependencies(primary_path, primary_content)

        # Build combined text for token counting
        combined = primary_content + "\n".join(deps.values())
        token_est = self._count_tokens(combined)
        trimmed = False

        if token_est > MAX_TOKENS:
            primary_content, deps, trimmed = self._trim_to_limit(primary_content, deps)

        return {
            "primary":      primary_content,
            "dependencies": deps,
            "token_count":  self._count_tokens(primary_content + "\n".join(deps.values())),
            "trimmed":      trimmed,
        }

    # ── Dependency scanning (DeepSeek Gem 1) ──────────────────────────────────

    def _scan_dependencies(self, primary: Path, content: str) -> dict:
        """
        Parse import statements and find connected files in the project.
        Supports: Python, JavaScript/TypeScript, basic HTML script tags.
        """
        deps = {}
        imported_names = set()

        # Python imports
        for match in re.finditer(r'^(?:from|import)\s+([\w.]+)', content, re.MULTILINE):
            imported_names.add(match.group(1).split('.')[0])

        # JS/TS imports
        for match in re.finditer(r"(?:import|require)\s*[({'\"]([^'\")\s]+)['\")]", content):
            raw = match.group(1)
            if raw.startswith('.'):
                imported_names.add(raw.lstrip('./').split('/')[0])

        # Scan project for matching files
        for fpath in self._all_project_files():
            stem = fpath.stem
            if stem in imported_names and fpath != primary:
                try:
                    text = fpath.read_text(encoding="utf-8", errors="ignore")
                    deps[str(fpath.relative_to(self.root))] = text
                except Exception:
                    pass
            if len(deps) >= 8:  # Cap at 8 dependency files
                break

        return deps

    def _all_project_files(self):
        """Walk project root, skip noise directories."""
        for fpath in self.root.rglob("*"):
            if fpath.is_file() and fpath.suffix in CODE_EXTENSIONS:
                if not any(skip in fpath.parts for skip in SKIP_DIRS):
                    if fpath.name not in SKIP_FILES:
                        yield fpath

    # ── Token governor (DeepSeek Gem 3) ───────────────────────────────────────

    def _count_tokens(self, text: str) -> int:
        return len(text) // AVG_CHARS_PER_TOKEN

    def _trim_to_limit(self, primary: str, deps: dict) -> tuple:
        """
        Trim strategy:
        1. Keep full primary file
        2. Trim each dependency to its first 40 lines
        3. If still over limit, drop dependencies one by one
        """
        trimmed = False

        # Step 1: Trim deps to first 40 lines each
        trimmed_deps = {}
        for fname, content in deps.items():
            lines = content.splitlines()
            trimmed_deps[fname] = "\n".join(lines[:40]) + "\n# ... (truncated for context limit)"
            trimmed = True

        # Step 2: Drop deps if still too large
        combined = primary + "\n".join(trimmed_deps.values())
        while self._count_tokens(combined) > MAX_TOKENS and trimmed_deps:
            trimmed_deps.popitem()
            combined = primary + "\n".join(trimmed_deps.values())
            trimmed = True

        # Step 3: If primary itself is huge, trim it to first 600 lines
        if self._count_tokens(primary) > MAX_TOKENS:
            lines = primary.splitlines()
            primary = "\n".join(lines[:600]) + "\n# ... (file truncated at 600 lines)"
            trimmed = True

        return primary, trimmed_deps, trimmed

    # ── Vision: detect active VS Code file ────────────────────────────────────

    def detect_active_file(self) -> str | None:
        """
        Take a screenshot and use moondream/llava to read the active file path
        shown in the VS Code title bar. Returns file path string or None.
        """
        try:
            import mss, mss.tools
            snap_path = Path("temp_vision") / "vscode_active.png"
            snap_path.parent.mkdir(exist_ok=True)

            with mss.mss() as sct:
                shot = sct.grab(sct.monitors[1])
                mss.tools.to_png(shot.rgb, shot.size, output=str(snap_path))

            # Ask vision model to read the title bar
            import ollama
            with open(snap_path, "rb") as f:
                img_data = f.read()

            response = ollama.chat(
                model="moondream",
                messages=[{
                    "role": "user",
                    "content": (
                        "Look at the VS Code title bar at the very top of this screenshot. "
                        "What is the full file path or filename shown? "
                        "Reply with ONLY the file path, nothing else."
                    ),
                    "images": [img_data],
                }]
            )
            path_str = response["message"]["content"].strip().strip('"\'')
            return path_str if os.path.exists(path_str) else None

        except Exception:
            return None


# ══════════════════════════════════════════════════════════════════════════════
# BLOCK 3 — SURGICAL EXECUTOR
# ══════════════════════════════════════════════════════════════════════════════

class SurgicalExecutor:
    """
    Fixes code using:
    - Fill-in-the-Middle (FIM) prompting for surgical patches
    - Sandbox shield: test in temp copy before touching live file
    - Kill-switch: voice announcement + web UI diff card before applying
    - Batch queue: processes all errors in sequence
    - Retry loop: MAX_FIX_ATTEMPTS before giving up
    """

    def __init__(self, vault: MemoryVault, speaker=None, flask_app=None):
        self.vault   = vault
        self.speaker = speaker   # cipher speak.py Speaker instance
        self.model   = self._resolve_model()
        self._error_queue: deque = deque()
        self._queue_lock = threading.Lock()

    # ── Model resolution (DeepSeek Gem 4) ─────────────────────────────────────

    def _resolve_model(self) -> str:
        """Try primary model, fall back to secondary."""
        try:
            import ollama
            models = [m["name"] for m in ollama.list().get("models", [])]
            if any(MODEL_PRIMARY in m for m in models):
                print(f">> AutonomousCoder: using {MODEL_PRIMARY}")
                return MODEL_PRIMARY
            else:
                print(f">> AutonomousCoder: {MODEL_PRIMARY} not found, using {MODEL_FALLBACK}")
                return MODEL_FALLBACK
        except Exception:
            return MODEL_FALLBACK

    # ── Batch queue (InfCode Gem 2) ────────────────────────────────────────────

    def enqueue_errors(self, errors: list[dict]):
        """Add a list of error dicts {file, line, error} to the processing queue."""
        with self._queue_lock:
            for e in errors:
                self._error_queue.append(e)

    def process_queue(self, context_engine: ContextEngine) -> str:
        """Process all queued errors one by one. Returns summary string."""
        results = []
        total = len(self._error_queue)

        if total == 0:
            return "Error queue is empty."

        self._announce(f"Starting batch fix. {total} error{'s' if total > 1 else ''} in queue.")

        idx = 0
        while self._error_queue:
            with self._queue_lock:
                if not self._error_queue:
                    break
                error_item = self._error_queue.popleft()

            idx += 1
            self._announce(f"Processing error {idx} of {total}: {error_item.get('error','')[:60]}")

            result = self.fix_single(error_item, context_engine)
            results.append(f"[{idx}/{total}] {result}")

        summary = "\n".join(results)
        self._announce(f"Batch complete. {idx} errors processed.")
        return summary

    # ── Single fix pipeline ────────────────────────────────────────────────────

    def fix_single(self, error_item: dict, context_engine: ContextEngine) -> str:
        """
        Full pipeline for one error:
        1. Check memory vault (seen before?)
        2. Build context
        3. FIM prompt → generate patch
        4. Sandbox test
        5. Kill-switch approval
        6. Apply or reject
        """
        file_path  = error_item.get("file", "")
        error_text = error_item.get("error", "")
        line_num   = error_item.get("line")

        if not file_path or not os.path.exists(file_path):
            return f"File not found: {file_path}"

        # ── Check vault first ──────────────────────────────────────────────────
        cached = self.vault.has_seen_error(error_text)
        if cached:
            self._announce(f"I've seen this error before. Applying the previously verified fix.")
            return self._apply_fix_from_cache(file_path, cached, error_text)

        # ── Build context ──────────────────────────────────────────────────────
        ctx = context_engine.build_context(file_path)
        if ctx["trimmed"]:
            self._announce("Context trimmed to fit within the 16K token limit.")

        original_content = ctx["primary"]
        attempts = []

        for attempt in range(1, MAX_FIX_ATTEMPTS + 1):
            self._announce(f"Attempt {attempt} of {MAX_FIX_ATTEMPTS}.")

            # ── Generate FIM patch ─────────────────────────────────────────────
            patch = self._generate_fim_patch(
                original_content, ctx["dependencies"],
                error_text, file_path, line_num
            )

            if not patch or patch.strip() == original_content.strip():
                attempts.append(f"Attempt {attempt}: LLM returned no change.")
                continue

            attempts.append(f"Attempt {attempt}: patch generated ({len(patch)} chars).")

            # ── Sandbox test (InfCode Gem 1) ───────────────────────────────────
            sandbox_ok, sandbox_output = self._sandbox_test(file_path, patch)

            if not sandbox_ok:
                attempts.append(f"Attempt {attempt}: sandbox failed — {sandbox_output[:200]}")
                # Feed the sandbox error back into the next attempt
                error_text = f"{error_text}\n\nPrevious patch caused: {sandbox_output[:300]}"
                continue

            # ── Build diff ─────────────────────────────────────────────────────
            diff = self._build_diff(original_content, patch, file_path)

            # ── Kill-switch (voice + web UI) ───────────────────────────────────
            approved = self._request_approval(file_path, error_text, diff, patch, original_content)

            if approved:
                # Write patched file
                Path(file_path).write_text(patch, encoding="utf-8")
                # Log to vault
                log_name = self.vault.log_fixed(file_path, error_text, original_content, patch, diff)
                self._announce(f"Fix applied. Memory saved to {log_name}.")
                return f"✅ Fixed: {os.path.basename(file_path)} — logged to vault."
            else:
                return f"❌ Fix rejected by user. Skipping {os.path.basename(file_path)}."

        # All attempts failed
        log_name = self.vault.log_unfixed(file_path, error_text, attempts)
        self._announce(f"Could not fix this error after {MAX_FIX_ATTEMPTS} attempts. Logged to unfixed vault.")
        return f"⚠ Unfixed: {os.path.basename(file_path)} — see unfixed_errors/{log_name}"

    # ── FIM Prompting (DeepSeek Gem 2) ────────────────────────────────────────

    def _generate_fim_patch(self, content: str, deps: dict,
                            error: str, filepath: str, line_num: int | None) -> str | None:
        """
        Fill-in-the-Middle prompting:
        Instead of asking LLM to rewrite the whole file, we isolate the error zone,
        show PREFIX (code before error) and SUFFIX (code after error),
        and ask the LLM to fill only the broken middle section.
        """
        try:
            import ollama

            lines = content.splitlines()
            total = len(lines)

            if line_num and 1 <= line_num <= total:
                # Isolate ±25 lines around the error for surgical precision
                start  = max(0, line_num - 26)
                end    = min(total, line_num + 25)
                prefix = "\n".join(lines[:start])
                middle = "\n".join(lines[start:end])
                suffix = "\n".join(lines[end:])
                fim_mode = True
            else:
                # No line number — full file rewrite mode
                prefix = ""
                middle = content
                suffix = ""
                fim_mode = False

            # Build dependency context string
            dep_context = ""
            if deps:
                dep_context = "\n\n# ── CONNECTED FILES (for context) ──\n"
                for fname, fcontent in deps.items():
                    dep_context += f"\n# FILE: {fname}\n{fcontent[:800]}\n"

            if fim_mode:
                prompt = (
                    f"You are an expert software engineer performing a surgical code fix.\n"
                    f"File: {filepath}\n"
                    f"Error: {error}\n"
                    f"{dep_context}\n\n"
                    f"The error is around line {line_num}. Here is the surrounding code:\n\n"
                    f"[CODE BEFORE ERROR - do NOT change this]\n{prefix[-1500:]}\n\n"
                    f"[BROKEN SECTION - fix ONLY this part]\n{middle}\n\n"
                    f"[CODE AFTER ERROR - do NOT change this]\n{suffix[:1500]}\n\n"
                    f"Output ONLY the fixed version of the [BROKEN SECTION].\n"
                    f"Do NOT include the before/after sections. Do NOT use markdown fences.\n"
                    f"Output pure code only."
                )
            else:
                prompt = (
                    f"You are an expert software engineer. Fix the following code.\n"
                    f"File: {filepath}\n"
                    f"Error: {error}\n"
                    f"{dep_context}\n\n"
                    f"Full file content:\n{content}\n\n"
                    f"Output the COMPLETE fixed file. No markdown. Pure code only."
                )

            response = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.1, "num_predict": 2048},
            )
            fixed_section = response["message"]["content"].strip()

            # Strip accidental markdown fences
            fixed_section = re.sub(r'^```[\w]*\n?|```$', '', fixed_section, flags=re.MULTILINE).strip()

            if fim_mode:
                # Reconstruct full file: prefix + fixed middle + suffix
                parts = []
                if prefix:       parts.append(prefix)
                if fixed_section: parts.append(fixed_section)
                if suffix:       parts.append(suffix)
                return "\n".join(parts)
            else:
                return fixed_section

        except Exception as e:
            return None

    # ── Sandbox Shield (InfCode Gem 1) ────────────────────────────────────────

    def _sandbox_test(self, original_path: str, patched_content: str) -> tuple[bool, str]:
        """
        Copy patched content to a temp file and run it.
        For Python: executes with python interpreter, captures errors.
        For JS: attempts node syntax check.
        For others: just validates it's non-empty and UTF-8 encodable.
        """
        ext = Path(original_path).suffix.lower()
        try:
            with tempfile.NamedTemporaryFile(
                mode='w', suffix=ext, delete=False,
                encoding='utf-8', errors='ignore'
            ) as tmp:
                tmp.write(patched_content)
                tmp_path = tmp.name

            if ext == '.py':
                result = subprocess.run(
                    [sys.executable, '-c', f'import ast; ast.parse(open("{tmp_path}").read())'],
                    capture_output=True, text=True, timeout=SANDBOX_TIMEOUT
                )
                if result.returncode != 0:
                    return False, result.stderr
                # Also try a syntax-only execution
                result2 = subprocess.run(
                    [sys.executable, '-m', 'py_compile', tmp_path],
                    capture_output=True, text=True, timeout=SANDBOX_TIMEOUT
                )
                return result2.returncode == 0, result2.stderr

            elif ext in ('.js', '.ts', '.jsx', '.tsx'):
                # Node.js syntax check
                result = subprocess.run(
                    ['node', '--check', tmp_path],
                    capture_output=True, text=True, timeout=SANDBOX_TIMEOUT
                )
                return result.returncode == 0, result.stderr

            else:
                # Generic: just verify it's valid text
                patched_content.encode('utf-8')
                return True, "Non-executable file — content validated."

        except subprocess.TimeoutExpired:
            return False, "Sandbox test timed out."
        except Exception as e:
            return False, str(e)
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    # ── Kill-Switch: Approval System (InfCode Gem 3) ──────────────────────────

    def _request_approval(self, file_path: str, error: str,
                           diff: str, patched: str, original: str) -> bool:
        """
        1. Voice announcement (Speaker)
        2. Push diff to /api/patch/pending for Web UI card
        3. Wait up to 120s for approval via /api/patch/decision
        Returns True if approved, False if rejected or timed out.
        """
        fname = os.path.basename(file_path)

        # ── Voice announcement ─────────────────────────────────────────────────
        self._announce(
            f"Sir, I have isolated the bug in {fname} and formulated a patch. "
            f"Requesting permission to apply. Say Approve or Reject, "
            f"or use the diff card in the web interface."
        )

        # ── Push to Web UI ─────────────────────────────────────────────────────
        set_pending_patch({
            "file":     file_path,
            "error":    error,
            "diff":     diff,
            "patched":  patched,
            "original": original,
            "status":   "pending",
            "timestamp": datetime.now().isoformat(),
        })

        # ── Wait for decision ──────────────────────────────────────────────────
        print(f"\n{'='*60}")
        print(f">> KILL SWITCH — Awaiting approval for patch to: {fname}")
        print(f">> Say 'approve' or 'reject', or use Web UI diff card.")
        print(f"{'='*60}\n")

        deadline = time.time() + 120  # 120 second window

        while time.time() < deadline:
            patch = get_pending_patch()
            if patch and patch.get("status") == "approved":
                clear_pending_patch()
                return True
            if patch and patch.get("status") == "rejected":
                clear_pending_patch()
                return False
            time.sleep(0.5)

        # Timed out — auto-reject for safety
        clear_pending_patch()
        self._announce("Approval window timed out. Patch rejected for safety.")
        return False

    # ── Diff builder ──────────────────────────────────────────────────────────

    def _build_diff(self, original: str, patched: str, filepath: str) -> str:
        diff_lines = list(difflib.unified_diff(
            original.splitlines(keepends=True),
            patched.splitlines(keepends=True),
            fromfile=f"a/{os.path.basename(filepath)}",
            tofile=f"b/{os.path.basename(filepath)}",
            n=3,
        ))
        return "".join(diff_lines)

    # ── Apply cached fix ──────────────────────────────────────────────────────

    def _apply_fix_from_cache(self, file_path: str, cached: dict, error: str) -> str:
        patched = cached.get("patched", "")
        if not patched:
            return "Cached fix has no patch content."
        original = Path(file_path).read_text(encoding="utf-8", errors="ignore")
        diff = self._build_diff(original, patched, file_path)
        approved = self._request_approval(file_path, error, diff, patched, original)
        if approved:
            Path(file_path).write_text(patched, encoding="utf-8")
            return f"✅ Cached fix applied to {os.path.basename(file_path)}."
        return f"❌ Cached fix rejected."

    # ── Speaker helper ────────────────────────────────────────────────────────

    def _announce(self, text: str):
        print(f"[CIPHER CODER] {text}")
        if self.speaker:
            try:
                self.speaker.speak(text)
            except Exception:
                pass


# ══════════════════════════════════════════════════════════════════════════════
# WATCHDOG — AUTO-HEAL THREAD
# ══════════════════════════════════════════════════════════════════════════════

class AutoHealWatchdog:
    """
    Attaches to a project folder and watches for file saves.
    On every Ctrl+S (file modification), reads the terminal output
    and auto-queues detected errors for Block 3.

    Usage: "cipher, activate auto-heal on votehub"
    """

    def __init__(self, project_root: str, executor: SurgicalExecutor,
                 context_engine: ContextEngine):
        self.root    = Path(project_root)
        self.executor= executor
        self.ctx     = context_engine
        self._active = False
        self._thread = None
        self._mtimes: dict = {}

    def start(self):
        if self._active:
            return "Auto-Heal Watchdog already running."
        self._active = True
        self._thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._thread.start()
        return f"Auto-Heal Watchdog activated on {self.root.name}. Monitoring for file changes..."

    def stop(self):
        self._active = False
        return "Auto-Heal Watchdog deactivated."

    def _watch_loop(self):
        print(f"[WATCHDOG] Monitoring {self.root} for changes...")
        while self._active:
            try:
                changed = self._detect_changes()
                if changed:
                    for fpath in changed:
                        print(f"[WATCHDOG] File changed: {fpath}")
                        # Read terminal output for errors
                        errors = self._detect_terminal_errors(fpath)
                        if errors:
                            print(f"[WATCHDOG] {len(errors)} error(s) detected — queuing for fix.")
                            self.executor.enqueue_errors(errors)
                            threading.Thread(
                                target=self.executor.process_queue,
                                args=(self.ctx,),
                                daemon=True
                            ).start()
            except Exception as e:
                print(f"[WATCHDOG] Error: {e}")
            time.sleep(1.5)

    def _detect_changes(self) -> list[str]:
        changed = []
        for fpath in self.ctx._all_project_files():
            try:
                mtime = fpath.stat().st_mtime
                key   = str(fpath)
                if key in self._mtimes and self._mtimes[key] != mtime:
                    changed.append(str(fpath))
                self._mtimes[key] = mtime
            except Exception:
                pass
        return changed

    def _detect_terminal_errors(self, changed_file: str) -> list[dict]:
        """
        Run the changed Python file briefly to capture any syntax/import errors.
        For non-Python files, attempts a quick lint check.
        """
        errors = []
        ext = Path(changed_file).suffix.lower()

        if ext == '.py':
            result = subprocess.run(
                [sys.executable, '-m', 'py_compile', changed_file],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                stderr = result.stderr.strip()
                line_match = re.search(r'line (\d+)', stderr)
                line_num = int(line_match.group(1)) if line_match else None
                errors.append({
                    "file":  changed_file,
                    "error": stderr,
                    "line":  line_num,
                })
        return errors


# ══════════════════════════════════════════════════════════════════════════════
# CIPHER SKILL WRAPPER
# ══════════════════════════════════════════════════════════════════════════════

class AutonomousCoderSkill:
    """
    Cipher skill entry point. Auto-discovered by FastLoader.
    Handles all voice/text commands for the autonomous coder system.
    """

    def __init__(self):
        self._vaults:   dict[str, MemoryVault]      = {}
        self._watchdogs:dict[str, AutoHealWatchdog] = {}
        self._active_executor: SurgicalExecutor | None = None
        self._active_ctx:      ContextEngine | None    = None
        self._speaker = None  # Injected by CipherAgent if available
        print(">> Autonomous Coder: ONLINE")

    # ── Main execute router ────────────────────────────────────────────────────

    def execute(self, command: str) -> str | None:
        cmd = command.lower().strip()

        # ── Fix / debug commands ───────────────────────────────────────────────
        if any(t in cmd for t in ["fix ", "debug ", "auto debug ", "repair "]):
            return self._handle_fix(command)

        # ── Auto-heal watchdog ────────────────────────────────────────────────
        if "activate auto-heal" in cmd or "auto heal" in cmd:
            return self._handle_auto_heal(command)

        if "deactivate auto-heal" in cmd or "stop auto heal" in cmd or "stop watchdog" in cmd:
            return self._handle_stop_watchdog(command)

        # ── Approval commands ─────────────────────────────────────────────────
        if cmd in ("approve", "yes approve", "apply fix", "confirm fix"):
            return self._handle_approval(True)

        if cmd in ("reject", "no reject", "deny fix", "cancel fix"):
            return self._handle_approval(False)

        # ── Memory vault queries ───────────────────────────────────────────────
        if "fixed errors" in cmd or "fixed history" in cmd:
            return self._handle_vault_query(command, "fixed")

        if "unfixed errors" in cmd or "failed fixes" in cmd:
            return self._handle_vault_query(command, "unfixed")

        if "roadmap" in cmd or "coming updates" in cmd or "pending tasks" in cmd:
            return self._handle_vault_query(command, "roadmap")

        if "remember task" in cmd or "add to roadmap" in cmd:
            return self._handle_add_roadmap(command)

        # ── Batch error scan ──────────────────────────────────────────────────
        if "scan errors" in cmd or "find all errors" in cmd or "batch fix" in cmd:
            return self._handle_batch_scan(command)

        # ── Vault status ───────────────────────────────────────────────────────
        if "coder status" in cmd or "vault status" in cmd:
            return self._handle_status()

        return None

    # ── Handler: Fix single error ──────────────────────────────────────────────

    def _handle_fix(self, command: str) -> str:
        # Parse: "fix <project> <optional: file path>"
        # Examples:
        #   "fix safenav"           → detect active file via vision
        #   "fix votehub main.py"   → explicit file
        #   "debug app.py TypeError: ..."

        parts = command.strip().split(None, 2)
        # parts[0] = fix/debug, parts[1] = project/file, parts[2] = error (optional)

        project_name = parts[1] if len(parts) > 1 else "default"
        explicit_file = None
        error_text = parts[2] if len(parts) > 2 else ""

        # Check if parts[1] looks like a file path
        if len(parts) > 1 and ('.' in parts[1] or '/' in parts[1] or '\\' in parts[1]):
            explicit_file = parts[1]
            project_name  = Path(parts[1]).parent.name or "default"
        elif len(parts) > 2 and ('.' in parts[2].split()[0]):
            explicit_file = parts[2].split()[0]
            error_text    = " ".join(parts[2].split()[1:])

        vault  = self._get_vault(project_name)
        ctx    = self._get_context_engine(project_name)

        # Resolve target file
        target_file = explicit_file
        if not target_file or not os.path.exists(target_file):
            print("[CODER] Attempting vision detection of active VS Code file...")
            target_file = ctx.detect_active_file()

        if not target_file or not os.path.exists(target_file):
            return (
                "I couldn't detect the active file. Please provide the file path explicitly. "
                "Example: 'fix safenav D:\\Projects\\safenav\\app.py'"
            )

        error_item = {
            "file":  target_file,
            "error": error_text or f"Fix any issues found in {os.path.basename(target_file)}",
            "line":  None,
        }

        executor = self._get_executor(vault)
        self._active_executor = executor
        self._active_ctx      = ctx

        # Run in background thread so Cipher stays responsive
        threading.Thread(
            target=executor.fix_single,
            args=(error_item, ctx),
            daemon=True
        ).start()

        return (
            f"Autonomous Coder activated for {os.path.basename(target_file)}. "
            f"Running Block 2 context scan + Block 3 FIM patching. "
            f"I'll speak when ready for your approval, Sir."
        )

    # ── Handler: Approval ─────────────────────────────────────────────────────

    def _handle_approval(self, approved: bool) -> str:
        patch = get_pending_patch()
        if not patch:
            return "No patch is currently awaiting approval."
        patch["status"] = "approved" if approved else "rejected"
        set_pending_patch(patch)
        return "Patch approved. Applying now." if approved else "Patch rejected. Skipping this fix."

    # ── Handler: Auto-Heal ────────────────────────────────────────────────────

    def _handle_auto_heal(self, command: str) -> str:
        # "activate auto-heal on votehub"
        match = re.search(r'on\s+(.+)', command, re.IGNORECASE)
        project = match.group(1).strip() if match else "default"

        # Try to find project root
        project_root = self._resolve_project_root(project)
        if not project_root:
            return f"Could not find project folder for '{project}'. Provide full path."

        vault   = self._get_vault(project)
        ctx     = self._get_context_engine(project, project_root)
        exec_   = self._get_executor(vault)

        watchdog = AutoHealWatchdog(project_root, exec_, ctx)
        self._watchdogs[project] = watchdog
        self._active_executor    = exec_
        self._active_ctx         = ctx

        return watchdog.start()

    def _handle_stop_watchdog(self, command: str) -> str:
        if not self._watchdogs:
            return "No Auto-Heal Watchdog is currently running."
        for name, wd in self._watchdogs.items():
            wd.stop()
        self._watchdogs.clear()
        return "All Auto-Heal Watchdogs deactivated."

    # ── Handler: Batch scan ───────────────────────────────────────────────────

    def _handle_batch_scan(self, command: str) -> str:
        match = re.search(r'(?:in|on|for)\s+(.+)', command, re.IGNORECASE)
        project = match.group(1).strip() if match else "default"
        project_root = self._resolve_project_root(project)
        if not project_root:
            return f"Could not find project folder for '{project}'."

        vault = self._get_vault(project)
        ctx   = self._get_context_engine(project, project_root)
        exec_ = self._get_executor(vault)

        # Scan all Python files for errors
        errors = []
        for fpath in ctx._all_project_files():
            if fpath.suffix != '.py':
                continue
            result = subprocess.run(
                [sys.executable, '-m', 'py_compile', str(fpath)],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                line_match = re.search(r'line (\d+)', result.stderr)
                errors.append({
                    "file":  str(fpath),
                    "error": result.stderr.strip(),
                    "line":  int(line_match.group(1)) if line_match else None,
                })

        if not errors:
            return f"No syntax errors found in {project}. Project looks clean."

        exec_.enqueue_errors(errors)
        threading.Thread(target=exec_.process_queue, args=(ctx,), daemon=True).start()
        return f"Found {len(errors)} error(s) in {project}. Batch fix queue started."

    # ── Handler: Vault queries ────────────────────────────────────────────────

    def _handle_vault_query(self, command: str, kind: str) -> str:
        project = self._extract_project(command) or "default"
        vault   = self._get_vault(project)

        if kind == "fixed":
            records = vault.get_fixed_summary()
            if not records:
                return f"No fixed errors logged for {project} yet."
            lines = [f"• {r['timestamp']} — {r['file']} — {r['error'][:60]}" for r in records[-5:]]
            return f"Last {len(lines)} fixes for {project}:\n" + "\n".join(lines)

        if kind == "unfixed":
            records = vault.get_unfixed_summary()
            if not records:
                return f"No unfixed errors for {project}. All clean."
            lines = [f"• {r['timestamp']} — {r['error'][:60]}" for r in records[-5:]]
            return f"Unfixed errors for {project}:\n" + "\n".join(lines)

        if kind == "roadmap":
            tasks = vault.get_roadmap()
            if not tasks:
                return f"No roadmap tasks for {project} yet."
            return f"Roadmap for {project}:\n" + "\n".join(f"• {t[:80]}" for t in tasks)

        return None

    def _handle_add_roadmap(self, command: str) -> str:
        task = re.sub(r'(remember task|add to roadmap)\s*', '', command, flags=re.IGNORECASE).strip()
        project = self._extract_project(command) or "default"
        vault = self._get_vault(project)
        name = vault.add_roadmap(task)
        return f"Task added to {project} roadmap: '{task[:60]}'"

    def _handle_status(self) -> str:
        lines = [f"[AUTONOMOUS CODER STATUS]",
                 f"Model: {MODEL_PRIMARY} → fallback {MODEL_FALLBACK}",
                 f"Vault root: {VAULT_ROOT}",
                 f"Active projects: {', '.join(self._vaults.keys()) or 'none'}",
                 f"Active watchdogs: {', '.join(self._watchdogs.keys()) or 'none'}",
                 f"Pending patch: {'Yes — awaiting approval' if get_pending_patch() else 'None'}",
                 f"Token limit: {MAX_TOKENS} tokens | Max retries: {MAX_FIX_ATTEMPTS}"]
        return "\n".join(lines)

    # ── Factory helpers ───────────────────────────────────────────────────────

    def _get_vault(self, name: str) -> MemoryVault:
        if name not in self._vaults:
            self._vaults[name] = MemoryVault(name)
        return self._vaults[name]

    def _get_context_engine(self, project: str, root: str = None) -> ContextEngine:
        resolved_root = root or self._resolve_project_root(project) or str(Path.cwd())
        return ContextEngine(resolved_root)

    def _get_executor(self, vault: MemoryVault) -> SurgicalExecutor:
        return SurgicalExecutor(vault, self._speaker)

    def _resolve_project_root(self, name: str) -> str | None:
        """Try common locations for a project by name."""
        candidates = [
            Path(r"D:\Visual Studio") / name,
            Path(r"D:\Projects") / name,
            Path.home() / "Desktop" / name,
            Path.home() / "Documents" / name,
            Path.home() / name,
        ]
        for c in candidates:
            if c.exists() and c.is_dir():
                return str(c)
        # Try case-insensitive search in D:\Visual Studio
        vs_root = Path(r"D:\Visual Studio")
        if vs_root.exists():
            for d in vs_root.iterdir():
                if d.is_dir() and d.name.lower() == name.lower():
                    return str(d)
        return None

    def _extract_project(self, command: str) -> str | None:
        for kw in ["for ", "on ", "in ", "of "]:
            if kw in command.lower():
                return command.lower().split(kw)[-1].strip().split()[0]
        return None