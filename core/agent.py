# core/agent.py
# ============================================================
#   CIPHER AGENT CORE — Multi-Step Planner & Executor
#   Upgrades Cipher from a skill-router to a true AI agent.
#   Supports: multi-step task planning, skill chaining,
#             session-scoped short-term memory, synthesis.
# ============================================================

import json
import time
import requests
from datetime import datetime

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL      = "deepseek-r1:1.5b"   # swap to phi3.5 or any ollama model

# ---- Planner prompt ----
PLAN_PROMPT = """You are Cipher's internal task planner. Your job is to break a user's request into sequential executable steps.

Available skills: {skill_list}

Rules:
- Return ONLY a valid JSON array. No explanation, no markdown fences.
- Maximum 5 steps.
- Each step: {{"step": <int>, "skill": "<skill_name>", "instruction": "<what to do>"}}
- If the task is simple and needs only 1 skill, return a 1-item array.
- Map instructions to real executable commands Cipher understands.
- If no skill fits a step, use "brain" as the skill name.

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
    Drop-in replacement for the skills.run_skills() + brain.think() pattern.
    
    Usage in main.py:
        agent = CipherAgent(skills, brain)
        response = agent.run(command)
    """

    def __init__(self, skill_manager, brain=None):
        self.skills       = skill_manager
        self.brain        = brain
        self.skill_names  = [s.__class__.__name__ for s in skill_manager.skills]
        self.session_mem  = []   # short-term rolling window (current session)
        self.task_log     = []   # full audit log of every task attempted
        self._verbose     = True

    # ------------------------------------------------------------------ #
    #  PUBLIC: main entry point                                            #
    # ------------------------------------------------------------------ #

    def run(self, user_input: str) -> str:
        """
        Main entry point. Replaces the old
        `skills.run_skills(cmd) or brain.think(cmd)` pattern.
        """
        user_input = user_input.strip()
        if not user_input:
            return "Sir, I didn't catch that."

        self._log(f"[AGENT] Input: {user_input[:80]}")
        start = time.time()

       # ── 1. Fast path: direct skill match ──────────────────────────
        # If the sentence has commas or words like "and", "then", it's a compound task. 
        # Skip the fast path and force the planner to break it down.
        is_compound = any(word in user_input for word in [" and ", " then ", " also "]) or "," in user_input
        
        if not is_compound:
            quick = self.skills.run_skills(user_input)
            if quick:
                self._remember("user",   user_input)
                self._remember("cipher", quick)
                self._log(f"[AGENT] Fast-path skill match ({time.time()-start:.2f}s)")
                self._record_task(user_input, [{"step":1,"result":quick}], quick)
                return quick
        else:
            self._log("[AGENT] Compound command detected. Bypassing fast-path for Planner.")

        # ── 2. Check if this is a multi-step / compound task ──────────
        plan = self._plan(user_input)

        # Planning failed or returned 1 step → straight to LLM brain
        if not plan or len(plan) <= 1:
            self._log("[AGENT] Single-step — routing to LLM brain")
            if self.brain:
                context_prefix = self._build_context_prefix()
                reply = self.brain.think(context_prefix + user_input)
                self._remember("user",   user_input)
                self._remember("cipher", reply)
                self._record_task(user_input, [], reply)
                return reply
            return None   # caller handles fallback if no brain injected

        # ── 3. Execute the plan step by step ──────────────────────────
        self._log(f"[AGENT] Executing {len(plan)}-step plan...")
        step_results = []

        for step in plan:
            step_num   = step.get("step", "?")
            instruction = step.get("instruction", "").strip()
            skill_hint  = step.get("skill", "")
            self._log(f"  >> Step {step_num} [{skill_hint}]: {instruction[:60]}")

            result = self.skills.run_skills(instruction)

            # If no skill matched, use brain as fallback for this step
            if not result and self.brain:
                result = self.brain.think(instruction)

            result = result or f"[Step {step_num} — no output]"
            step_results.append({
                "step":        step_num,
                "skill":       skill_hint,
                "instruction": instruction,
                "result":      result,
            })
            self._log(f"  >> Step {step_num} result: {str(result)[:80]}")

        # ── 4. Synthesize all results into one reply ───────────────────
        final = self._synthesize(user_input, step_results)
        self._remember("user",   user_input)
        self._remember("cipher", final)
        self._record_task(user_input, step_results, final)
        self._log(f"[AGENT] Done in {time.time()-start:.2f}s")
        return final

    # ------------------------------------------------------------------ #
    #  PLANNING                                                            #
    # ------------------------------------------------------------------ #

    def _plan(self, user_input: str) -> list | None:
        """Ask the LLM to decompose the task into steps."""
        prompt = PLAN_PROMPT.format(
            skill_list = ", ".join(self.skill_names),
            user_input = user_input
        )
        try:
            resp = requests.post(
                OLLAMA_URL,
                json={"model": MODEL, "prompt": prompt, "stream": False},
                timeout=20
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

    # ------------------------------------------------------------------ #
    #  SYNTHESIS                                                           #
    # ------------------------------------------------------------------ #

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
                json={"model": MODEL, "prompt": prompt, "stream": False},
                timeout=20
            )
            return resp.json().get("response", "Sir, all steps completed.").strip()
        except:
            return "Sir, all steps completed successfully."

    # ------------------------------------------------------------------ #
    #  SESSION MEMORY                                                      #
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
    #  TASK LOG                                                            #
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
    #  UTILS                                                               #
    # ------------------------------------------------------------------ #

    def _log(self, msg: str):
        if self._verbose:
            print(msg)