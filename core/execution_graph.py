from dataclasses import dataclass
from typing import List, Dict, Any
from core.capability_registry import CapabilityRegistry
from core.hud_server import HUDServer

@dataclass
class ExecutionStep:
    step_id: int
    intent: str
    payload: Dict[str, Any]
    status: str = "pending"  # pending, running, success, failed

class ExecutionGraph:
    """Manages multi-step autonomous workflows."""
    
    def __init__(self, steps_data: List[Dict[str, Any]]):
        self.steps = [
            ExecutionStep(
                step_id=idx + 1,
                intent=step.get("intent", "unknown"),
                payload=step
            ) for idx, step in enumerate(steps_data)
        ]

    def execute_all(self) -> bool:
        """Iterates through the DAG (Directed Acyclic Graph) of tasks."""
        total_steps = len(self.steps)
        HUDServer.push_log(f"🔗 GRAPH: Initializing {total_steps}-step execution sequence...")
        print(f"🔗 [EXECUTION GRAPH]: {total_steps} sequential operations loaded.")

        for step in self.steps:
            step.status = "running"
            print(f"⏳ [GRAPH]: Executing Step {step.step_id}/{total_steps} -> Intent: '{step.intent}'")
            
            # 1. Resolve the capability dynamically
            skill = CapabilityRegistry.get_skill_for_intent(step.intent)
            
            if not skill:
                print(f"🛑 [GRAPH ERROR]: Unregistered capability '{step.intent}'. Graph aborted.")
                HUDServer.push_log(f"🛑 GRAPH HALT: Missing capability '{step.intent}'.")
                step.status = "failed"
                return False

            # 2. Execute the skill using the universal interface
            try:
                # Every registered skill implements the execute(payload: dict) interface
                success = skill.execute(step.payload)
                if not success:
                    print(f"🛑 [GRAPH ERROR]: Step {step.step_id} failed execution. Graph aborted.")
                    step.status = "failed"
                    return False
                
                step.status = "success"
                from core.event_bus import EventBus, Event
                EventBus().publish(Event(
                    type="graph.step.success",
                    source="ExecutionGraph",
                    data={"intent": step.intent, "payload": step.payload}
                ))
                print(f"✅ [GRAPH]: Step {step.step_id} completed.")
                
            except Exception as e:
                print(f"💥 [GRAPH CRASH]: Fatal error in Step {step.step_id} -> {str(e)}")
                step.status = "failed"
                return False

        print("✨ [EXECUTION GRAPH]: All sequential operations completed successfully.")
        HUDServer.push_log("✨ GRAPH: Execution sequence complete.")
        return True
