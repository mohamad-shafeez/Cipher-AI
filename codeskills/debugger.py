"""
Cipher - Debugger Skill Module
File: skills/debugger.py
Author: Claude (Lead Engine Developer)
Team: Cipher AI Dev Team (Lead: Shafeez | Frontend: DeepSeek | Media+Utils: ChatGPT | Engine: Claude)

Responsibility:
    Triggers on debug-related voice commands, automatically locates the most
    recently modified file in generated_code/, reads its contents, and delegates
    to CodingSwarm.debug_file() for AI-powered patching.
"""

import os
import glob

from codeskills.swarm import CodingSwarm


class DebuggerSkill:
    """
    Skill module that handles all code debugging commands for Cipher.
    Automatically targets the most recently modified file in generated_code/
    so the user doesn't have to specify which file to fix.
    """

    TRIGGER_PHRASES = [
        "debug this",
        "debug the code",
        "fix my code",
        "fix the code",
        "fix the bug",
        "fix the error",
        "why is this broken",
        "why is my code broken",
        "something is wrong with the code",
        "the code is broken",
        "code isn't working",
        "code is not working",
        "it's not working",
        "its not working",
        "not working",
        "there's an error",
        "there is an error",
        "got an error",
        "i have an error",
        "help me debug",
        "patch the code",
        "repair the code",
    ]

    # Where the swarm saves all generated files
    GENERATED_CODE_DIR = "generated_code"

    def __init__(self):
        """
        Initializes the DebuggerSkill and its CodingSwarm instance.
        The swarm is shared state — initialize once and reuse.
        """
        self.swarm = CodingSwarm()

    def _is_triggered(self, command: str) -> bool:
        command_lower = command.lower().strip()
        return any(phrase in command_lower for phrase in self.TRIGGER_PHRASES)

    def _extract_error_description(self, command: str) -> str:
        """
        Attempts to extract a meaningful error description from the command.
        Falls back to the full command if no clean extraction is possible.

        Examples:
            "debug this, the button isn't clicking"  → "the button isn't clicking"
            "fix my code"                            → "General bug fix requested"
        """
        command_stripped = command.strip()

        # Try to extract anything after a comma or colon
        for separator in [",", ":", " - ", " because ", " the error is ", " saying "]:
            if separator in command_stripped:
                parts = command_stripped.split(separator, 1)
                description = parts[1].strip()
                if len(description) > 5:
                    return description

        # If the full command IS a trigger phrase with no extra detail, use a default
        if command_stripped.lower() in [p.lower() for p in self.TRIGGER_PHRASES]:
            return "General bug fix requested by user."

        # Otherwise return the full command as context
        return command_stripped

    def _get_most_recent_file(self) -> str | None:
        """
        Scans the generated_code/ directory (recursively) and returns the
        filename (relative to generated_code/) of the most recently modified file.

        Returns:
            str | None: Relative filename like 'index.html' or 'portfolio/script.js',
                        or None if no files exist.
        """
        if not os.path.exists(self.GENERATED_CODE_DIR):
            return None

        # Recursively find all files in generated_code/
        all_files = glob.glob(
            os.path.join(self.GENERATED_CODE_DIR, "**", "*"),
            recursive=True,
        )

        # Filter to files only (exclude directories)
        all_files = [f for f in all_files if os.path.isfile(f)]

        if not all_files:
            return None

        # Sort by last-modified time, most recent first
        all_files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
        most_recent = all_files[0]

        # Return path relative to generated_code/ so swarm.debug_file() can find it
        relative = os.path.relpath(most_recent, self.GENERATED_CODE_DIR)
        return relative

    def execute(self, command: str) -> str | None:
        """
        Entry point called by the Cipher core engine.

        Workflow:
            1. Check trigger phrases.
            2. Extract error description from command.
            3. Find most recently modified file in generated_code/.
            4. Call swarm.debug_file() with the file and error description.
            5. Return the spoken confirmation message.

        Args:
            command (str): The voice/text command from the Cipher engine.

        Returns:
            str | None: Response string if triggered, None to pass to next skill.
        """
        if not self._is_triggered(command):
            return None

        # Find the most recent file to debug
        target_file = self._get_most_recent_file()

        if target_file is None:
            return (
                "Sir, I couldn't find any generated files to debug. "
                "Please ask me to build something first."
            )

        error_description = self._extract_error_description(command)

        print(f"\n>> [DebuggerSkill] Targeting: {target_file}")
        print(f">> [DebuggerSkill] Error description: {error_description}")

        try:
            result = self.swarm.debug_file(
                filename=target_file,
                error_description=error_description,
            )

            # result["message"] is the AI-generated spoken confirmation
            return result.get("message", f"Sir, I have patched {target_file}.")

        except Exception as e:
            return (
                f"Sir, I encountered an error while trying to debug {target_file}: {e}."
            )