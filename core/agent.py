# core/agent.py
# ============================================================
#   CIPHER AGENT CORE — Multi-Step Planner & Executor
#   Ghost OS Level 5 Edition
# ============================================================

import json
import time
import requests
import re
from datetime import datetime
import config

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL      = config.LLM_MODEL   # <--- The corrected config link

PLAN_PROMPT = """You are Cipher's internal task orchestrator. 
Break the user's request into a sequential JSON array of executable steps.

Available skills: {skill_list}
Relevant Memory Context: {memory_context}

STRICT MAPPING RULES:
1. If the user wants to see the screen or find a visual error, Step 1 MUST be "VisionSkill" with the instruction: "Look at the screen".
2. If the user wants to fix, build, or write code, Step 2 MUST be "CodingSkill" with the instruction: "Fix the code in [filename]".
3. NEVER use words like "Search", "Scan", or "Browse" for local screen tasks. This triggers the web search by mistake.
4. Return ONLY a valid JSON array. No explanation, no markdown.
5. If the user asks to generate code, write HTML, or fix a script, you MUST use 'CodingSkill' or 'AutonomousCoder'. Do NOT use 'SystemMonitor' or 'Clock' unless the user explicitly asks for the time, date, or battery.
6. If the command is to fix a file, extract the filename and pass it to the Coding tool.
7. If the user asks to generate a UI, a web page, a project, or explicitly asks to SAVE code to a folder, you MUST route to the 'Swarm' or 'ProjectGenerator' skill (whichever handles multi-file writing). Do NOT use the basic 'CodingSkill' for file-saving tasks.
8. If the user asks about a complex, novel, or unfamiliar topic (academic concepts, scientific theories, historical events, technical domains) and the Memory Context is EMPTY or IRRELEVANT, do NOT hallucinate an answer. Instead, route the task to 'DeepResearchSkill' with the instruction: "deep research [topic]". This will scrape the web and store permanent knowledge.
9. If the user asks to open a desktop application, click a button on screen, play media from a specific app, interact with the desktop GUI, or control the mouse/cursor, route the command to 'GhostHandSkill' with the instruction: "click on [element]" or "open [app name]". Do NOT use WindowSkill for app-opening tasks unless it is a window management command (minimize, maximize, snap).
10. CRITICAL: If the user asks to 'fix code', 'debug', or 'edit a file', you MUST route it directly to 'CodingSkill' or 'AutonomousDebugger' ONLY.
11. CRITICAL: Do NOT use 'VisionSkill', 'WebScout', or 'BrowserSkill' for local file editing or coding tasks.
12. CRITICAL: Do NOT use 'FileVaultSkill' unless the user explicitly mentions 'encryption' or 'passwords'.
13. If the user mentions a folder and a file (e.g., 'generated code folder test.py'), extract the path and pass it entirely to 'CodingSkill'.

User request: "{user_input}"

JSON array:"""

# ---- Synthesizer prompt ----
SYNTH_PROMPT = """You are Cipher, a loyal AI assistant. Summarize the results of a multi-step task for your user.

Original request: "{original}"

Steps completed:
{steps}

Write a concise 1-3 sentence summary. Start with "Sir," and be direct. Do not repeat each step — just give the outcome."""


