"""
Cipher Skill — OS Automator
Organ: The RawDog Task Executor
Converts natural language task descriptions into Python scripts,
executes them via subprocess, and returns the result.
Uses TurboBrain (local 8B LLM) to write the script — zero cloud dependency.
Includes safety rails to prevent destructive system operations.
"""

import os
import re
import subprocess
import sys
import hashlib
from datetime import datetime


SCRIPTS_DIR = "temp_scripts"
SCRIPT_TIMEOUT = 30  # Max seconds a generated script may run


# ── Safety Rails ──────────────────────────────────────────────────────────────
# Any generated script containing these patterns is BLOCKED before execution.
BLOCKED_PATTERNS = [
    # Disk destruction
    r"rm\s+-rf\s+[/\\]",
    r"rmdir\s+/s\s+/q\s+[A-Za-z]:\\",
    r"format\s+[A-Za-z]:",
    r"mkfs\.",
    r"dd\s+if=",
    r"shutil\.rmtree\(['\"]\/",        # rmtree on root
    r"shutil\.rmtree\(['\"]C:\\\\",    # rmtree on C drive root

    # System-level destruction
    r"os\.system\(['\"]shutdown",
    r"subprocess.*shutdown",
    r"subprocess.*format",
    r"ctypes.*DeviceIoControl",

    # Credential / registry theft
    r"winreg.*SAM",
    r"HKEY_LOCAL_MACHINE.*SAM",
    r"lsass",

    # Network exfiltration patterns
    r"socket\.connect.*\b(?!localhost|127\.0\.0\.1)\b\d{1,3}\.\d{1,3}",
    r"requests\.(post|put|patch).*password",
    r"requests\.(post|put|patch).*secret",
    r"requests\.(post|put|patch).*token",

    # Self-modification / infinite loops
    r"while\s+True:.*os\.(remove|unlink)",
    r"os\.remove\(__file__\)",
]

# Paths explicitly protected — scripts cannot touch these
PROTECTED_PATHS = [
    "C:\\Windows",
    "C:\\Program Files",
    "/etc",
    "/usr",
    "/bin",
    "/sbin",
    "/boot",
    os.path.expanduser("~/.ssh"),
    os.path.expanduser("~/.aws"),
    os.path.expanduser("~/.env"),
]


