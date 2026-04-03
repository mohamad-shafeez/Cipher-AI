"""
Cipher - Coding Swarm v2.0
File: codeskills/swarm.py
Author: Claude (Lead Engine Developer)
Team: Cipher AI Dev Team (Lead: Shafeez | Frontend: DeepSeek | Media+Utils: ChatGPT | Engine: Claude)

Changelog v2.0:
    - execute_swarm() now supports "Project Mode" for multi-file generation
      (HTML + CSS + JS), auto-creates a project subfolder, and writes each file.
    - debug_file() response message fixed (was always hardcoded, now dynamic).
    - Internal helpers refactored for clarity and reuse across both modes.
"""

import re
import os
import json
import requests


# ─────────────────────────────────────────────────────────────────────────────
# PROJECT MODE DETECTION
# Phrases that indicate the user wants a multi-file project, not a single file.
# ─────────────────────────────────────────────────────────────────────────────
PROJECT_TRIGGERS = [
    "website with css and js",
    "website with css & js",
    "html css and js",
    "html, css and js",
    "html, css, and js",
    "html css js",
    "full website",
    "multi-file",
    "multifile",
    "with separate css",
    "with separate js",
    "with external css",
    "with external js",
    "project",
]


class CodingSwarm:
    def __init__(self):
        # Ollama local API endpoint
        self.ollama_url = "http://localhost:11434/api/generate"

        # Root output directory for all generated files
        self.output_dir = "generated_code"
        os.makedirs(self.output_dir, exist_ok=True)

    # ─────────────────────────────────────────────────────────────────────────
    # PRIVATE: OLLAMA COMMUNICATION
    # ─────────────────────────────────────────────────────────────────────────

    def _query_model(self, model_name: str, prompt: str, system_prompt: str) -> str:
        """Sends a prompt to an Ollama model and returns the raw response string."""
        print(f"      [Swarm] Waking up {model_name}...")

        payload = {
            "model": model_name,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
        }

        try:
            response = requests.post(self.ollama_url, json=payload, timeout=300)
            response.raise_for_status()
            return response.json().get("response", "")

        except requests.exceptions.ConnectionError:
            print("      [Swarm Error] Ollama is not running.")
            return "Error: Could not connect to Ollama. Is it running?"

        except requests.exceptions.Timeout:
            print("      [Swarm Error] Ollama request timed out.")
            return "Error: Ollama request timed out. The model may be too slow."

        except requests.exceptions.RequestException as e:
            print(f"      [Swarm Error] Request failed: {e}")
            return f"Error: {e}"

    # ─────────────────────────────────────────────────────────────────────────
    # PRIVATE: CODE EXTRACTION
    # ─────────────────────────────────────────────────────────────────────────

    def _extract_code(self, raw_text: str, language: str = "html") -> str:
        """
        Extracts clean code from a markdown fenced block.
        Tries the specific language first, then falls back to any code block,
        then returns raw text if no blocks found at all.
        """
        # Try language-specific block first
        pattern = rf"```(?:{re.escape(language)})?\n(.*?)```"
        matches = re.findall(pattern, raw_text, re.DOTALL | re.IGNORECASE)
        if matches:
            return matches[0].strip()

        # Generic fallback — any fenced block
        generic_matches = re.findall(r"```(?:\w+)?\n(.*?)```", raw_text, re.DOTALL)
        if generic_matches:
            return generic_matches[0].strip()

        return raw_text.strip()

    # ─────────────────────────────────────────────────────────────────────────
    # PRIVATE: FILE I/O
    # ─────────────────────────────────────────────────────────────────────────

    def _save_file(self, filepath: str, content: str) -> None:
        """Writes content to a file, creating parent directories if needed."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"      [Swarm] Saved → {filepath}")

    # ─────────────────────────────────────────────────────────────────────────
    # PRIVATE: PROJECT MODE DETECTION
    # ─────────────────────────────────────────────────────────────────────────

    def _is_project_request(self, user_request: str) -> bool:
        """Returns True if the request implies multi-file project generation."""
        request_lower = user_request.lower()
        return any(trigger in request_lower for trigger in PROJECT_TRIGGERS)

    def _derive_project_name(self, user_request: str) -> str:
        """
        Derives a safe folder name from the user's request.
        e.g. "Build a portfolio website with CSS and JS" → "portfolio_website"
        """
        # Remove common filler words, keep meaningful ones
        stopwords = {
            "a", "an", "the", "build", "make", "create", "generate",
            "with", "and", "for", "me", "my", "please", "write", "code",
            "css", "js", "html", "javascript", "website", "full", "using",
            "separate", "external",
        }
        words = re.sub(r"[^a-z0-9\s]", "", user_request.lower()).split()
        meaningful = [w for w in words if w not in stopwords]
        name = "_".join(meaningful[:4]) if meaningful else "project"
        return name or "project"

    # ─────────────────────────────────────────────────────────────────────────
    # PRIVATE: SINGLE FILE GENERATION (original behaviour)
    # ─────────────────────────────────────────────────────────────────────────

    def _generate_single_file(self, user_request: str, plan: str, filename: str) -> dict:
        """
        Generates a single file using qwen2.5-coder and saves it.
        Returns {"message": str, "code": str, "files": {filename: code}}.
        """
        print(">> STEP 2: Qwen2.5-Coder is writing the code...")

        file_ext = filename.rsplit(".", 1)[-1]

        code_prompt = f"""
