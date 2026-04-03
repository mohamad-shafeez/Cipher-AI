# skills/git_commander.py
# ============================================================
#   CIPHER GIT COMMANDER
#   Full Git workflow control by voice or text command.
#
#   Triggers (examples):
#     "git status"         → show working tree status
#     "git commit saving login fix"  → stage all + commit
#     "git push"           → push to origin current branch
#     "git pull"           → pull latest
#     "git log"            → last 5 commits
#     "git branch"         → list branches
#     "git new branch feature-auth"  → create + checkout
#     "git switch main"    → checkout a branch
#     "git stash"          → stash changes
#     "git restore"        → restore stash
#     "git diff"           → show unstaged changes
#     "git undo"           → soft reset last commit
#     "git clone <url>"    → clone a repo
# ============================================================

import subprocess
import os
import re


class GitCommanderSkill:

    def execute(self, command: str) -> str | None:
        cmd = command.lower().strip()

        if not cmd.startswith("git"):
            return None

        # Route to handlers
        if "status" in cmd:
            return self._status()
        if "log" in cmd:
            return self._log()
        if "diff" in cmd:
            return self._diff()
        if "branch" in cmd and ("new" in cmd or "create" in cmd):
            name = self._extract_after(cmd, ["new branch", "create branch"])
            return self._new_branch(name)
        if "branch" in cmd:
            return self._branches()
        if "switch" in cmd or "checkout" in cmd:
            name = self._extract_after(cmd, ["switch", "checkout"])
            return self._switch(name)
        if "commit" in cmd:
            msg = self._extract_after(cmd, ["commit"])
            return self._commit(msg or "Auto-commit by Cipher")
        if "push" in cmd:
            return self._push()
        if "pull" in cmd:
            return self._pull()
        if "stash" in cmd and "restore" not in cmd and "pop" not in cmd:
            return self._stash()
        if "restore" in cmd or "stash pop" in cmd:
            return self._stash_pop()
        if "undo" in cmd:
            return self._undo()
        if "clone" in cmd:
            url = self._extract_url(cmd)
            return self._clone(url)
        if "init" in cmd:
            return self._init()

        return None

    # ------------------------------------------------------------------ #

    def _run(self, *args, cwd=None) -> tuple[bool, str]:
        try:
            r = subprocess.run(
                ["git"] + list(args),
                capture_output=True, text=True,
                timeout=30, cwd=cwd or os.getcwd()
            )
            out = (r.stdout + r.stderr).strip()
            return r.returncode == 0, out or "(no output)"
        except FileNotFoundError:
            return False, "Git is not installed or not in PATH."
        except Exception as e:
            return False, str(e)

    def _status(self) -> str:
        ok, out = self._run("status", "--short", "--branch")
        return f"Sir, Git status:\n{out}"

    def _log(self) -> str:
        ok, out = self._run(
            "log", "--oneline", "--decorate", "--graph", "-8"
        )
        return f"Sir, last 8 commits:\n{out}"

    def _diff(self) -> str:
        ok, out = self._run("diff", "--stat")
        if not out.strip():
            return "Sir, no unstaged changes."
        return f"Sir, diff summary:\n{out}"

    def _commit(self, message: str) -> str:
        # Stage all changes first
        self._run("add", "-A")
        ok, out = self._run("commit", "-m", message)
        if ok:
            return f"Sir, committed: '{message}'\n{out}"
        return f"Sir, commit failed:\n{out}"

    def _push(self) -> str:
        ok, out = self._run("push")
        return f"Sir, push {'successful' if ok else 'failed'}:\n{out}"

    def _pull(self) -> str:
        ok, out = self._run("pull")
        return f"Sir, pull {'successful' if ok else 'failed'}:\n{out}"

    def _branches(self) -> str:
        ok, out = self._run("branch", "-a")
        return f"Sir, branches:\n{out}"

    def _new_branch(self, name: str) -> str:
        if not name:
            return "Sir, please provide a branch name."
        name = name.replace(" ", "-").lower()
        ok, out = self._run("checkout", "-b", name)
        return f"Sir, branch '{name}' {'created and checked out' if ok else 'failed'}:\n{out}"

    def _switch(self, name: str) -> str:
        if not name:
            return "Sir, which branch should I switch to?"
        ok, out = self._run("checkout", name)
        return f"Sir, switched to '{name}'" if ok else f"Sir, switch failed:\n{out}"

    def _stash(self) -> str:
        ok, out = self._run("stash")
        return f"Sir, changes stashed.\n{out}" if ok else f"Sir, stash failed:\n{out}"

    def _stash_pop(self) -> str:
        ok, out = self._run("stash", "pop")
        return f"Sir, stash restored.\n{out}" if ok else f"Sir, no stash to restore."

    def _undo(self) -> str:
        ok, out = self._run("reset", "--soft", "HEAD~1")
        return "Sir, last commit undone. Changes kept in staging." if ok else f"Sir, undo failed:\n{out}"

    def _clone(self, url: str) -> str:
        if not url:
            return "Sir, please provide a repository URL."
        ok, out = self._run("clone", url)
        return f"Sir, cloned {url}." if ok else f"Sir, clone failed:\n{out}"

    def _init(self) -> str:
        ok, out = self._run("init")
        return "Sir, Git repository initialized." if ok else f"Sir, init failed:\n{out}"

    # ------------------------------------------------------------------ #
    #  HELPERS                                                             #
    # ------------------------------------------------------------------ #

    def _extract_after(self, text: str, keywords: list[str]) -> str:
        for kw in keywords:
            idx = text.find(kw)
            if idx != -1:
                return text[idx + len(kw):].strip()
        return ""

    def _extract_url(self, text: str) -> str:
        match = re.search(r'https?://\S+', text)
        return match.group(0) if match else ""