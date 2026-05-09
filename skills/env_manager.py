# skills/env_manager.py
# ============================================================
#   CIPHER ENV MANAGER
#   Read, set, delete and list .env variables by voice.
#   Never prints secret values in full — shows masked versions.
#
#   Triggers:
#     "env list"                     → list all keys (masked)
#     "env get API_KEY"              → show masked value
#     "env set PORT 5500"            → add/update a variable
#     "env delete OLD_KEY"           → remove a key
#     "env backup"                   → copy .env → .env.backup
#     "env reload"                   → reload into os.environ
#     "env check"                    → verify all keys present
# ============================================================

import os
import re
import shutil
from pathlib import Path
from datetime import datetime


class EnvManagerSkill:

    TRIGGERS = ["env list", "env get ", "env set ", "env delete ",
                "env backup", "env reload", "env check",
                "list env", "show env"]

    ENV_PATH = Path(".env")

    def execute(self, command: str) -> str | None:
        cmd = command.lower().strip()

        if not any(t in cmd for t in self.TRIGGERS):
            return None

        if "env list" in cmd or "list env" in cmd or "show env" in cmd:
            return self._list()
        if cmd.startswith("env get "):
            return self._get(command[8:].strip().upper())
        if cmd.startswith("env set "):
            return self._set(command[8:].strip())
        if cmd.startswith("env delete "):
            return self._delete(command[11:].strip().upper())
        if "env backup" in cmd:
            return self._backup()
        if "env reload" in cmd:
            return self._reload()
        if "env check" in cmd:
            return self._check()

        return None

    # ------------------------------------------------------------------ #

    def _read_env(self) -> dict[str, str]:
        """Parse .env into {KEY: VALUE} dict."""
        env = {}
        if not self.ENV_PATH.exists():
            return env
        for line in self.ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip().strip('"').strip("'")
        return env

    def _write_env(self, data: dict[str, str]):
        """Write dict back to .env, preserving comments."""
        if not self.ENV_PATH.exists():
            lines = []
        else:
            lines = self.ENV_PATH.read_text(encoding="utf-8").splitlines()

        # Build new line set — update existing keys, append new ones
        written_keys = set()
        new_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#") or not stripped:
                new_lines.append(line)
                continue
            if "=" in stripped:
                k = stripped.split("=", 1)[0].strip()
                if k in data:
                    new_lines.append(f'{k}="{data[k]}"')
                    written_keys.add(k)
                    continue
            new_lines.append(line)

        # Append brand-new keys
        for k, v in data.items():
            if k not in written_keys:
                new_lines.append(f'{k}="{v}"')

        self.ENV_PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    def _mask(self, value: str) -> str:
        """Show first 3 and last 2 chars, mask the middle."""
        if len(value) <= 6:
            return "*" * len(value)
        return value[:3] + "*" * (len(value) - 5) + value[-2:]

    def _list(self) -> str:
        env = self._read_env()
        if not env:
            return f"Sir, .env not found at {self.ENV_PATH.absolute()} or it is empty."
        lines = [f"Sir, {len(env)} variable(s) in .env:\n"]
        for k, v in sorted(env.items()):
            lines.append(f"  {k:30s} = {self._mask(v)}")
        return "\n".join(lines)

    def _get(self, key: str) -> str:
        env = self._read_env()
        if key in env:
            return f"Sir, {key} = {self._mask(env[key])}  ({len(env[key])} chars)"
        # Also check live os.environ
        live = os.environ.get(key)
        if live:
            return f"Sir, {key} found in environment (not in .env): {self._mask(live)}"
        return f"Sir, key '{key}' not found in .env or environment."

    def _set(self, raw: str) -> str:
        """Parse 'KEY value with spaces' or 'KEY=value'."""
        raw = raw.strip()
        if "=" in raw:
            key, _, val = raw.partition("=")
        else:
            parts = raw.split(" ", 1)
            if len(parts) < 2:
                return "Sir, format: env set KEY_NAME value"
            key, val = parts
        key = key.strip().upper()
        val = val.strip().strip('"').strip("'")

        env = self._read_env()
        is_update = key in env
        env[key] = val
        self._write_env(env)
        os.environ[key] = val   # apply live
        action = "updated" if is_update else "added"
        return f"Sir, {key} {action} in .env and live environment."

    def _delete(self, key: str) -> str:
        env = self._read_env()
        if key not in env:
            return f"Sir, key '{key}' not found in .env."
        del env[key]
        self._write_env(env)
        os.environ.pop(key, None)
        return f"Sir, {key} deleted from .env."

    def _backup(self) -> str:
        if not self.ENV_PATH.exists():
            return "Sir, no .env file found to backup."
        ts     = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest   = Path(f".env.backup_{ts}")
        shutil.copy(self.ENV_PATH, dest)
        return f"Sir, .env backed up to {dest}."

    def _reload(self) -> str:
        env = self._read_env()
        count = 0
        for k, v in env.items():
            os.environ[k] = v
            count += 1
        return f"Sir, {count} variables reloaded into os.environ."

    def _check(self) -> str:
        """Verify all keys have non-empty values."""
        env = self._read_env()
        empty = [k for k, v in env.items() if not v.strip()]
        if empty:
            return (
                f"Sir, {len(empty)} empty variable(s) found:\n"
                + "\n".join(f"  ⚠ {k}" for k in empty)
            )
        return f"Sir, all {len(env)} variables are set and non-empty. .env looks healthy."