import webbrowser
import re
import urllib.parse
from typing import Optional

class BrowserSkill:
    """
    Cipher Skill — Advanced Web Scout
    Handles direct URL navigation, vast alias resolution, and multi-engine searching.
    """
    def __init__(self):
        # Expanded alias dictionary for fast access
        self.sites = {
            "google": "https://www.google.com",
            "youtube": "https://www.youtube.com",
            "github": "https://www.github.com",
            "stackoverflow": "https://stackoverflow.com",
            "stack overflow": "https://stackoverflow.com",
            "gmail": "https://mail.google.com",
            "chatgpt": "https://chatgpt.com",
            "netflix": "https://www.netflix.com",
            "amazon": "https://www.amazon.com",
            "reddit": "https://www.reddit.com",
            "linkedin": "https://www.linkedin.com",
            "twitter": "https://twitter.com",
            "x": "https://x.com",
            "wikipedia": "https://www.wikipedia.org"
        }
        print(">> Web Scout Skill: ONLINE (Advanced Navigation & Search Active)")

    def execute(self, command: str) -> Optional[str]:
        if not command:
            return None
        
        cmd = command.lower().strip()

        # ── Route 1: Explicit Search Command ──
        # e.g., "search for python tutorials", "google how to bake a cake"
        search_match = re.search(r"^(?:search for|search|google|look up)\s+(.+)", cmd)
        if search_match:
            query = search_match.group(1).strip()
            return self._perform_search(query)

        # ── Route 2: Open / Launch Command ──
        # e.g., "open youtube", "launch github.com", "go to reddit"
        open_match = re.search(r"^(?:open|launch|go to|visit)\s+(.+)", cmd)
        if open_match:
            target = open_match.group(1).strip()
            return self._open_target(target)

        return None

    def _perform_search(self, query: str) -> str:
        """Executes a secure, URL-encoded Google search."""
        try:
            encoded_query = urllib.parse.quote_plus(query)
            url = f"https://www.google.com/search?q={encoded_query}"
            webbrowser.open(url)
            return f"Sir, I am searching the web for '{query}'."
        except Exception as e:
            print(f"[WebScout Error] {e}")
            return "Sir, I encountered an error while trying to search the web."

    def _open_target(self, target: str) -> str:
        """Resolves aliases or opens direct URLs."""
        try:
            # 1. Check if it's a known alias (e.g., "youtube")
            if target in self.sites:
                webbrowser.open(self.sites[target])
                return f"Opening {target.capitalize()}, Sir."

            # 2. Check if the user spoke a direct domain (e.g., "github.com")
            # Remove spaces in case speech recognition separated the dot (e.g. "github . com")
            compact_target = target.replace(" ", "")
            if re.search(r"\.[a-z]{2,}$", compact_target):
                # Ensure it has http/https protocol
                url = compact_target if compact_target.startswith("http") else f"https://{compact_target}"
                webbrowser.open(url)
                return f"Navigating directly to {compact_target}, Sir."

            # 3. Fallback: If it's not a known site and not a URL, default to a Google search
            return self._perform_search(target)

        except Exception as e:
            print(f"[WebScout Error] {e}")
            return f"Sir, I could not open {target}."