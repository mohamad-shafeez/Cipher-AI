# core/agent.py
# ============================================================
#   CIPHER AGENT CORE — Multi-Step Planner & Executor
#   Ghost OS Level 5 Edition
# ============================================================

import json
import time
import requests
from datetime import datetime
import config

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL      = config.LLM_MODEL   # <--- The corrected config link

PLAN_PROMPT = """You are Cipher's internal task orchestrator. 
Break the user's request into a sequential JSON array of executable steps.

Available skills: {skill_list}

STRICT MAPPING RULES:
1. If the user wants to see the screen or find a visual error, Step 1 MUST be "VisionSkill" with the instruction: "Look at the screen".
2. If the user wants to fix, build, or write code, Step 2 MUST be "CodingSkill" with the instruction: "Fix the code in [filename]".
3. NEVER use words like "Search", "Scan", or "Browse" for local screen tasks. This triggers the web search by mistake.
4. Return ONLY a valid JSON array. No explanation, no markdown.

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

    def activate_ghost(self):
        """The Royal Summoning Trigger"""
        # Safely imported inside the function to prevent circular crash
        from skills.hello import HelloSkill
        hello = HelloSkill()
        royal_welcome = hello.get_royal_greeting()
        
        if self.speaker:
            self.speaker.speak(royal_welcome)
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
        noise_words = ["like", "for", "please", "just", "hey", "can", "you", "to"]
        clean_input = raw_input.lower()
        input_words = clean_input.split()
        processed_input = " ".join([w for w in input_words if w not in noise_words])

        # ── 1. HEURISTIC ROUTING ──────────────────────────
        # Forced Planner triggers: "and", "then", "also", or the "fix" command
        is_compound = any(w in raw_input.lower() for w in [" and ", " then ", " also ", " fix "])
        
        # God Mode Triggers for Fast-Path
        god_mode_triggers = ["look", "see", "screen", "status", "who are you", "time"]
        has_god_trigger = any(w in processed_input for w in god_mode_triggers)
        
        # FAST PATH: Only if it is NOT compound.
        if not is_compound and (len(input_words) < 7 or has_god_trigger):
            quick = self.skills.run_skills(processed_input)
            if quick:
                self._remember("user",   raw_input)
                self._remember("cipher", quick)
                self._log(f"[AGENT] Fast-path match: {time.time()-start:.2f}s")
                self._record_task(raw_input, [{"step":1,"result":quick}], quick)
                return quick

        # ── 2. PLANNER PATH ────────────────────
        if self.speaker:
            self.speaker.speak("Analyzing sequence, please hold...")

        plan = self._plan(raw_input)

        # ── 3. FALLBACK: Direct Brain Reasoning ───────────────────────
        if not plan or len(plan) <= 1:
            self._log("[AGENT] Routing to Neural Brain")
            if self.brain:
                context_prefix = self._build_context_prefix()
                reply = self.brain.think(context_prefix + raw_input)
                self._remember("user",   raw_input)
                self._remember("cipher", reply)
                self._record_task(raw_input, [], reply)
                return reply
            return "Sir, I'm unable to process that request."

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
            instruction = f"{base_instr}. Context from previous step: {last_result}" if last_result else base_instr

            self._log(f"  >> Step {step_num} [{skill_hint}]: {instruction[:80]}...")

            # Execute Skill
            result = self.skills.run_skills(instruction)
            
            if not result and self.brain:
                result = self.brain.think(instruction)

            result = result or "[Task completed]"
            last_result = str(result)[:500] # Save the findings for the next step
            
            step_results.append({
                "step": step_num, "skill": skill_hint, "result": result
            })
    # ------------------------------------------------------------------ #
    #  PLANNING & SYNTHESIS                                              #
    # ------------------------------------------------------------------ #

    def _plan(self, user_input: str) -> list | None:
        """Ask the LLM to decompose the task into steps."""
        prompt = PLAN_PROMPT.format(
            skill_list = ", ".join(self.skill_names),
            user_input = user_input
        )
        try:
            # 120s timeout for stability
            resp = requests.post(
                OLLAMA_URL,
                json={"model": MODEL, "prompt": prompt, "stream": False},
                timeout=120
            )
            raw = resp.json().get("response", "").strip()
            # Strip markdown fences if model added them
            raw = raw.strip("```json").strip("```").strip()
            plan = json.loads(raw)
            if isinstance(plan, list) and all(isinstance(s, dict) for s in plan):
                return plan
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
            # 120s timeout for stability
            resp = requests.post(
                OLLAMA_URL,
                json={"model": MODEL, "prompt": prompt, "stream": False},
                timeout=120
            )
            return resp.json().get("response", "Sir, all steps completed.").strip()
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
        """Expose session memory (used by knowledge_forge or debug tools)."""
        return list(self.session_mem)

    def clear_session(self):
        """Reset short-term memory on new chat session."""
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