Based on this architectural plan:
{plan}

Write the FULL and COMPLETE code for a single file named '{filename}'.

RULES:
- Output ONLY the code inside ONE markdown code block
- No explanations, no comments outside the code block
- The code must be complete and production-ready
"""

        raw_output = self._query_model(
            model_name="qwen2.5-coder:7b",
            prompt=code_prompt,
            system_prompt="You are an expert developer. Output only code inside a markdown block. Zero explanations.",
        )

        clean_code = self._extract_code(raw_output, language=file_ext)
        filepath = os.path.join(self.output_dir, filename)
        self._save_file(filepath, clean_code)

        return {"filename": filename, "code": clean_code, "filepath": filepath}

    # ─────────────────────────────────────────────────────────────────────────
    # PRIVATE: PROJECT MODE — MULTI-FILE GENERATION
    # ─────────────────────────────────────────────────────────────────────────

    def _generate_project(self, user_request: str, plan: str) -> dict:
        """
        Generates HTML, CSS, and JS as three separate files inside a project subfolder.
        The HTML file references style.css and script.js via relative paths.

        Returns:
            dict with keys: project_dir, files (dict of filename→code), main_file, main_code
        """
        project_name = self._derive_project_name(user_request)
        project_dir = os.path.join(self.output_dir, project_name)
        os.makedirs(project_dir, exist_ok=True)

        print(f">> [Project Mode] Creating project folder: {project_dir}")

        generated = {}

        # ── 1. Generate CSS ───────────────────────────────────────────────
        print(">> STEP 2a: Qwen2.5-Coder is writing style.css...")

        css_prompt = f"""
Based on this architectural plan:
{plan}

Write ONLY the CSS code for 'style.css' for this project: '{user_request}'.

RULES:
- Output ONLY CSS inside ONE ```css block
- No HTML, no JS, no explanations
- Use clean modern CSS, including responsive design
"""
        raw_css = self._query_model(
            model_name="qwen2.5-coder:7b",
            prompt=css_prompt,
            system_prompt="You are a CSS expert. Output only CSS inside a markdown code block.",
        )
        css_code = self._extract_code(raw_css, language="css")
        self._save_file(os.path.join(project_dir, "style.css"), css_code)
        generated["style.css"] = css_code

        # ── 2. Generate JS ────────────────────────────────────────────────
        print(">> STEP 2b: Qwen2.5-Coder is writing script.js...")

        js_prompt = f"""
Based on this architectural plan:
{plan}

Write ONLY the JavaScript code for 'script.js' for this project: '{user_request}'.

RULES:
- Output ONLY JavaScript inside ONE ```javascript block
- No HTML, no CSS, no explanations
- Use clean, modern vanilla JS (ES6+)
"""
        raw_js = self._query_model(
            model_name="qwen2.5-coder:7b",
            prompt=js_prompt,
            system_prompt="You are a JS expert. Output only JavaScript inside a markdown code block.",
        )
        js_code = self._extract_code(raw_js, language="javascript")
        self._save_file(os.path.join(project_dir, "script.js"), js_code)
        generated["script.js"] = js_code

        # ── 3. Generate HTML (links to style.css + script.js) ────────────
        print(">> STEP 2c: Qwen2.5-Coder is writing index.html...")

        html_prompt = f"""
Based on this architectural plan:
{plan}

Write ONLY the HTML for 'index.html' for this project: '{user_request}'.

