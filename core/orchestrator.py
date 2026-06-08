import json
import winsound
from core.hud_server import HUDServer
from core.llm_interface import LocalLLM
from core.execution_graph import ExecutionGraph
from core.capability_registry import CapabilityRegistry

class MasterOrchestrator:
    @classmethod
    def parse_intent(cls, transcript: str) -> list:
        """
        Forces the local LLM to act as a strict NLP parser returning a list of tasks.
        Converts human speech into a machine-readable JSON array of intent schemas.
        """
        HUDServer.set_agent("Heavy Planner")
        print(f"🧠 [ORCHESTRATOR]: Parsing cognitive intent array for -> '{transcript}'")
        
        system_prompt = """
        You are the Intent Parsing Engine for an OS-level AI daemon.
        Analyze the user's command and output a JSON ARRAY of execution steps.
        Break multi-part commands into sequential tasks.
        Do not include markdown formatting or explanations. Output ONLY JSON.
        
        Schema requirements (Must be a JSON Array/List of Objects):
        [
          {
            "intent": "media.play" | "app.launch" | "system.search" | "code.generate" | "temporal.schedule" | "conversation" | "autonomous.solve" | "system.vision_analyze",
            "device": "desktop" | "mobile" | "local",
            "application": "target app name or null",
            "query": "specific search terms, code requirements, scheduling, conversational prompt, complex autonomous goal, or vision query or null"
          }
        ]
        
        Examples:
        - "open spotify and play interstellar soundtrack"
          [
            {"intent": "media.play", "device": "desktop", "application": "spotify", "query": "interstellar soundtrack"}
          ]
        - "open spotify, then remind me in 10 minutes to grab a coffee"
          [
            {"intent": "app.launch", "device": "desktop", "application": "spotify", "query": null},
            {"intent": "temporal.schedule", "device": "local", "application": null, "query": "remind me in 10 minutes to grab a coffee"}
          ]
        - "who are you?"
          [
            {"intent": "conversation", "device": "local", "application": null, "query": "who are you?"}
          ]
        - "fix the memory leak in my server.py file"
          [
            {"intent": "autonomous.solve", "device": "local", "application": null, "query": "fix the memory leak in my server.py file"}
          ]
        - "look at my screen and tell me what is wrong with this code"
          [
            {"intent": "system.vision_analyze", "device": "local", "application": null, "query": "tell me what is wrong with this code"}
          ]
        """
        
        raw_json_response = LocalLLM.generate(system_prompt, transcript)
        
        # Clean markdown code block decorators if model returns them
        cleaned_response = raw_json_response.strip()
        if cleaned_response.startswith("```"):
            lines = cleaned_response.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned_response = "\n".join(lines).strip()
            
        try:
            intent_data = json.loads(cleaned_response)
            if isinstance(intent_data, dict):
                intent_data = [intent_data] # Force single dict into a list wrapper
            return intent_data
        except json.JSONDecodeError:
            print(f"⚠️ [ORCHESTRATOR]: Model failed to output strict JSON array. Raw: '{raw_json_response}'")
            # Heuristic keyword fallback if LLM returned bad format
            intent_lower = transcript.lower()
            
            # Check for temporal triggers
            if any(k in intent_lower for k in ["remind", "schedule", "alarm", "watch for", "every"]):
                return [{
                    "intent": "temporal.schedule",
                    "device": "local",
                    "application": None,
                    "query": transcript
                }]
                
            system_triggers = ["open", "launch", "start", "play"]
            if any(t in intent_lower for t in system_triggers):
                # Infer app name
                app_name = None
                for key in ["instagram", "youtube", "github", "chatgpt", "chrome", "google", "notepad", "calculator", "spotify", "vs code", "discord"]:
                    if key in intent_lower:
                        app_name = key
                        break
                return [{
                    "intent": "media.play" if "play" in intent_lower else "app.launch",
                    "device": "local",
                    "application": app_name,
                    "query": transcript
                }]
            return [{
                "intent": "conversation",
                "device": "local",
                "application": None,
                "query": transcript
            }]

    @classmethod
    def route_command(cls, transcript: str, active_directory: str) -> bool:
        """
        The central nervous system. Parses the intent, plans the execution, 
        and routes to the sequential Execution Graph.
        Maintains memory of interactions for future context injection.
        """
        text = transcript.lower().strip()
        
        # ⚡ Deterministic Shortcut for all configured applications/websites in our matrix
        try:
            from skills.system_operator_skill import SystemOperatorSkill
            operator = SystemOperatorSkill()
            for app_name in operator.app_matrix.keys():
                if ("open" in text or "launch" in text or "start" in text or "play" in text) and app_name in text:
                    print(f"⚡ [DETERMINISTIC ROUTING]: Bypassing LLM planner for fast app launch -> '{app_name}'")
                    HUDServer.push_log(f"⚡ FAST ROUTE: Bypassing LLM planner for '{app_name}' launch.")
                    
                    query = None
                    for trigger in ["search for", "search", "play"]:
                        if trigger in text:
                            parts = text.split(trigger)
                            if len(parts) > 1:
                                query = parts[1].strip()
                                break
                                
                    result = operator.execute({"application": app_name, "query": query})
                    cls._log_interaction(transcript, app_name, "Fast route executed")
                    return result
        except Exception as fast_route_err:
            print(f"⚠️ [FAST ROUTING ERROR]: {fast_route_err}. Falling back to standard LLM route...")

        HUDServer.push_log("🧠 ORCHESTRATOR: Engaging central planner...")
        
        # 1. Parse human speech into a List of machine intents
        execution_steps = cls.parse_intent(transcript)
        print(f"📋 [INTENT GRAPH PAYLOAD]:\n{json.dumps(execution_steps, indent=2)}")
        HUDServer.push_log(f"📋 GRAPH RECEIVED: {len(execution_steps)} execution steps.")
        
        # 2. Feed the steps into the Graph Engine
        graph = ExecutionGraph(execution_steps)
        result = graph.execute_all()
        
        # 3. Log interaction to memory for future context
        if execution_steps:
            primary_intent = execution_steps[0].get("intent", "unknown")
            cls._log_interaction(transcript, primary_intent, "Graph execution completed")
        
        return result
    
    @staticmethod
    def _log_interaction(user_input: str, executed_skill: str, summary: str):
        """Persist interaction to memory systems for future context injection."""
        try:
            from core.memory_sql import MemorySQL
            mem_sql = MemorySQL()
            mem_sql.add_log(user_input, executed_skill, summary)
        except Exception as e:
            print(f"⚠️ [ORCHESTRATOR]: Failed to log interaction: {e}")
