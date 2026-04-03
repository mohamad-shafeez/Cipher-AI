import os
import json
import requests
from datetime import datetime

class KnowledgeForgeSkill:
    def __init__(self):
        self.knowledge_dir = "cipher_knowledge"
        os.makedirs(self.knowledge_dir, exist_ok=True)
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model = "phi3.5"  # Using your NLP model for summarization
        print(">> Knowledge Forge Skill: ONLINE (Self-Learning Active)")

    def _search_archives(self, query: str) -> str | None:
        results = []
        for fname in os.listdir(self.knowledge_dir):
            if fname.endswith(".json"):
                try:
                    with open(os.path.join(self.knowledge_dir, fname), "r", encoding="utf-8") as f:
                        data = json.load(f)
                    topic = data.get("topic", "")
                    content = data.get("content", "")
                    
                    if query in topic.lower() or query in content.lower():
                        results.append(f"Regarding {topic}: {content}")
                except Exception:
                    continue
                    
        if results:
            return "Sir, based on my forged archives: " + " ".join(results[:2]) # Keep it brief for voice
        return None

    def _start_interview(self) -> str:
        print("\n" + "="*40)
        print(">> [TERMINAL OVERRIDE] INTERVIEW MODE ENGAGED")
        print(">> Microphone paused. Please use the keyboard.")
        print("="*40)
        
        topic = input(">> What topic are you teaching me? : ").strip()
        if not topic:
            return "Sir, interview aborted. No topic provided."
            
        print(f">> Understood. Please explain '{topic}':")
        explanation = input(">> ").strip()

        if not explanation:
            return "Sir, interview aborted. No explanation provided."

        print(">> [KnowledgeForge] Summarizing and forging memory...")

        # Summarize with LLM
        prompt = (
            f"Summarize the following explanation into a concise, factual knowledge snippet "
            f"in 2 to 3 sentences. Do not use conversational filler.\n\n"
            f"Topic: {topic}\nExplanation: {explanation}"
        )
        
        try:
            resp = requests.post(self.ollama_url, json={
                "model": self.model, "prompt": prompt, "stream": False
            }, timeout=30)
            summary = resp.json().get("response", explanation).strip()
        except Exception as e:
            print(f"[KnowledgeForge Error] LLM timeout: {e}")
            summary = explanation # Fallback to raw text if LLM fails

        # Save to cipher_knowledge/
        filename = f"{topic.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.knowledge_dir, filename)
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump({
                    "topic": topic,
                    "raw_input": explanation,
                    "content": summary,
                    "timestamp": datetime.now().isoformat()
                }, f, indent=4)
            return f"Sir, the knowledge regarding '{topic}' has been permanently forged into my archives. I am now smarter."
        except Exception as e:
            return f"Sir, I failed to write the knowledge to the disk: {e}"

    def execute(self, command: str) -> str | None:
        try:
            if not command: return None
            cmd = command.lower().strip()

            # --- TRIGGER 1: SEARCH FORGE ---
            search_match = [t for t in ["check archives for ", "search knowledge for "] if t in cmd]
            if search_match:
                query = cmd.split(search_match[0])[-1].strip()
                print(f">> [KnowledgeForge] Searching archives for: {query}")
                res = self._search_archives(query)
                return res if res else f"Sir, I have no forged records concerning '{query}'."

            # --- TRIGGER 2: TEACH CIPHER ---
            if any(t in cmd for t in ["teach cipher", "interview mode", "learn something new"]):
                return self._start_interview()

            return None

        except Exception as e:
            print(f"[KnowledgeForge Error] {e}")
            return None