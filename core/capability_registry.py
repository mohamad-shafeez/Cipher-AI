from typing import Dict, Any, Type

class CapabilityRegistry:
    """Central registry mapping cognitive intents to executable skill modules."""
    
    _capabilities: Dict[str, Any] = {}

    @classmethod
    def register_skill(cls, skill_instance: Any):
        """Allows a skill to self-register its capabilities into the OS."""
        if not hasattr(skill_instance, "capabilities"):
            print(f"⚠️ [REGISTRY ERROR]: {skill_instance.__class__.__name__} is missing 'capabilities' attribute.")
            return

        for intent in skill_instance.capabilities:
            cls._capabilities[intent] = skill_instance
            
        print(f"🔌 [REGISTRY]: Linked {skill_instance.__class__.__name__} -> {skill_instance.capabilities}")

    @classmethod
    def get_skill_for_intent(cls, intent: str) -> Any:
        """Dynamically resolves an intent to the correct skill module."""
        return cls._capabilities.get(intent)
        
    @classmethod
    def get_all_registered_intents(cls) -> list:
        return list(cls._capabilities.keys())
