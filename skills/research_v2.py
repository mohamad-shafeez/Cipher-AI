"""
Cipher Skill — Research V2
Organ: The Deep Researcher
Architecture: Dual-Engine (Fast Wiki lookups + Deep Web Scraping via LLM Synthesis)
"""

import re
import time

# Deep Research Config (Optimized for 16GB RAM)
REQUEST_TIMEOUT = 8 
MAX_CHARS_PER_PAGE = 3500  # Increased since 16GB RAM allows for larger LLM context windows
MAX_URLS = 3               # Scrape the top 3 sites

class ResearchV2Skill:
    def __init__(self):
        print(">> Research V2 Skill: ONLINE (Dual-Engine Active)")

    def execute(self, command: str) -> str | None:
        if not command:
            return None
            
        cmd = command.lower().strip()

        # ---------------------------------------------------------
        # ROUTE 1: THE DEEP PATH (Live Web Scrape + LLM Synthesis)
        # ---------------------------------------------------------
        deep_triggers = ["deep research", "investigate", "search the web for", "deep search", "web research"]
        for t in deep_triggers:
            if cmd.startswith(t):
                query = cmd.replace(t, "").strip()
                if not query:
                    return "Sir, please specify a topic for deep research."
                return self._run_deep_research(query)

        # ---------------------------------------------------------
        # ROUTE 2: THE FAST PATH (Wikipedia Fact Retrieval)
        # ---------------------------------------------------------
        wiki_triggers = ["who is", "tell me about", "wikipedia", "what is a", "what is an"]
        is_wiki = any(phrase in cmd for phrase in wiki_triggers)
        
        # User's brilliant exception logic to avoid overriding system commands
        if "what is" in cmd and not any(x in cmd for x in ["time", "date", "battery", "cpu", "ram", "memory", "my screen"]):
            is_wiki = True

        if is_wiki:
            query = cmd
            for phrase in wiki_triggers + ["what is"]:
                query = query.replace(phrase, "")
            query = query.replace("?", "").strip()
            
            if query:
                return self._run_wiki_research(query)

        return None

    # =========================================================
    # FAST PATH LOGIC (Wikipedia)
    # =========================================================
    def _run_wiki_research(self, query: str) -> str:
        try:
            import wikipedia
            wikipedia.set_lang("en")
            
            print(f">> [Research: Fast Path] Querying Wiki archives for: {query}")
            summary = wikipedia.summary(query, sentences=3)
            return f"Sir, according to the archives: {summary}"
            
        except ImportError:
            return "Sir, Wikipedia module is missing. Run: pip install wikipedia"
        except Exception as e:
            # Fallback to Deep Research if Wikipedia fails or requires disambiguation
            print(f">> [Research: Wiki Failed] Falling back to Deep Web Search...")
            return self._run_deep_research(query)

    # =========================================================
    # DEEP PATH LOGIC (Web Scrape -> TurboBrain LLM)
    # =========================================================
    def _run_deep_research(self, query: str) -> str:
        print(f">> [Research: Deep Path] Initializing web scrape for: {query}")
        
        # 1. Search DDG
        urls = self._ddg_search(query)
        if not urls:
            return f"Sir, I could not find any live web results for '{query}'."

        # 2. Scrape Sites
        scraped_chunks = []
        for url in urls[:MAX_URLS]:
            text = self._scrape_url(url)
            if text:
                scraped_chunks.append(f"[Source: {url}]\n{text}")

        if not scraped_chunks:
            return "Sir, I located URLs but firewalls prevented me from extracting the text."

        combined_text = "\n\n".join(scraped_chunks)
        print(f">> [Research: Deep Path] Successfully extracted {len(combined_text)} characters. Feeding to TurboBrain...")

        # 3. Synthesize via LLM
        return self._synthesize(query, combined_text)

    def _ddg_search(self, query: str) -> list[str]:
        try:
            from duckduckgo_search import DDGS
            urls = []
            with DDGS() as ddgs:
                results = ddgs.text(query, max_results=MAX_URLS + 2)
                for r in results:
                    href = r.get("href") or r.get("url", "")
                    if href and href.startswith("http"):
                        urls.append(href)
                    if len(urls) >= MAX_URLS:
                        break
            return urls
        except Exception as e:
            print(f"[DDG Error] {e}")
            return []

    def _scrape_url(self, url: str) -> str | None:
        try:
            import requests
            from bs4 import BeautifulSoup
            
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()

            paragraphs = soup.find_all("p")
            text = " ".join(p.get_text(separator=" ", strip=True) for p in paragraphs)
            text = re.sub(r'\s+', ' ', text).strip()
            
            return text[:MAX_CHARS_PER_PAGE] if text else None
        except Exception:
            return None

    def _synthesize(self, query: str, scraped_text: str) -> str:
        try:
            from skills.turbo_brain import turbo_think
            
            prompt = (
                f"You are Cipher, an advanced AI. Analyze the following live web data to answer the user's query.\n"
                f"Query: '{query}'\n\n"
                f"Web Data:\n{scraped_text}\n\n"
                f"Synthesize a factual, concise, and highly intelligent answer. Do not use filler words."
            )
            
            result = turbo_think(prompt)
            return result if result else "Sir, I scraped the data but the neural brain failed to synthesize a response."
            
        except Exception as e:
            return f"Sir, synthesis failed: {e}"