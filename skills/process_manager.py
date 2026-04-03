# skills/process_manager.py
# ============================================================
#   CIPHER PROCESS MANAGER
#   Voice-controlled process management via psutil.
#
#   Triggers:
#     "kill chrome"          → kill process by name
#     "kill pid 4821"        → kill by PID
#     "restart flask"        → kill then relaunch
#     "list processes"       → top 15 by CPU
#     "find process python"  → search by name
#     "process info chrome"  → detailed info
#     "top processes"        → top CPU consumers
#     "memory hogs"          → top RAM consumers
# ============================================================

import psutil
import subprocess
import os
import signal
import platform


class ProcessManagerSkill:

    TRIGGERS = [
        "kill ", "restart ", "list processes", "find process",
        "process info", "top processes", "memory hogs",
        "stop process", "terminate ",
    ]

    def execute(self, command: str) -> str | None:
        cmd = command.lower().strip()

        if not any(t in cmd for t in self.TRIGGERS):
            return None

        if cmd.startswith("kill pid "):
            return self._kill_pid(cmd.replace("kill pid ", "").strip())

        if cmd.startswith("kill ") or cmd.startswith("terminate "):
            name = cmd.replace("kill ", "").replace("terminate ", "").strip()
            return self._kill_name(name)

        if cmd.startswith("restart "):
            name = cmd.replace("restart ", "").strip()
            return self._restart(name)

        if "list processes" in cmd:
            return self._list()

        if cmd.startswith("find process "):
            name = cmd.replace("find process ", "").strip()
            return self._find(name)

        if cmd.startswith("process info "):
            name = cmd.replace("process info ", "").strip()
            return self._info(name)

        if "top processes" in cmd:
            return self._top_cpu()

        if "memory hogs" in cmd:
            return self._top_mem()

        return None

    # ------------------------------------------------------------------ #

    def _kill_pid(self, pid_str: str) -> str:
        try:
            pid = int(pid_str)
            p   = psutil.Process(pid)
            name = p.name()
            p.kill()
            return f"Sir, process '{name}' (PID {pid}) has been terminated."
        except psutil.NoSuchProcess:
            return f"Sir, PID {pid_str} not found."
        except psutil.AccessDenied:
            return f"Sir, access denied to kill PID {pid_str}. Try running as admin."
        except Exception as e:
            return f"Sir, error: {e}"

    def _kill_name(self, name: str) -> str:
        killed = []
        for p in psutil.process_iter(['pid', 'name']):
            if name.lower() in p.info['name'].lower():
                try:
                    p.kill()
                    killed.append(f"{p.info['name']} (PID {p.info['pid']})")
                except Exception:
                    pass
        if killed:
            return f"Sir, terminated: {', '.join(killed)}"
        return f"Sir, no process matching '{name}' found."

    def _restart(self, name: str) -> str:
        # Find command line of the process before killing
        cmd_args = None
        for p in psutil.process_iter(['pid', 'name', 'cmdline']):
            if name.lower() in p.info['name'].lower():
                cmd_args = p.info.get('cmdline')
                try:
                    p.kill()
                except Exception:
                    pass
                break

        if not cmd_args:
            return f"Sir, process '{name}' not found to restart."

        try:
            subprocess.Popen(cmd_args, shell=False)
            return f"Sir, '{name}' has been restarted."
        except Exception as e:
            return f"Sir, killed '{name}' but could not relaunch: {e}"

    def _list(self) -> str:
        procs = sorted(
            psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']),
            key=lambda p: p.info.get('cpu_percent') or 0,
            reverse=True
        )[:15]
        lines = ["Sir, top 15 processes by CPU:\n"]
        lines.append(f"  {'PID':>6}  {'CPU%':>5}  {'MEM%':>5}  NAME")
        lines.append("  " + "-" * 40)
        for p in procs:
            lines.append(
                f"  {p.info['pid']:>6}  "
                f"{(p.info.get('cpu_percent') or 0):>5.1f}  "
                f"{(p.info.get('memory_percent') or 0):>5.1f}  "
                f"{p.info['name']}"
            )
        return "\n".join(lines)

    def _find(self, name: str) -> str:
        found = []
        for p in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent']):
            if name.lower() in p.info['name'].lower():
                found.append(
                    f"  PID {p.info['pid']} — {p.info['name']} "
                    f"[{p.info['status']}] CPU: {p.info['cpu_percent']}%"
                )
        if found:
            return f"Sir, found {len(found)} match(es) for '{name}':\n" + "\n".join(found)
        return f"Sir, no running process matches '{name}'."

    def _info(self, name: str) -> str:
        for p in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent',
                                       'memory_info', 'create_time', 'cmdline']):
            if name.lower() in p.info['name'].lower():
                import datetime
                mem_mb = (p.info.get('memory_info') or psutil._common.pmem(0,0)).rss / 1024 / 1024
                started = datetime.datetime.fromtimestamp(
                    p.info.get('create_time') or 0
                ).strftime('%H:%M:%S')
                cmdline = " ".join(p.info.get('cmdline') or [])[:80]
                return (
                    f"Sir, process info for '{name}':\n"
                    f"  PID      : {p.info['pid']}\n"
                    f"  Name     : {p.info['name']}\n"
                    f"  Status   : {p.info['status']}\n"
                    f"  CPU      : {p.info['cpu_percent']}%\n"
                    f"  RAM      : {mem_mb:.1f} MB\n"
                    f"  Started  : {started}\n"
                    f"  Command  : {cmdline}"
                )
        return f"Sir, no process '{name}' found."

    def _top_cpu(self) -> str:
        procs = sorted(
            psutil.process_iter(['pid', 'name', 'cpu_percent']),
            key=lambda p: p.info.get('cpu_percent') or 0,
            reverse=True
        )[:8]
        lines = ["Sir, top CPU consumers:"]
        for p in procs:
            lines.append(f"  {p.info['cpu_percent']:>5.1f}%  {p.info['name']} (PID {p.info['pid']})")
        return "\n".join(lines)

    def _top_mem(self) -> str:
        procs = sorted(
            psutil.process_iter(['pid', 'name', 'memory_percent']),
            key=lambda p: p.info.get('memory_percent') or 0,
            reverse=True
        )[:8]
        lines = ["Sir, top RAM consumers:"]
        for p in procs:
            pct = p.info.get('memory_percent') or 0
            lines.append(f"  {pct:>5.1f}%  {p.info['name']} (PID {p.info['pid']})")
        return "\n".join(lines)