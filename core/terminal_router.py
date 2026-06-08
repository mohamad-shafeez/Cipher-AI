import subprocess
import os

class TerminalRouter:
    # 🛡️ THE SECURITY GUARDIAN SHIELD
    # Instantly intercepts and blocks commands that pose a structural threat to your operating system
    FORBIDDEN_KEYWORDS = [
        "rmdir /s", "del /f", "format", "mkfs", "shutdown", 
        "drop database", "registry delete", "os.remove"
    ]

    @classmethod
    def execute_command(cls, command_str: str, working_dir: str = "D:/Visual Studio/Cipher-AI") -> dict:
        result = {"success": False, "output": "", "error": ""}
        cmd_lower = command_str.lower()

        # Check for safety violations
        if any(forbidden in cmd_lower for forbidden in cls.FORBIDDEN_KEYWORDS):
            result["error"] = "🛡️ [SECURITY VIOLATION]: Command aborted. Subprocess violates native protection guardrails."
            print(f"🛑 {result['error']} Blocked payload: '{command_str}'")
            return result

        try:
            print(f"🖥️ [AUTONOMOUS CLI]: Executing command sequence: '{command_str}'...")
            
            # Spawn a controlled background terminal shell pipeline
            process = subprocess.run(
                command_str,
                shell=True,
                cwd=working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30  # Hard deadline to prevent shell hangs
            )

            result["output"] = process.stdout.strip()
            result["error"] = process.stderr.strip()
            result["success"] = (process.returncode == 0)

            if not result["success"] and result["error"]:
                print(f"⚠️ [CLI STDERR TRACE]: {result['error']}")

        except subprocess.TimeoutExpired:
            result["error"] = "TimeoutError: System execution limits exceeded 30-second constraint window."
            print(f"❌ [CLI CRITICAL]: {result['error']}")
        except Exception as e:
            result["error"] = f"Ecosystem shell exception: {str(e)}"
            print(f"❌ [CLI CRASH]: {result['error']}")

        return result
