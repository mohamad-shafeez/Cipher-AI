from typing import Dict, Any, List
from core.llm_interface import LocalLLM, ModelSelector
from core.hud_server import HUDServer
from core.event_bus import EventBus, Event
from core.cognitive_memory import CognitiveMemory

import config
import os

class BaseAgent:
    """The foundational class for all specialized swarm workers."""
    def __init__(self, name: str, system_prompt: str, model: str = None):
        self.name = name
        self.system_prompt = system_prompt
        self.model = model if model else ModelSelector.get_model("coding")

    def execute(self, context: str) -> str:
        HUDServer.set_agent(self.name)
        print(f"🤖 [{self.name.upper()}]: Analyzing context...")
        response = LocalLLM.generate(self.system_prompt, context, model=self.model)
        return response

class SwarmManager:
    """Orchestrates autonomous multi-agent problem solving."""
    
    def __init__(self):
        # Initialize our specialized workforce
        self.agents = {
            "planner": BaseAgent(
                name="Heavy Planner", 
                system_prompt="You are the Swarm Planner. Break the user's abstract goal into 3 strict, logical coding steps. Output nothing but the steps."
            ),
            "coder": BaseAgent(
                name="Turbo Brain", 
                system_prompt="You are the Swarm Coder. Write exactly the code requested by the planner. No markdown, no explanations. Just raw code."
            ),
            "verifier": BaseAgent(
                name="CodeAnalyst", 
                system_prompt="You are the Swarm Verifier. Look at the code. If it has syntax errors, reply 'FAIL: [reason]'. If it looks perfect, reply 'PASS'."
            )
        }

    def delegate_goal(self, goal: str, active_context: str) -> bool:
        """The autonomous loop: Plan -> Code -> Verify -> (Retry) -> Success"""
        print(f"🌪️ [SWARM MANAGER]: Initiating autonomous swarm for goal: '{goal}'")
        HUDServer.push_log(f"🌪️ SWARM: Autonomous goal execution started.")

        # 0. PATH CORRECTION: If path is just a folder, append the fallback filename
        target_file = active_context
        if target_file.endswith("generated_code") or target_file.endswith("generated_code/"):
            target_file = os.path.join(target_file, "test.py").replace("\\", "/")
            print(f"🛠️ [PATH CORRECTION]: Folder path detected. Appending fallback target: {target_file}")

        # 1. Read file to enable intelligent model routing
        file_content = ""
        try:
            if os.path.isfile(target_file):
                with open(target_file, 'r', encoding='utf-8') as f:
                    file_content = f.read()
        except Exception as e:
            print(f"⚠️ [FILE READ]: Could not read {target_file}: {e}")

        # 2. Intelligent model selection based on task complexity
        chosen_model = ModelSelector.classify_task(file_content, goal)

        # 3. FORCE HOT-SWAP THE GLOBAL CONFIG OBJECT
        original_heavy = getattr(config, "HEAVY_MODEL", "qwen2.5-coder:7b")
        config.HEAVY_MODEL = str(chosen_model)
        print(f"🔥 [CONFIG HOT-SWAP]: Global HEAVY_MODEL overridden from {original_heavy} to {chosen_model}")

        # 4. COMPLETE OVERRIDE: Re-create agents with CHOSEN model (forced string conversion)
        self.agents["planner"] = BaseAgent(
            name="Heavy Planner",
            system_prompt="You are the Swarm Planner. Break the user's abstract goal into 3 strict, logical coding steps. Output nothing but the steps.",
            model=str(chosen_model)
        )
        self.agents["coder"] = BaseAgent(
            name="Turbo Brain",
            system_prompt="You are the Swarm Coder. Write exactly the code requested by the planner. No markdown, no explanations. Just raw code.",
            model=str(chosen_model)
        )
        self.agents["verifier"] = BaseAgent(
            name="CodeAnalyst",
            system_prompt="You are the Swarm Verifier. Look at the code. If it has syntax errors, reply 'FAIL: [reason]'. If it looks perfect, reply 'PASS'.",
            model=str(chosen_model)
        )

        # 5. DOUBLE-CHECK OVERRIDE: Manually set model on each agent to be absolutely sure
        self.agents["planner"].model = chosen_model
        self.agents["coder"].model = chosen_model
        self.agents["verifier"].model = chosen_model

        # Also set as attributes for backup access
        self.planner = self.agents["planner"]
        self.coder = self.agents["coder"]
        self.verifier = self.agents["verifier"]

        print(f"🚀 [SWARM BLITZ]: All agents locked onto {chosen_model} for high-speed execution.")

        # 6. VERIFICATION: Confirm models before execution
        print(f"✅ [VERIFY PLANNER]: Using model={self.agents['planner'].model}")
        print(f"✅ [VERIFY CODER]: Using model={self.agents['coder'].model}")
        print(f"✅ [VERIFY VERIFIER]: Using model={self.agents['verifier'].model}")
        print(f"✅ [CONFIG CHECK]: config.HEAVY_MODEL now reads {config.HEAVY_MODEL}")

        # 7. PLAN
        plan = self.agents["planner"].execute(f"Goal: {goal}\nContext: {target_file}")
        print(f"📋 [SWARM PLANNER]:\n{plan}")

        # We will limit the swarm to 3 retry loops to prevent infinite hallucinations
        max_retries = 3
        current_attempt = 1
        current_code = ""

        while current_attempt <= max_retries:
            print(f"🔄 [SWARM LOOP]: Attempt {current_attempt}/{max_retries}")

            # 8. CODE
            current_code = self.agents["coder"].execute(f"Plan: {plan}\nPrevious Code (if any): {current_code}")

            # 9. VERIFY
            verification = self.agents["verifier"].execute(f"Code to verify:\n{current_code}")
            print(f"🔍 [SWARM VERIFIER]: {verification}")

            if "PASS" in verification.upper():
                print("✨ [SWARM MANAGER]: Swarm reached consensus! Goal achieved.")
                EventBus().publish(Event(type="swarm.consensus.reached", source="SwarmManager", data={"code": current_code}))
                return current_code

            print("⚠️ [SWARM MANAGER]: Verifier rejected the code. Sending back to Coder...")
            current_attempt += 1

        print("🛑 [SWARM FATAL]: Swarm failed to reach consensus after maximum retries.")
        return False