class CipherAgent:
    """
    Ghost OS Central Nervous System.
    """

    def __init__(self, skill_manager, brain=None, speaker=None):
        self.skills       = skill_manager
        self.brain        = brain
        self.speaker      = speaker  
        self.skill_names  = [s.__class__.__name__ for s in skill_manager.skills]
        self.session_mem  = []   
        self.task_log     = []   
        self._verbose     = True
        self.full_control = False
        
        from core.memory_sql import MemorySQL
        from core.memory_vector import MemoryVector
        self.memory_sql = MemorySQL()
        self.memory_vector = MemoryVector()
        
        from core.orchestrator import SwarmOrchestrator
        self.orchestrator = SwarmOrchestrator(self.skills)
        
        self._async_prewarm()

    def _async_prewarm(self):
        """Async Pre-warming: load LLM weights into RAM on boot without blocking."""
        import threading
        def _warm():
            try:
                # Pre-warm planner model
                requests.post(
                    OLLAMA_URL,
                    json={"model": config.PLANNER_MODEL, "prompt": "hi", "stream": False, "keep_alive": -1},
                    timeout=30
                )
                # Pre-warm synthesizer model
                requests.post(
                    OLLAMA_URL,
                    json={"model": config.SYNTHESIZER_MODEL, "prompt": "hi", "stream": False, "keep_alive": -1},
                    timeout=30
                )
                self._log(">> [Agent] Neural models pre-warmed & cached in VRAM.")
            except Exception as e:
                pass
        threading.Thread(target=_warm, daemon=True).start()

    def activate_ghost(self):
        """The Royal Summoning Trigger"""
        # Safely imported inside the function to prevent circular crash
        try:
            from skills.hello import HelloSkill
        except ModuleNotFoundError:
            from skills._archived.hello import HelloSkill
        
        hello = HelloSkill()
        royal_welcome = hello.get_royal_greeting()
        
        # Print full for visual readout, speak clean for audio
        print(f"\n{royal_welcome['full']}")
        
        if self.speaker:
            self.speaker.speak(royal_welcome['clean'])
        else:
            print(royal_welcome)

    def run(self, user_input: str) -> str:
        """
        Ghost OS Level 5: Features Smart Routing, Memory, and Status Cues.
        """
        raw_input = user_input.strip()
        if not raw_input:
            return "Sir, I didn't catch that."

        self._log(f"[AGENT] Raw Input: {raw_input[:80]}")
        start = time.time()

        # ── 0. PRE-PROCESSING ───────────────────
        # Removed words that break skill triggers (like "to" and "for")
        noise_words = ["please", "just", "hey", "can", "you", "cypher"] 
        clean_input = raw_input.lower()
        input_words = clean_input.split()
        processed_input = " ".join([w for w in input_words if w not in noise_words])

        if "full control" in clean_input:
            self.full_control = True
            self._log("[AGENT] Full Control Override Activated.")

        # ── Universal Dynamic App Routing ─────────────────────
        app_match = re.search(r'\bopen\s+(.+?)(?:\s+on\s+(mobile|phone))?$', clean_input)
        if app_match:
            app_name = app_match.group(1).strip()
            is_mobile = bool(app_match.group(2))
            
            self._log(f"[AGENT] Hard Override: App Routing detected. App: {app_name}, Mobile: {is_mobile}")
            
            result = None
            if is_mobile:
                for skill in self.skills.skills:
                    if skill.__class__.__name__ == "MobileSkill":
                        result = skill.execute(f"Launch {app_name}")
                        break
                if not result:
                    result = "Sir, Mobile Skill is not available or failed."
            else:
                for skill in self.skills.skills:
                    if skill.__class__.__name__ == "AppsSkill":
                        result = skill.execute(f"Launch {app_name}")
                        break
                if not result:
                    result = "Sir, Apps Skill is not available or failed."
                    
            final_summary = self._synthesize(raw_input, [{"step": 1, "skill": "MobileSkill" if is_mobile else "AppsSkill", "result": result}])
            self._remember("user", raw_input)
            self._remember("cipher", final_summary)
            if self.speaker:
                self.speaker.speak(final_summary)
            return final_summary

        # ── Hands-Free System Navigation ─────────────────────
        nav_match = re.search(r'\b(go back|go home|scroll up|scroll down|desktop)(?:\s+on\s+(mobile|phone))?$', clean_input)
        if nav_match:
            action = nav_match.group(1).strip()
            is_mobile = bool(nav_match.group(2))
            
            self._log(f"[AGENT] Hard Override: Navigation detected. Action: {action}, Mobile: {is_mobile}")
            
            result = None
            if is_mobile:
                for skill in self.skills.skills:
                    if skill.__class__.__name__ == "MobileSkill":
                        result = skill.execute(action)
                        break
                if not result:
                    result = "Sir, Mobile Skill is not available or failed."
            else:
                for skill in self.skills.skills:
                    if skill.__class__.__name__ == "NavigationSkill":
                        result = skill.execute(action)
                        break
                if not result:
                    result = "Sir, Navigation Skill is not available or failed."
                    
            final_summary = self._synthesize(raw_input, [{"step": 1, "skill": "MobileSkill" if is_mobile else "NavigationSkill", "result": result}])
            self._remember("user", raw_input)
            self._remember("cipher", final_summary)
            if self.speaker:
                self.speaker.speak(final_summary)
            return final_summary

        # ── Live Internet Ingestion Engine ─────────────────────
        live_triggers = ["weather", "bitcoin", "crypto", "hacker news", "world news", "earthquake"]
        if any(w in clean_input for w in live_triggers):
            self._log(f"[AGENT] Hard Override: Live Data detected.")
            
            result = None
            for skill in self.skills.skills:
                if skill.__class__.__name__ == "LiveDataSkill":
                    result = skill.execute(raw_input)
                    break
            if not result:
                result = "Sir, Live Data Skill is not available or failed."
                
            # Pass to LLM for summarization
            prompt = f"Summarize this raw live data payload into a single, natural, voice-friendly response for the user. Data: {result}"
            try:
                resp = requests.post(
                    OLLAMA_URL,
                    json={
                        "model": "qwen2.5-coder:1.5b", 
                        "prompt": prompt, 
                        "stream": False,
                        "options": {"keep_alive": -1}
                    },
                    timeout=30
                )
                if resp.status_code == 200:
                    data = resp.json()
                    final_summary = data.get("response", "").strip()
                else:
                    final_summary = f"Sir, I fetched the data but failed to summarize it. Raw data: {result}"
            except Exception as e:
                final_summary = f"Sir, I fetched the data but failed to summarize it. Raw data: {result}"
                
            self._remember("user", raw_input)
            self._remember("cipher", final_summary)
            if self.speaker:
                self.speaker.speak(final_summary)
            return final_summary

        # ── Browser Automation ─────────────────────
        browser_triggers = ["browse", "scrape website", "search duckduckgo"]
        if any(w in clean_input for w in browser_triggers):
            self._log(f"[AGENT] Hard Override: Browser Automation detected.")
            
            result = None
            for skill in self.skills.skills:
                if skill.__class__.__name__ == "BrowserAutomationSkill":
                    result = skill.execute(raw_input)
                    break
            if not result:
                result = "Sir, Browser Automation Skill is not available or failed."
                
            # Pass to LLM for summarization if it's a scrape
            if "scrape" in clean_input or "browse" in clean_input:
                prompt = f"Summarize this raw webpage content into a short, natural, voice-friendly response for the user. Data: {result[:2000]}"
                try:
                    resp = requests.post(
                        OLLAMA_URL,
                        json={
                            "model": "qwen2.5-coder:1.5b", 
                            "prompt": prompt, 
                            "stream": False,
                            "options": {"keep_alive": -1}
                        },
                        timeout=30
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        final_summary = data.get("response", "").strip()
                    else:
                        final_summary = f"Sir, I scraped the page but failed to summarize it."
                except Exception as e:
                    final_summary = f"Sir, I scraped the page but failed to summarize it."
            else:
                final_summary = result
                
            self._remember("user", raw_input)
            self._remember("cipher", final_summary)
            if self.speaker:
                self.speaker.speak(final_summary)
            return final_summary

        # ── OSINT Aggregator ─────────────────────
        osint_triggers = ["intel", "tech news", "hacker news", "security updates", "latest headlines"]
        if any(w in clean_input for w in osint_triggers):
            self._log(f"[AGENT] Hard Override: OSINT Aggregator detected.")
            
            result = None
            for skill in self.skills.skills:
                if skill.__class__.__name__ == "OSINTAggregatorSkill":
                    result = skill.execute(raw_input)
                    break
            if not result:
                result = "Sir, OSINT Aggregator Skill is not available or failed."
                
            # Pass to LLM for summarization
            prompt = f"Summarize these raw news headlines into a short, natural, voice-friendly response for the user. Data: {result}"
            try:
                resp = requests.post(
                    OLLAMA_URL,
                    json={
                        "model": "qwen2.5-coder:1.5b", 
                        "prompt": prompt, 
                        "stream": False,
                        "options": {"keep_alive": -1}
                    },
                    timeout=30
                )
                if resp.status_code == 200:
                    data = resp.json()
                    final_summary = data.get("response", "").strip()
                else:
                    final_summary = f"Sir, I fetched the headlines but failed to summarize them. Raw data: {result}"
            except Exception as e:
                final_summary = f"Sir, I fetched the headlines but failed to summarize them. Raw data: {result}"
                
            self._remember("user", raw_input)
            self._remember("cipher", final_summary)
            if self.speaker:
                self.speaker.speak(final_summary)
            return final_summary

        # ── Vision Cortex ─────────────────────
        vision_triggers = ["look at my screen", "read this error", "what am i looking at", "analyze my screen"]
        if any(w in clean_input for w in vision_triggers):
            self._log(f"[AGENT] Hard Override: Vision Cortex detected.")
            
            result = None
            for skill in self.skills.skills:
                if skill.__class__.__name__ == "ScreenVisionSkill":
                    result = skill.execute(raw_input)
                    break
            if not result:
                result = "Sir, Vision Skill is not available or failed."
                
            # Pass to LLM for summarization
            prompt = f"Summarize what the vision model sees on the screen into a short, natural, voice-friendly response for the user. Data: {result}"
            try:
                resp = requests.post(
                    OLLAMA_URL,
                    json={
                        "model": "qwen2.5-coder:1.5b", 
                        "prompt": prompt, 
                        "stream": False,
                        "options": {"keep_alive": -1}
                    },
                    timeout=30
                )
                if resp.status_code == 200:
                    data = resp.json()
                    final_summary = data.get("response", "").strip()
                else:
                    final_summary = f"Sir, I analyzed the screen but failed to summarize it. Raw description: {result}"
            except Exception as e:
                final_summary = f"Sir, I analyzed the screen but failed to summarize it. Raw description: {result}"
                
            self._remember("user", raw_input)
            self._remember("cipher", final_summary)
            if self.speaker:
                self.speaker.speak(final_summary)
            return final_summary

        # ── System & Clipboard Awareness ─────────────────────
        sys_triggers = ["system status", "hardware health", "check battery", "cpu", "ram", "explain clipboard", "fix my clipboard", "what did i copy", "clipboard", "copied"]
        if any(w in clean_input for w in sys_triggers):
            self._log(f"[AGENT] Hard Override: System Awareness detected.")
            
            result = None
            for skill in self.skills.skills:
                if skill.__class__.__name__ == "SystemAwarenessSkill":
                    result = skill.execute(raw_input)
                    break
            if not result:
                result = "Sir, System Awareness Skill is not available or failed."
                
            # If it's a clipboard analyze/fix action, we need to pass it to the LLM to do the work.
            if result.startswith("Action: ANALYZE_CLIPBOARD"):
                clipboard_data = result.replace("Action: ANALYZE_CLIPBOARD\nData:", "").strip()
                prompt = f"The user asked: '{raw_input}'. They are referring to this text on their clipboard:\n\n{clipboard_data}\n\nPlease respond to their request based on this clipboard context."
                try:
                    resp = requests.post(
                        OLLAMA_URL,
                        json={"model": "qwen2.5-coder:1.5b", "prompt": prompt, "stream": False, "options": {"keep_alive": -1}},
                        timeout=45
                    )
                    if resp.status_code == 200:
                        final_summary = resp.json().get("response", "").strip()
                    else:
                        final_summary = "Sir, I extracted the clipboard but failed to analyze it."
                except Exception:
                    final_summary = "Sir, I extracted the clipboard but the local model failed to analyze it."
            else:
                final_summary = result
                
            self._remember("user", raw_input)
            self._remember("cipher", final_summary)
            if self.speaker:
                self.speaker.speak(final_summary)
            return final_summary

        # ── Ghost Operator ─────────────────────
        operator_triggers = ["type this", "open application", "press enter", "take control", "press key", "click at"]
        if any(w in clean_input for w in operator_triggers):
            self._log(f"[AGENT] Hard Override: Ghost Operator detected.")
            
            result = None
            for skill in self.skills.skills:
                if skill.__class__.__name__ == "ComputerOperatorSkill":
                    result = skill.execute(raw_input)
                    break
            if not result:
                result = "Sir, Computer Operator Skill is not available or failed."
                
            self._remember("user", raw_input)
            self._remember("cipher", result)
            if self.speaker:
                self.speaker.speak(result)
            return result

        # ── 1. HARD HEURISTIC BYPASS (FAST-PATH) ───────────────
        # Force-routing for common coding/debug tasks to avoid planner hallucinations
        coding_keywords = ['fix', 'debug', 'error', 'refactor']
        coding_extensions = ['.py', '.js', '.html', '.css', '.cpp', '.java', 'code']
        
        is_coding_task = any(kw in clean_input for kw in coding_keywords)
        has_file_context = any(ext in clean_input for ext in coding_extensions)
        
        if is_coding_task and has_file_context:
            self._log("[AGENT] Hard Override: Bypassing planner, routing directly to Coding/Debugger Skill.")
            # Run skills directly with raw input to ensure full path/instruction context
            try:
                result = self.skills.run_skills(raw_input)
            except Exception as e:
                import traceback
                print(f">> [AGENT] Error running skills in Hard Override:")
                traceback.print_exc()
                result = f"Error executing coding skill: {e}"
            
            # Synthesize the result into a professional summary
            final_summary = self._synthesize(raw_input, [{"step": 1, "skill": "AutonomousCoderSkill", "result": result}])
            
            self._remember("user", raw_input)
            self._remember("cipher", final_summary)
            self._record_task(raw_input, [{"step": 1, "skill": "HardOverride(Coding)", "result": result}], final_summary)
            
            # Save to Long-Term Memory
            for s in self.skills.skills:
                if s.__class__.__name__ == "VectorMemorySkill":
                    s.save_interaction(raw_input, final_summary)
                    break

            # THE MAGIC WORD THAT STOPS THE LEAK:
            return final_summary

        # Web Search Hard Override
        search_keywords = ["score", "match", "who is", "what is", "latest", "news", "search"]
        if any(w in clean_input for w in search_keywords):
            self._log("[AGENT] Hard Override: Bypassing planner, routing directly to WebScoutSkill.")
            for s in self.skills.skills:
                if s.__class__.__name__ == "WebScoutSkill":
                    result = s.execute(raw_input)
                    if result:
                        self._remember("user", raw_input)
                        self._remember("cipher", result)
                        self._record_task(raw_input, [{"step": 1, "skill": "WebScoutSkill", "result": result}], result)
                        return result

        # ── 2. HEURISTIC ROUTING ──────────────────────────
        # Forced Planner triggers: "and", "then", "also", or the "fix" command
        is_compound = any(w in raw_input.lower() for w in [" and ", " then ", " also ", " fix "])
        
        # FAST PATH: If it's not a multi-step compound request, ALWAYS try skills first!
        if not is_compound:
            # Smart Routing: Prioritize MobileSkill if requested
            if any(w in clean_input for w in ["mobile", "phone"]):
                self._log("[AGENT] Mobile intent detected. Prioritizing MobileSkill.")
                for s in self.skills.skills:
                    if s.__class__.__name__ == "MobileSkill":
                        quick = s.execute(clean_input)
                        if quick:
                            self._remember("user",   raw_input)
                            self._remember("cipher", quick)
                            self._log(f"[AGENT] Mobile fast-path match: {time.time()-start:.2f}s")
                            self._record_task(raw_input, [{"step":1,"result":quick}], quick)
                            return quick
            
            # Fallback to normal skill execution
            quick = self.skills.run_skills(clean_input)
            if quick:
                self._remember("user",   raw_input)
                self._remember("cipher", quick)
                self._log(f"[AGENT] Fast-path match: {time.time()-start:.2f}s")
                self._record_task(raw_input, [{"step":1,"result":quick}], quick)
                return quick

        # ── 3. SWARM ORCHESTRATOR PATH ────────────────────
        if self.speaker:
            self.speaker.speak("Analyzing multi-step sequence, please hold...")
            
        self._log(f"[AGENT] Routing complex request to Swarm Orchestrator.")
        
        # We fetch memory context just in case we need it later, but the orchestrator handles the rest.
        sql_context = self.memory_sql.get_recent_context(limit=3)
        vector_context = self.memory_vector.query_semantic_memory(raw_input, n_results=2)
        
        from core.state_manager import StateManager
        if sql_context:
            StateManager.add_memory_retrieval(f"SQL Memory: {sql_context[:100]}...")
        if vector_context:
            StateManager.add_memory_retrieval(f"Vector Memory: {', '.join(vector_context)[:100]}...")
            
        past_context = ""
        if sql_context:
            past_context += f"Recent Timeline Logs:\n{sql_context}\n\n"
        if vector_context:
            past_context += f"Semantically Relevant Facts:\n" + "\n".join(vector_context)
            
        if past_context:
            raw_input_with_context = f"{raw_input}\nContext:\n{past_context}"
        else:
            raw_input_with_context = raw_input
            
        final_summary = self.orchestrator.delegate_task(raw_input_with_context)
        
        self._remember("user", raw_input)
        self._remember("cipher", final_summary)
        
        # Save to Long-Term Memory
        for s in self.skills.skills:
            if s.__class__.__name__ == "VectorMemorySkill":
                s.save_interaction(raw_input, final_summary)
                break
                
        if self.speaker:
            self.speaker.speak(final_summary)
            
        return final_summary

    # ------------------------------------------------------------------ #
    #  PLANNING & SYNTHESIS                                              #
    # ------------------------------------------------------------------ #

    def _plan(self, user_input: str, memory_context: str = "") -> list | None:
        """Ask the LLM to decompose the task into steps."""
        prompt = PLAN_PROMPT.format(
            skill_list = ", ".join(self.skill_names),
            user_input = user_input,
            memory_context = memory_context
        )
        try:
            # 15s timeout for stability to fast-fail to neural brain
            resp = requests.post(
                OLLAMA_URL,
                json={
                    "model": config.PLANNER_MODEL, 
                    "prompt": prompt, 
                    "stream": False,
                    "options": {"keep_alive": -1}
                },
                timeout=30
            )
            if resp.status_code != 200:
                self._log(f"[AGENT] Ollama HTTP {resp.status_code} Error: Model likely not found or unloaded.")
                return None
            try:
                data = resp.json()
                raw_text = data.get("response", "")
                # Strip DeepSeek <think> tags safely
                think_end = raw_text.find("</think>")
                clean_text = raw_text[think_end + 8:].strip() if think_end != -1 else raw_text.strip()
            except Exception as e:
                self._log(f"[AGENT] Failed to parse Ollama response: {str(e)}")
                return None
                
            # Surgically extract JSON array in case the LLM yaps
            json_match = re.search(r'\[.*\]', clean_text, re.DOTALL)
            if json_match:
                clean_text = json_match.group()
                
            try:
                plan = json.loads(clean_text)
                if isinstance(plan, list):
                    return plan
            except Exception as e:
                self._log(f"[AGENT] JSON Parse Error: {str(e)}. Using fallback step.")
                # Fallback step: just pass the input to the brain
                return [{"step": 1, "skill": "brain", "instruction": user_input}]
        except Exception as e:
            self._log(f"[AGENT] Planning error: {e}")
        return None

    def _synthesize(self, original: str, steps: list) -> str:
        """Summarize multi-step results into one clean reply."""
        steps_text = "\n".join(
            f"Step {s['step']} ({s['skill']}): {str(s['result'])[:300]}"
            for s in steps
        )
        prompt = SYNTH_PROMPT.format(original=original, steps=steps_text)
        try:
            resp = requests.post(
                OLLAMA_URL,
                json={
                    "model": config.SYNTHESIZER_MODEL, 
                    "prompt": prompt, 
                    "stream": False,
                    "options": {"keep_alive": -1}
                },
                timeout=30
            )
            if resp.status_code != 200:
                return f"Sir, all steps completed. (Fallback: HTTP {resp.status_code})"
            try:
                data = resp.json()
                raw_text = data.get("response", "")
                think_end = raw_text.find("</think>")
                clean_text = raw_text[think_end + 8:].strip() if think_end != -1 else raw_text.strip()
                return clean_text if clean_text else "Sir, all steps completed."
            except Exception as e:
                return "Sir, all steps completed. (Synthesis parse error)"
        except Exception as e:
            self._log(f"[AGENT] Synthesis error: {e}")
            return "Sir, all steps completed successfully."

    # ------------------------------------------------------------------ #
    #  SESSION MEMORY                                                    #
    # ------------------------------------------------------------------ #

    def _remember(self, role: str, text: str):
        """Rolling short-term memory (last 20 turns)."""
        self.session_mem.append({
            "role":      role,
            "text":      str(text)[:500],
            "timestamp": datetime.now().isoformat(),
        })
        if len(self.session_mem) > 20:
            self.session_mem.pop(0)

    def _build_context_prefix(self) -> str:
        """Inject recent conversation into LLM prompt for continuity."""
        if not self.session_mem:
            return ""
        recent = self.session_mem[-6:]
        lines = ["Recent conversation:"]
        for turn in recent:
            tag = "User" if turn["role"] == "user" else "Cipher"
            lines.append(f"  {tag}: {turn['text'][:200]}")
        return "\n".join(lines) + "\n\nNow respond to: "

    def get_session_memory(self) -> list:
        return list(self.session_mem)

    def clear_session(self):
        self.session_mem.clear()
        self._log("[AGENT] Session memory cleared.")

    # ------------------------------------------------------------------ #
    #  TASK LOG                                                          #
    # ------------------------------------------------------------------ #

    def _record_task(self, inp: str, steps: list, output: str):
        self.task_log.append({
            "timestamp": datetime.now().isoformat(),
            "input":     inp[:300],
            "steps":     len(steps),
            "output":    str(output)[:300],
        })
        if len(self.task_log) > 100:
            self.task_log.pop(0)
            
        # Log to Hybrid Memory
        executed_skill = steps[0].get("skill", "unknown") if steps else "unknown"
        try:
            self.memory_sql.add_log(inp, executed_skill, output)
            self.memory_vector.remember_fact(f"User: {inp}\nCipher: {output}", {"skill": executed_skill})
        except Exception as e:
            self._log(f"[AGENT] Failed to log to hybrid memory: {e}")

    def get_task_log(self) -> list:
        return list(self.task_log)

    # ------------------------------------------------------------------ #
    #  UTILS                                                             #
    # ------------------------------------------------------------------ #

    def _log(self, msg: str):
        if self._verbose:
            print(msg)

    def clear_temp_files(self):
        """Unified lifecycle management: Clean up temporary media."""
        import os
        import shutil
        self._log("[AGENT] Sweeping temporary files...")
        
        if os.path.exists("temp_vision"):
            try:
                shutil.rmtree("temp_vision")
            except Exception as e:
                self._log(f"[AGENT] Failed to clear temp_vision: {e}")
                
        for f in ["temp_input.wav", "input.wav"]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception as e:
                    self._log(f"[AGENT] Failed to remove {f}: {e}")

    def _verify_file(self, filepath: str) -> tuple[bool, str]:
        """Hidden Linter / Syntax Checker for Triple-Check Loop."""
        import subprocess
        import os
        ext = os.path.splitext(filepath)[1].lower()
        if not os.path.exists(filepath):
            return True, ""
            
        try:
            if ext == '.py':
                res = subprocess.run(['python', '-m', 'py_compile', filepath], capture_output=True, text=True)
                if res.returncode != 0:
                    return False, res.stderr
            elif ext in ['.js', '.ts']:
                res = subprocess.run(['node', '--check', filepath], capture_output=True, text=True)
                if res.returncode != 0:
                    return False, res.stderr
        except Exception as e:
            return False, str(e)
            
        return True, ""