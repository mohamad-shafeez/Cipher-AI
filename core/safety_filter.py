"""
Safety Filter & Guardrails Layer

Enforces content policies at runtime to prevent unsafe model outputs.
Integrated into LocalLLM.generate() for all inference calls.
"""
import re
from typing import Dict, Tuple

class SafetyFilter:
    """Runtime response filtering and safety enforcement."""
    
    # Patterns for unsafe content detection
    UNSAFE_PATTERNS = {
        "jailbreak": [
            r"ignore.*instruction",
            r"pretend.*previous",
            r"forget.*all",
            r"act.*as.*unrestricted",
            r"DAN\s*:",
            r"GPT-J\s*:",
            r"bypass.*filter",
            r"disable.*safety"
        ],
        "violent": [
            r"kill\s+\w+\s+(with|by)",
            r"how.*to.*harm",
            r"make.*weapon",
            r"assassination.*guide",
            r"torture.*method",
            r"bomb.*recipe"
        ],
        "toxic": [
            r"nigger|faggot|retard",  # Slurs (minimal)
            r"hate.*\w+\s+(people|group)",
            r"eliminate.*ethnicit",
            r"genocide.*plan"
        ],
        "illegal": [
            r"how.*to.*hack.*\w+",
            r"crack.*password",
            r"bypass.*authentication",
            r"steal.*data",
            r"forge.*document",
            r"launder.*money"
        ],
        "sexual": [
            r"child.*sexual",
            r"minor.*explicit",
            r"non-consensual.*sexual"
        ]
    }
    
    # Safe response templates
    SAFE_RESPONSES = {
        "jailbreak": "I can't help with that request. I'm designed to follow my guidelines consistently.",
        "violent": "I can't provide guidance on causing harm to people or property.",
        "toxic": "I can't engage with hateful or discriminatory content.",
        "illegal": "I can't provide assistance with illegal activities.",
        "sexual": "I can't provide sexual content involving minors or non-consent."
    }

    @staticmethod
    def filter_response(response: str) -> Tuple[str, Dict[str, bool]]:
        """
        Filters a model response for unsafe content.
        
        Returns:
            (filtered_response, flagged_categories)
        """
        if not response:
            return response, {}
        
        flagged = {}
        response_lower = response.lower()
        
        # Check each unsafe category
        for category, patterns in SafetyFilter.UNSAFE_PATTERNS.items():
            is_unsafe = any(re.search(pattern, response_lower, re.IGNORECASE) for pattern in patterns)
            
            if is_unsafe:
                flagged[category] = True
                # Return safe response for this category
                return SafetyFilter.SAFE_RESPONSES[category], flagged
        
        # No unsafe patterns detected
        return response, flagged
    
    @staticmethod
    def filter_prompt(prompt: str) -> Tuple[str, bool]:
        """
        Detects and flags prompt injection attempts.
        
        Returns:
            (cleaned_prompt, is_injection_attempt)
        """
        if not prompt:
            return prompt, False
        
        injection_patterns = [
            r"ignore.*instruction",
            r"new.*instruction",
            r"override.*system",
            r"forget.*context",
            r"disregard.*previous",
            r"\[NEW SYSTEM PROMPT\]",
            r"SYSTEM OVERRIDE"
        ]
        
        is_injection = any(re.search(pattern, prompt, re.IGNORECASE) for pattern in injection_patterns)
        
        return prompt, is_injection
    
    @staticmethod
    def enforce_length_limit(response: str, max_tokens: int = 2000) -> str:
        """Enforces maximum response length (approximate token count)."""
        # Rough token estimate: ~4 characters per token
        max_chars = max_tokens * 4
        
        if len(response) > max_chars:
            # Truncate and add continuation marker
            return response[:max_chars] + "\n\n[Response truncated due to length limit]"
        
        return response
    
    @staticmethod
    def check_rate_limit(user_id: str, calls_per_minute: int = 20) -> bool:
        """
        Simple rate limiting check (per-user).
        Would need Redis/cache in production.
        For now, returns True (not rate-limited).
        """
        # TODO: Implement with Redis or in-memory cache
        return True
    
    @staticmethod
    def get_safety_report(flagged: Dict[str, bool]) -> str:
        """Generates a human-readable safety report."""
        if not flagged:
            return "[SAFETY] No issues detected ✓"
        
        issues = ", ".join(flagged.keys())
        return f"[SAFETY] Flagged categories: {issues} ⚠️"
