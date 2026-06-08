from core.hud_server import HUDServer
from core.worker_manager import crash_shield

def run_vision_analysis(query: str):
    """Module-level pickleable function to run in the isolated Process Pool."""
    from core.vision_engine import VisionEngine
    from core.speak import speak
    import os
    
    print(f"👁️ [VISION WORKER PID {os.getpid()}]: Starting visual context analysis...")
    engine = VisionEngine()
    analysis = engine.analyze_screen(query)
    
    # Speak the result out loud to the user
    speak(analysis)
    return analysis

class VisionSkill:
    def __init__(self):
        # The Orchestrator will route intents here
        self.capabilities = ["system.vision_analyze"]

    @crash_shield
    def execute(self, payload: dict) -> bool:
        query = payload.get("query")
        
        if not query or query.lower() in ["none", "null", ""]:
            query = "Analyze the screen and tell me what the user is currently looking at."
            
        from core.worker_manager import WorkerManager
        # Offload screenshot capturing and Moondream HTTP POST to the Process Pool
        WorkerManager.submit_task(run_vision_analysis, query)
        
        return True
