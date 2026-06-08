from core.cognitive_memory import CognitiveMemory
from core.worker_manager import crash_shield
import os

class SwarmSkill:
    def __init__(self):
        # This intent tells the Orchestrator to hand complex goals to the Swarm
        self.capabilities = ["autonomous.solve"]

    @crash_shield
    def execute(self, payload: dict) -> bool:
        # If payload has transcript (from main.py), use it as goal
        goal = payload.get("transcript", payload.get("query", "Unknown Goal"))

        # 1. DYNAMIC FILE PATH RESOLUTION
        # First, check if main.py extracted the filename from voice command
        target_file_path = payload.get("target_file")

        # If not provided, try to grab from active_context
        if not target_file_path:
            active_context = payload.get("active_context", {})
            target_file_path = active_context.get("file_path")

        # If still not found, fallback to dir from main.py
        if not target_file_path:
            target_file_path = payload.get("dir")

        # Last resort: use test.py as safe placeholder
        if not target_file_path:
            target_file_path = "D:/Visual Studio/Cipher-AI/generated_code/test.py"

        print(f"🚀 [SOVEREIGN TARGET]: File pipeline locked onto -> '{target_file_path}'")

        # 2. USE DIRECT CODE GENERATION SKILL (bypasses complex swarm)
        from core.code_generation_skill import CodeGenerationSkill
        skill = CodeGenerationSkill()

        # Extract just the command part (voice intent)
        user_command = goal if goal else payload.get("transcript", "")

        result = skill.execute({
            "command": user_command,
            "target_file": target_file_path
        })

        return bool(result)
