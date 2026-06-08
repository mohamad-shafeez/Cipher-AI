# core/state_manager.py
import threading
import psutil

class StateManager:
    _lock = threading.Lock()
    _state = {
        "current_agent": "Idle",
        "last_transcript": "No command captured yet.",
        "system_status": "Online",
        "memory_retrievals": [],
        "reflection_logs": [],
        "cpu_usage": 0.0,
        "ram_usage": 0.0,
        "background_tasks_running": False
    }

    @classmethod
    def get_state(cls):
        with cls._lock:
            # Dynamically update CPU and RAM metrics
            try:
                cls._state["cpu_usage"] = psutil.cpu_percent(interval=0)
                cls._state["ram_usage"] = psutil.virtual_memory().percent
            except Exception:
                pass
            return cls._state.copy()

    @classmethod
    def get_all_states(cls):
        return cls.get_state()

    @classmethod
    def update_state(cls, key, value):
        with cls._lock:
            if key in cls._state:
                if key == "reflection_logs" or key == "memory_retrievals":
                    if isinstance(value, list):
                        cls._state[key] = value
                    else:
                        cls._state[key].append(value)
                        # Keep only last 20 logs to prevent memory bloat
                        cls._state[key] = cls._state[key][-20:]
                else:
                    cls._state[key] = value

    @classmethod
    def set_agent(cls, agent_name):
        cls.update_state("current_agent", agent_name)

    @classmethod
    def set_transcript(cls, transcript):
        cls.update_state("last_transcript", transcript)

    @classmethod
    def set_status(cls, status):
        cls.update_state("system_status", status)

    @classmethod
    def add_reflection_log(cls, log):
        cls.update_state("reflection_logs", log)

    @classmethod
    def add_log(cls, log):
        cls.update_state("reflection_logs", log)

    @classmethod
    def add_memory_retrieval(cls, retrieval):
        cls.update_state("memory_retrievals", retrieval)
