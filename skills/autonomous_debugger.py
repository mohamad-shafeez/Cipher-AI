import os
import glob
import subprocess
import requests
import re


class AutonomousDebuggerSkill:
    def __init__(self):
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model = "qwen2.5-coder:7b"
        self.max_retries = 3
        self.target_dir = "generated_code"
        print(">> Auto-Debugger Skill: ONLINE (Self-Healing Loop Active)")

    def _extract_code(self, raw_text: str) -> str:
        """
        Extracts Python code from LLM response.
        Handles markdown code blocks safely.
        """

        # Match ```python ... ``` or ``` ... ```
        matches = re.findall(r"```(?:python)?\n(.*?)```", raw_text, re.DOTALL | re.IGNORECASE)
        if matches:
            return matches[0].strip()

        # Fallback: return raw text if no markdown found
        return raw_text.strip()

    def execute(self, command: str) -> str | None:
        try:
            if not command:
                return None

            cmd = command.lower().strip()

            # --- TRIGGER DETECTION ---
            triggers = ["auto debug", "autonomous debug", "fix loop", "self heal", "debug loop"]
            if not any(t in cmd for t in triggers):
                return None

            # Ensure sandbox exists
            if not os.path.exists(self.target_dir):
                return "Sir, the generated code sandbox does not exist yet."

            # Find all Python files
            py_files = glob.glob(os.path.join(self.target_dir, "**/*.py"), recursive=True)

            if not py_files:
                return "Sir, I could not find any Python files in the sandbox to debug."

            # Pick most recently modified file
            target = max(py_files, key=os.path.getmtime)
            print(f"\n>> [AutoDebugger] Initiating self-healing loop on: {target}")

            for attempt in range(1, self.max_retries + 1):
                print(f">> [AutoDebugger] Attempt {attempt}/{self.max_retries}...")

                # Execute file
                result = subprocess.run(
                    ["python", target],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=os.path.dirname(os.path.abspath(target))
                )

                # Success case
                if result.returncode == 0:
                    print(">> [AutoDebugger] Execution successful. Zero errors.")
                    return (
                        f"Sir, I have successfully patched '{os.path.basename(target)}'. "
                        f"It is running cleanly after {attempt} attempt{'s' if attempt > 1 else ''}."
                    )

                # Capture error
                error = result.stderr.strip() or result.stdout.strip()
                print(f">> [AutoDebugger] Error detected:\n{error[:200]}...")

                # Read current code
                with open(target, "r", encoding="utf-8") as f:
                    code = f.read()

                # Build LLM prompt
                prompt = (
                    "You are an expert Python debugger.\n\n"
                    "Fix the following broken Python code.\n\n"
                    f"ERROR:\n{error}\n\n"
                    f"CODE:\n{code}\n\n"
                    "Return ONLY the corrected full Python file inside a markdown code block."
                )

                # Call Ollama
                resp = requests.post(
                    self.ollama_url,
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False
                    },
                    timeout=60
                )

                raw_fixed_code = resp.json().get("response", "").strip()
                clean_code = self._extract_code(raw_fixed_code)

                if clean_code:
                    with open(target, "w", encoding="utf-8") as f:
                        f.write(clean_code)
                    print(">> [AutoDebugger] Patch applied. Re-evaluating...")
                else:
                    return "Sir, the neural engine failed to generate a valid patch. Manual intervention required."

            return (
                f"Sir, '{os.path.basename(target)}' still contains errors after "
                f"{self.max_retries} attempts. Escalating for manual review."
            )

        except Exception as e:
            print(f"[AutoDebugger Error] {e}")
            return None