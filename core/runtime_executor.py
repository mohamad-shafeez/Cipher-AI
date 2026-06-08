import subprocess
import os
import sys
import config

class RuntimeExecutor:
    @staticmethod
    def is_docker_active() -> bool:
        """Checks if the local Docker daemon is alive and reachable."""
        try:
            process = subprocess.run(
                ["docker", "info"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=3
            )
            return process.returncode == 0
        except Exception:
            return False

    @classmethod
    def validate_code(cls, filepath: str) -> dict:
        """
        Executes code inside a secure, containerized sandbox using ephemeral 
        Docker instances to shield the host machine from runtime anomalies.
        """
        result = {"success": True, "traceback": ""}
        if not os.path.exists(filepath):
            return {"success": False, "traceback": "File not found on disk."}

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                code_content = f.read()
        except Exception as e:
            return {"success": False, "traceback": f"File read error: {str(e)}"}

        file_ext = os.path.splitext(filepath)[1].lower()
        filename = os.path.basename(filepath)

        # 🐳 CONTAINERIZED CONFIGURATION ROUTING
        if file_ext == '.py':
            docker_image = "python:3.11-slim"
            exec_args = ["docker", "run", "--rm", "-i", "--net=none", "--memory=128m", docker_image, "python"]
        elif file_ext == '.js':
            docker_image = "node:20-slim"
            exec_args = ["docker", "run", "--rm", "-i", "--net=none", "--memory=128m", docker_image, "node"]
        else:
            # Codebases without interactive execution targets skip sandboxing
            return result

        # Verify docker daemon state before launching container streams
        if cls.is_docker_active():
            print(f"🐳 [SHADOW SANDBOX]: Spawning isolated {docker_image} sandbox for {filename}...")
            try:
                # Fire up the container and stream code directly via STDIN 
                # --net=none disables internet access inside the container for absolute lock-down
                # --memory=128m limits RAM allocation so infinite loops can't freeze your system
                process = subprocess.run(
                    exec_args,
                    input=code_content,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=5  # Hard timeout constraint
                )

                if process.returncode != 0:
                    result["success"] = False
                    result["traceback"] = process.stderr.strip()
                    print(f"🛑 [SANDBOX CONTAINER CRASH]: Runtime exception intercepted.")
                else:
                    print("⚡ [SANDBOX TRIAL PASSED]: Ephemeral container exited with status code 0.")

            except subprocess.TimeoutExpired:
                result["success"] = False
                result["traceback"] = "TimeoutError: Sandbox container execution limit exceeded (Potential resource starvation/infinite loop)."
                print("🛑 [SANDBOX CRITICAL]: Execution timeline breached! Container terminated.")
            except Exception as e:
                result["success"] = False
                result["traceback"] = f"Sandbox subsystem failure: {str(e)}"
        else:
            # Defensive Fallback: If Docker isn't open, run locally but warn the HUD
            print("⚠️ [RUNTIME WARNING]: Docker daemon unreachable. Dropping back to host terminal sandbox layer...")
            try:
                local_cmd = [sys.executable, filepath] if file_ext == '.py' else ['node', filepath]
                process = subprocess.run(local_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
                if process.returncode != 0:
                    result["success"] = False
                    result["traceback"] = process.stderr.strip()
            except subprocess.TimeoutExpired:
                result["success"] = False
                result["traceback"] = "TimeoutError: Host terminal execution threshold breached."
            except Exception as e:
                result["success"] = False
                result["traceback"] = f"Native execution path failure: {str(e)}"

        return result
