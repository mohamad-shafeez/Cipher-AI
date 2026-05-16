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
        self._async_prewarm()

    def _async_prewarm(self):
        """Async Pre-warming: load LLM weights into RAM on boot without blocking."""
        import threading
        def _warm():
            try:
                # Pre-warm planner model
                requests.post(
                    OLLAMA_URL,
                    json={"model": "deepseek-r1:1.5b", "prompt": "hi", "stream": False},
                    timeout=30
                )
                # Pre-warm synthesizer model
                requests.post(
                    OLLAMA_URL,
                    json={"model": "llama3.2:3b", "prompt": "hi", "stream": False},
                    timeout=30
                )
                self._log(">> [Agent] Neural models pre-warmed & cached in RAM.")
            except Exception as e:
                pass
        threading.Thread(target=_warm, daemon=True).start()

    def activate_ghost(self):
        """The Royal Summoning Trigger"""
        # Safely imported inside the function to prevent circular crash
        from skills.hello import HelloSkill
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

        # ── 1. HARD HEURISTIC BYPASS (FAST-PATH) ───────────────
        # Force-routing for common coding/debug tasks to avoid planner hallucinations
        coding_keywords = ['fix', 'debug', 'error', 'refactor']
        coding_extensions = ['.py', '.js', '.html', '.css', '.cpp', '.java', 'code']
        
        is_coding_task = any(kw in clean_input for kw in coding_keywords)
        has_file_context = any(ext in clean_input for ext in coding_extensions)
        
        if is_coding_task and has_file_context:
            self._log("[AGENT] Hard Override: Bypassing planner, routing directly to Coding/Debugger Skill.")
            # Run skills directly with raw input to ensure full path/instruction context
            result = self.skills.run_skills(raw_input)
            if result:
                self._remember("user", raw_input)
                self._remember("cipher", result)
                self._log(f"[AGENT] Hard-path match: {time.time()-start:.2f}s")
                self._record_task(raw_input, [{"step": 1, "skill": "HardOverride(Coding)", "result": result}], result)
                return result
            
            # If we match the heuristic but skills fail, we MUST still exit to avoid planner hallucinations
            self._log("[AGENT] Hard Override matched but skills returned empty. Forcing exit.")
            return "Sir, I recognized the coding task but the internal repair module failed to return a result. Please check the file path."

        # ── 2. HEURISTIC ROUTING ──────────────────────────
        # Forced Planner triggers: "and", "then", "also", or the "fix" command
        is_compound = any(w in raw_input.lower() for w in [" and ", " then ", " also ", " fix "])
        
        # FAST PATH: If it's not a multi-step compound request, ALWAYS try skills first!
        if not is_compound:
            # We pass clean_input so skills that look for exact phrasing don't break
            quick = self.skills.run_skills(clean_input)
            if quick:
                self._remember("user",   raw_input)
                self._remember("cipher", quick)
                self._log(f"[AGENT] Fast-path match: {time.time()-start:.2f}s")
                self._record_task(raw_input, [{"step":1,"result":quick}], quick)
                return quick

        # ── 3. PLANNER PATH ────────────────────
        if self.speaker:
            self.speaker.speak("Analyzing sequence, please hold...")
            
        # Get Long-Term Memory Context
        past_context = ""
        for s in self.skills.skills:
            if s.__class__.__name__ == "VectorMemorySkill":
                past_context = s.similarity_search(raw_input)
                break
        
        if past_context:
            self._log(f"[AGENT] Retrieved Memory Context: {past_context[:100]}...")

        plan = self._plan(raw_input, past_context)

        # ── 4. FALLBACK: Local Error Handling ───────────────────────
        if not plan or len(plan) <= 1:
            self._log("[AGENT] Planner failed or returned empty.")
            reply = "Local brain is congested. Please repeat."
            self._remember("user",   raw_input)
            self._remember("cipher", reply)
            self._record_task(raw_input, [], reply)
            return reply

        # ── 4. EXECUTION: Multi-Step Sequence with Context Injection ──
        self._log(f"[AGENT] Executing {len(plan)}-step plan...")
        step_results = []
        last_result = "" # <--- THE MEMORY BRIDGE

        for step in plan:
            step_num    = step.get("step", "?")
            base_instr  = step.get("instruction", "").strip()
            skill_hint  = step.get("skill", "brain")
            
            # INJECTION: We append the last result to the current instruction
            # This tells the Coder what the Vision saw!
            prev_skill = step_results[-1]["skill"] if step_results else ""
            if "Vision" in prev_skill and "error" in last_result.lower():
                instruction = f"{base_instr}. Bug Report context from VisionSkill: {last_result}"
            else:
                instruction = f"{base_instr}. Context from previous step: {last_result}" if last_result else base_instr

            self._log(f"  >> Step {step_num} [{skill_hint}]: {instruction[:80]}...")

            # ── PERMISSION GATE (REMOVED: Main thread roadblock resolved) ──
            # Automated progression active. Code security is now handled 
            # by the Plagiarism Guardian & UI Patch Diff Card systems.

            # Execute Skill
            result = self.skills.run_skills(instruction)
            
            # ── TRIPLE-CHECK LOOP (Execute, Verify, Repair) ──
            if result and "Successfully created" in result:
                files_created = []
                if ":" in result:
                    files_str = result.split(":", 1)[1].strip()
                    files_created = [f.strip() for f in files_str.split(",")]
                
                for fpath in files_created:
                    verify_ok, error_msg = self._verify_file(fpath)
                    if not verify_ok:
                        self._log(f"[TRIPLE-CHECK] Verification failed for {fpath}. Auto-repairing...")
                        for s in self.skills.skills:
                            if s.__class__.__name__ == "CodingSkill":
                                fix_result = s.fix_my_code(fpath)
                                self._log(f"[TRIPLE-CHECK] Repair result: {fix_result}")
                                result += f" (Auto-repaired {fpath})"
                                break
            
            if not result and self.brain:
                result = self.brain.think(instruction)

            result = result or "[Task completed]"
            last_result = str(result)[:500] # Save the findings for the next step
            
            step_results.append({
                "step": step_num, "skill": skill_hint, "result": result
            })
            
        # Synthesize final response
        final_summary = self._synthesize(raw_input, step_results)
        self._remember("user", raw_input)
        self._remember("cipher", final_summary)
        self._record_task(raw_input, step_results, final_summary)
        
        # Save to Long-Term Memory
        for s in self.skills.skills:
            if s.__class__.__name__ == "VectorMemorySkill":
                s.save_interaction(raw_input, final_summary)
                break
                
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
                    "model": "deepseek-r1:1.5b", 
                    "prompt": prompt, 
                    "stream": False
                },
                timeout=120
            )
            if resp.status_code != 200:
                self._log(f"[AGENT] Ollama HTTP {resp.status_code} Error: Model likely not found or unloaded.")
                return None
            try:
                data = resp.json()
                raw_text = data.get("response", "")
                # Strip DeepSeek <think> tags safely
                clean_text = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL).strip()
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
                    "model": "llama3.2:3b", 
                    "prompt": prompt, 
                    "stream": False,
                    "keep_alive": "5m"
                },
                timeout=120
            )
            if resp.status_code != 200:
                return f"Sir, all steps completed. (Fallback: HTTP {resp.status_code})"
            try:
                data = resp.json()
                raw_text = data.get("response", "")
                clean_text = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL).strip()
                return clean_text if clean_text else "Sir, all steps completed."
            except Exception as e:
                return "Sir, all steps completed. (Synthesis parse error)"
        except:
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