IMPORTANT LINKING RULES:
- Link the stylesheet with: <link rel="stylesheet" href="style.css">
- Link the script with: <script src="script.js" defer></script>
- Do NOT embed any CSS or JS directly in the HTML
- Output ONLY HTML inside ONE ```html block
- No explanations
"""
        raw_html = self._query_model(
            model_name="qwen2.5-coder:7b",
            prompt=html_prompt,
            system_prompt="You are an HTML expert. Output only HTML inside a markdown code block.",
        )
        html_code = self._extract_code(raw_html, language="html")
        self._save_file(os.path.join(project_dir, "index.html"), html_code)
        generated["index.html"] = html_code

        return {
            "project_dir": project_dir,
            "files": generated,
            "main_file": "index.html",
            "main_code": html_code,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC: EXECUTE SWARM (v2.0 — Single File + Project Mode)
    # ─────────────────────────────────────────────────────────────────────────

    def execute_swarm(self, user_request: str, filename: str = "index.html") -> dict:
        """
        Orchestrates the full Cipher coding swarm pipeline.

        Single File Mode (default):
            Generates one file, saves to generated_code/<filename>.

        Project Mode (triggered automatically):
            If user_request contains multi-file indicators (e.g. "website with CSS and JS"),
            generates index.html + style.css + script.js inside a named subfolder.

        Args:
            user_request (str): The natural language description of what to build.
            filename (str): Target filename for single-file mode. Ignored in project mode.

        Returns:
            dict: {
                "message": str,         # Cipher's spoken confirmation
                "code": str,            # Main file code (index.html in project mode)
                "files": dict,          # {filename: code} — all generated files
                "project_dir": str      # Folder path (project mode only, else None)
            }
        """
        print("\n>> [SWARM v2.0 INITIATED] Orchestrating AI Agents...")

        # ── STEP 1: Architecture Planning ────────────────────────────────
        print(">> STEP 1: Innovator is planning the architecture...")

        is_project = self._is_project_request(user_request)
        mode_hint = (
            "Plan for a multi-file web project with separate index.html, style.css, and script.js."
            if is_project
            else f"Plan for a single file named '{filename}'."
        )

        plan_prompt = f"""
Create a concise, step-by-step architectural plan to build this:
'{user_request}'

{mode_hint}
Keep it structured and brief.
"""
        plan = self._query_model(
            model_name="phi3.5",
            prompt=plan_prompt,
            system_prompt="You are a senior software architect. Output only the architectural plan.",
        )

        # ── STEP 2+3: Code Generation ─────────────────────────────────────
        if is_project:
            print(">> [Project Mode Detected] Generating multi-file project...")
            result = self._generate_project(user_request, plan)
            saved_label = f"project folder '{result['project_dir']}'"
            main_code = result["main_code"]
            all_files = result["files"]
            project_dir = result["project_dir"]
        else:
            print(">> [Single File Mode] Generating single file...")
            result = self._generate_single_file(user_request, plan, filename)
            saved_label = f"file '{filename}'"
            main_code = result["code"]
            all_files = {filename: main_code}
            project_dir = None

        # ── STEP 4: Voice Response ────────────────────────────────────────
        print(">> STEP 4: Documenter generating voice response...")

        summary_prompt = f"""
I just successfully generated and saved {saved_label} 
based on this request: '{user_request}'.

Respond in ONE short sentence confirming completion, like Cipher would say it.
"""
        final_speech = self._query_model(
            model_name="phi3.5",
            prompt=summary_prompt,
            system_prompt="You are Cipher, an AI voice assistant. Speak concisely and confidently.",
        )

        print(f">> [SWARM COMPLETE] {saved_label} generated successfully.")

        return {
            "message": final_speech,
            "code": main_code,
            "files": all_files,
            "project_dir": project_dir,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC: DEBUG FILE (v1.1 — response message fix)
    # ─────────────────────────────────────────────────────────────────────────

    def debug_file(self, filename: str, error_description: str) -> dict:
        """
        Reads an existing generated file, sends it to qwen2.5-coder for bug fixing,
        overwrites the file with the patched version, and returns a confirmation.

        Args:
            filename (str): The filename inside generated_code/ to debug.
            error_description (str): User's description of the bug or error.

        Returns:
            dict: {"message": str, "code": str}
        """
        print(f"\n>> [DEBUGGER INITIATED] Analyzing {filename}...")

        filepath = os.path.join(self.output_dir, filename)

        if not os.path.exists(filepath):
            return {
                "message": f"Sir, I could not find '{filename}' in the generated_code folder.",
                "code": "",
            }

        with open(filepath, "r", encoding="utf-8") as f:
            existing_code = f.read()

        # ── STEP 1: Fix the code ──────────────────────────────────────────
        print(">> STEP 1: Qwen2.5-Coder is analyzing the error and patching the code...")

        fix_prompt = f"""
Here is the existing code for '{filename}':
{existing_code}

The user reported this error:
'{error_description}'

Rewrite the FULL file with the bug fixed.

RULES:
- Output ONLY the corrected code inside ONE markdown block
- Return the COMPLETE file — do not truncate anything
- No explanations, no apologies
"""
        raw_output = self._query_model(
            model_name="qwen2.5-coder:7b",
            prompt=fix_prompt,
            system_prompt="You are an expert debugger. Output only the corrected code. No explanations.",
        )

        # ── STEP 2: Clean + Overwrite ─────────────────────────────────────
        print(">> STEP 2: Cleaning and overwriting file...")

        file_ext = filename.rsplit(".", 1)[-1]
        clean_code = self._extract_code(raw_output, language=file_ext)
        self._save_file(filepath, clean_code)

        # ── STEP 3: Voice Response ────────────────────────────────────────
        print(">> STEP 3: Documenter generating voice response...")

        summary_prompt = f"""
I just fixed a bug in '{filename}'. The reported error was: '{error_description}'.
Respond in ONE short sentence confirming the file has been patched.
"""
        final_speech = self._query_model(
            model_name="phi3.5",
            prompt=summary_prompt,
            system_prompt="You are Cipher, an AI voice assistant. Speak concisely.",
        )

        print(f">> [DEBUGGER COMPLETE] {filename} has been patched.")

        return {
            "message": final_speech,   # ← FIXED: was hardcoded in v1, now dynamic
            "code": clean_code,
        }