"""
Cipher - Executor Skill Module
File: skills/executor.py
Author: Claude (Lead Engine Developer)
Team: Cipher AI Dev Team (Lead: Shafeez | Frontend: DeepSeek | Media+Utils: ChatGPT | Engine: Claude)

Responsibility:
    Triggers on "run the code" or "execute the script" commands.
    Finds the most recent generated file, detects whether it's Python or Node.js,
    runs it via subprocess, captures stdout/stderr, and returns the terminal
    output as a readable string for Cipher to speak.
"""

import os
import glob
import subprocess
import shutil


# Supported runtimes: maps file extension → (runtime_display_name, executable)
SUPPORTED_RUNTIMES = {
    "py":  ("Python",  "python"),
    "js":  ("Node.js", "node"),
}

# Extensions that can be "opened" but not run as scripts (browser-opened)
BROWSER_TYPES = {"html", "htm"}

# Max characters of output to return to Cipher (voice output should stay concise)
MAX_OUTPUT_CHARS = 800

# Subprocess timeout in seconds
EXECUTION_TIMEOUT = 30


class ExecutorSkill:
    """
    Skill module that allows Cipher to execute the code it just generated.
    Supports Python (.py) and Node.js (.js) scripts.
    HTML files are opened in the default browser instead.
    """

    TRIGGER_PHRASES = [
        "run the code",
        "execute the code",
        "run the script",
        "execute the script",
        "run it",
        "execute it",
        "run the file",
        "execute the file",
        "run the program",
        "execute the program",
        "test the code",
        "run the python",
        "run the node",
        "run the javascript",
        "launch the script",
    ]

    GENERATED_CODE_DIR = "generated_code"

    def __init__(self):
        """Initializes the ExecutorSkill."""
        pass

    def _is_triggered(self, command: str) -> bool:
        command_lower = command.lower().strip()
        return any(phrase in command_lower for phrase in self.TRIGGER_PHRASES)

    def _get_most_recent_runnable_file(self) -> str | None:
        """
        Scans generated_code/ recursively and returns the full path to the most
        recently modified file that has a runnable or openable extension.

        Priority order for same-timestamp ties:
            .py > .js > .html (most executable first)

        Returns:
            str | None: Full file path, or None if nothing runnable found.
        """
        if not os.path.exists(self.GENERATED_CODE_DIR):
            return None

        runnable_exts = set(SUPPORTED_RUNTIMES.keys()) | BROWSER_TYPES

        all_files = glob.glob(
            os.path.join(self.GENERATED_CODE_DIR, "**", "*"),
            recursive=True,
        )
        all_files = [
            f for f in all_files
            if os.path.isfile(f) and f.rsplit(".", 1)[-1].lower() in runnable_exts
        ]

        if not all_files:
            return None

        # Sort by modification time (most recent first)
        all_files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
        return all_files[0]

    def _check_runtime_available(self, executable: str) -> bool:
        """Checks whether a runtime (python/node) is available on PATH."""
        return shutil.which(executable) is not None

    def _format_output(self, stdout: str, stderr: str, returncode: int, display_name: str, filename: str) -> str:
        """
        Formats subprocess output into a clean, speakable Cipher response.

        Rules:
            - If stdout is empty and returncode == 0: report clean exit.
            - If stderr has content: lead with the error.
            - Truncate long outputs with a note.
        """
        has_stdout = bool(stdout.strip())
        has_stderr = bool(stderr.strip())
        success = returncode == 0

        if success and not has_stdout and not has_stderr:
            return (
                f"Sir, the {display_name} script '{filename}' ran successfully "
                f"with no output."
            )

        parts = []

        if success:
            parts.append(f"Sir, '{filename}' ran successfully.")
        else:
            parts.append(f"Sir, '{filename}' exited with an error (code {returncode}).")

        if has_stdout:
            output_text = stdout.strip()
            if len(output_text) > MAX_OUTPUT_CHARS:
                output_text = output_text[:MAX_OUTPUT_CHARS] + "... [output truncated]"
            parts.append(f"Output: {output_text}")

        if has_stderr:
            error_text = stderr.strip()
            if len(error_text) > MAX_OUTPUT_CHARS:
                error_text = error_text[:MAX_OUTPUT_CHARS] + "... [truncated]"
            parts.append(f"Error output: {error_text}")

        return " ".join(parts)

    def _run_script(self, filepath: str) -> str:
        """
        Executes a Python or Node.js script using subprocess.
        Captures stdout and stderr, enforces a timeout, and returns
        a formatted result string.

        Args:
            filepath (str): Full path to the script to run.

        Returns:
            str: Formatted output string for Cipher to speak.
        """
        ext = filepath.rsplit(".", 1)[-1].lower()
        filename = os.path.basename(filepath)

        if ext not in SUPPORTED_RUNTIMES:
            return f"Sir, I don't know how to run .{ext} files directly."

        display_name, executable = SUPPORTED_RUNTIMES[ext]

        if not self._check_runtime_available(executable):
            return (
                f"Sir, {display_name} doesn't appear to be installed or isn't on the system PATH. "
                f"Please install {display_name} to run this script."
            )

        print(f"\n>> [ExecutorSkill] Running: {executable} {filepath}")

        try:
            process = subprocess.run(
                [executable, filepath],
                capture_output=True,
                text=True,
                timeout=EXECUTION_TIMEOUT,
                cwd=os.path.dirname(filepath),  # Run from the file's own directory
            )

            return self._format_output(
                stdout=process.stdout,
                stderr=process.stderr,
                returncode=process.returncode,
                display_name=display_name,
                filename=filename,
            )

        except subprocess.TimeoutExpired:
            return (
                f"Sir, '{filename}' was terminated after {EXECUTION_TIMEOUT} seconds. "
                "It may contain an infinite loop or is waiting for input."
            )

        except FileNotFoundError:
            return (
                f"Sir, the {display_name} executable could not be found. "
                "Please verify your installation."
            )

        except PermissionError:
            return (
                f"Sir, I don't have permission to execute '{filename}'. "
                "Please check the file permissions."
            )

        except Exception as e:
            return f"Sir, an unexpected error occurred while running '{filename}': {e}."

    def _open_in_browser(self, filepath: str) -> str:
        """
        Opens an HTML file in the system's default browser using os.startfile (Windows)
        or xdg-open (Linux/Mac).

        Args:
            filepath (str): Full path to the HTML file.

        Returns:
            str: Confirmation string for Cipher to speak.
        """
        filename = os.path.basename(filepath)
        abs_path = os.path.abspath(filepath)

        try:
            import platform
            system = platform.system()

            if system == "Windows":
                os.startfile(abs_path)
            elif system == "Darwin":
                subprocess.Popen(["open", abs_path])
            else:
                subprocess.Popen(["xdg-open", abs_path])

            return f"Sir, I've opened '{filename}' in your default browser."

        except Exception as e:
            return (
                f"Sir, I tried to open '{filename}' but encountered an error: {e}. "
                f"You can open it manually at: {abs_path}"
            )

    def execute(self, command: str) -> str | None:
        """
        Entry point called by the Cipher core engine.

        Workflow:
            1. Check trigger phrases.
            2. Find the most recently generated runnable file.
            3. If it's .py or .js → run with subprocess and capture output.
            4. If it's .html → open in browser.
            5. Return the result for Cipher to speak.

        Args:
            command (str): The voice/text command from the Cipher engine.

        Returns:
            str | None: Response string if triggered, None to pass to next skill.
        """
        if not self._is_triggered(command):
            return None

        target_file = self._get_most_recent_runnable_file()

        if target_file is None:
            return (
                "Sir, I couldn't find any runnable files in the generated_code folder. "
                "Please ask me to build something first."
            )

        ext = target_file.rsplit(".", 1)[-1].lower()
        filename = os.path.basename(target_file)

        print(f"\n>> [ExecutorSkill] Target file: {target_file}")

        # HTML → open in browser
        if ext in BROWSER_TYPES:
            return self._open_in_browser(target_file)

        # Python / Node.js → run and capture output
        return self._run_script(target_file)