class OsAutomatorSkill:
    def __init__(self):
        os.makedirs(SCRIPTS_DIR, exist_ok=True)
        print(">> OS Automator: ONLINE")

    def execute(self, command: str) -> str | None:
        cmd = command.lower().strip()

        triggers = [
            "automate ",
            "run os task",
            "os task ",
            "organize my files",
            "organize files",
            "run script",
            "execute task",
            "write a script",
            "create a script",
            "automate task",
            "file task ",
            "batch rename",
            "move all ",
            "delete all duplicate",
            "clean up ",
        ]

        matched = next((t for t in triggers if t in cmd), None)
        if not matched:
            return None

        # Extract the task description
        task = command
        for t in triggers:
            task = re.sub(re.escape(t), "", task, flags=re.IGNORECASE).strip()

        task = task.strip().strip("'\"")
        if not task or len(task) < 5:
            return "Describe the task to automate. Example: 'automate move all PDFs from Downloads to Documents'"

        return self._run_automation(task)

    # ── Core Pipeline ──────────────────────────────────────────────────────

    def _run_automation(self, task: str) -> str:
        # Step 1: Generate Python script from task description
        script = self._generate_script(task)
        if not script:
            return "TurboBrain could not generate a script for that task. Try rephrasing."

        # Step 2: Safety audit
        blocked, reason = self._safety_check(script)
        if blocked:
            return f"⛔ Script BLOCKED by safety rails: {reason}\nGenerated script was not executed."

        # Step 3: Save script to disk
        filepath = self._save_script(script, task)

        # Step 4: Execute and capture output
        return self._execute_script(filepath, task)

    # ── Script Generation ──────────────────────────────────────────────────

    def _generate_script(self, task: str) -> str | None:
        try:
            from skills.turbo_brain import turbo_think
        except ImportError:
            return self._fallback_script(task)

        prompt = f"""You are a Python automation expert. Write a safe, single-purpose Python script for this task:

TASK: {task}

STRICT RULES:
1. Use ONLY Python standard library (os, shutil, pathlib, glob, re, json, csv, datetime).
2. Do NOT import requests, socket, subprocess, or any network library.
3. Do NOT delete files permanently — use shutil.move() to a trash folder instead of os.remove().
4. Do NOT touch system directories: C:\\Windows, /etc, /usr, /bin, /sbin.
5. Always use os.path.expanduser("~") for home directory paths.
6. Add print() statements showing what the script did (files moved, renamed, etc.).
7. Wrap everything in a try/except and print errors clearly.
8. The script must COMPLETE in under 30 seconds.
9. Output ONLY the Python code. No explanations, no markdown fences, no comments outside the code.

Python script:"""

        try:
            result = turbo_think(prompt)
            if not result:
                return self._fallback_script(task)

            # Strip markdown fences if LLM added them
            result = re.sub(r'^```python\s*|^```\s*|```$', '', result.strip(), flags=re.MULTILINE)
            return result.strip()
        except Exception:
            return self._fallback_script(task)

    def _fallback_script(self, task: str) -> str | None:
        """
        Minimal hardcoded scripts for common tasks
        when TurboBrain is unavailable.
        """
        task_lower = task.lower()

        if "pdf" in task_lower and ("move" in task_lower or "organize" in task_lower):
            return self._template_move_files("Downloads", "Documents/PDFs", "*.pdf")

        if "screenshot" in task_lower and ("move" in task_lower or "organize" in task_lower):
            return self._template_move_files("Desktop", "Pictures/Screenshots", "*.png")

        if "duplicate" in task_lower:
            return self._template_find_duplicates()

        if "rename" in task_lower:
            return """
import os
from pathlib import Path
from datetime import datetime

folder = Path(os.path.expanduser("~/Downloads"))
count = 0
for f in folder.iterdir():
    if f.is_file():
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        new_name = f.parent / f"{timestamp}_{count:03d}{f.suffix}"
        f.rename(new_name)
        print(f"Renamed: {f.name} -> {new_name.name}")
        count += 1
print(f"Done. Renamed {count} files.")
"""
        return None

    def _template_move_files(self, src_folder: str, dst_folder: str, pattern: str) -> str:
        return f"""
import os
import shutil
import glob
from pathlib import Path

src = Path(os.path.expanduser("~/{src_folder}"))
dst = Path(os.path.expanduser("~/{dst_folder}"))
dst.mkdir(parents=True, exist_ok=True)

moved = 0
for filepath in src.glob("{pattern}"):
    try:
        shutil.move(str(filepath), str(dst / filepath.name))
        print(f"Moved: {{filepath.name}}")
        moved += 1
    except Exception as e:
        print(f"Error moving {{filepath.name}}: {{e}}")

print(f"Done. Moved {{moved}} files to {{dst}}")
"""

    def _template_find_duplicates(self) -> str:
        return """
import os
import hashlib
from pathlib import Path
from collections import defaultdict

folder = Path(os.path.expanduser("~/Downloads"))
hashes = defaultdict(list)

for f in folder.iterdir():
    if f.is_file():
        try:
            h = hashlib.md5(f.read_bytes()).hexdigest()
            hashes[h].append(f)
        except Exception:
            pass

duplicates_found = 0
for h, files in hashes.items():
    if len(files) > 1:
        print(f"Duplicate group ({len(files)} files):")
        for f in files:
            print(f"  {f.name}")
        duplicates_found += len(files) - 1

if duplicates_found == 0:
    print("No duplicates found in Downloads folder.")
else:
    print(f"Found {duplicates_found} duplicate file(s). No files were deleted.")
"""

    # ── Safety Check ──────────────────────────────────────────────────────

    def _safety_check(self, script: str) -> tuple[bool, str]:
        """
        Returns (is_blocked: bool, reason: str).
        Audits the generated script against all safety rails before execution.
        """
        # Check blocked regex patterns
        for pattern in BLOCKED_PATTERNS:
            if re.search(pattern, script, re.IGNORECASE):
                return True, f"Blocked pattern detected: '{pattern}'"

        # Check for protected path references
        for protected in PROTECTED_PATHS:
            if protected.lower() in script.lower():
                return True, f"Script references protected path: '{protected}'"

        # Block scripts that are suspiciously short (likely incomplete/garbage)
        if len(script.strip()) < 30:
            return True, "Generated script is too short to be valid."

        # Block anything that's clearly not Python
        if script.strip().startswith(("#!/bin/bash", "#!/bin/sh", "@echo")):
            return True, "Only Python scripts are permitted."

        return False, ""

    # ── Save & Execute ─────────────────────────────────────────────────────

    def _save_script(self, script: str, task: str) -> str:
        """Save generated script with a unique name."""
        safe_task = re.sub(r'[^\w]', '_', task)[:35]
        timestamp = datetime.now().strftime('%H%M%S')
        # Include content hash to avoid overwriting identical scripts
        content_hash = hashlib.md5(script.encode()).hexdigest()[:6]
        filename = f"auto_{safe_task}_{timestamp}_{content_hash}.py"
        filepath = os.path.join(SCRIPTS_DIR, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# Cipher OS Automator — Generated Script\n")
            f.write(f"# Task: {task}\n")
            f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(script)

        return filepath

    def _execute_script(self, filepath: str, task: str) -> str:
        """Execute the generated script and return its output."""
        try:
            result = subprocess.run(
                [sys.executable, filepath],
                capture_output=True,
                text=True,
                timeout=SCRIPT_TIMEOUT,
                cwd=os.path.expanduser("~"),  # Run from home dir for safety
            )

            stdout = result.stdout.strip()
            stderr = result.stderr.strip()

            if result.returncode == 0:
                output = stdout if stdout else "Script completed with no output."
                return f"✅ Task '{task}' completed:\n{output}"
            else:
                error_msg = stderr if stderr else "Unknown error."
                # Truncate very long error traces
                if len(error_msg) > 600:
                    error_msg = error_msg[-600:]
                return (
                    f"⚠️ Script ran but encountered an error:\n{error_msg}\n"
                    f"Script saved at: {filepath}"
                )

        except subprocess.TimeoutExpired:
            return (
                f"⏱️ Script timed out after {SCRIPT_TIMEOUT}s and was terminated.\n"
                f"Task may be too complex. Try breaking it into smaller steps."
            )
        except Exception as e:
            return f"OS Automator execution error: {e}\nScript saved at: {filepath}"