"""
Cipher - System Monitor Skill Module
File: skills/system_monitor.py
Author: Claude (Vision & Systems Module Developer)
Team: Cipher AI Dev Team (Lead: Shafeez | Frontend: DeepSeek | Media: ChatGPT | Systems: Claude)

Responsibility:
    Reports real-time CPU usage, RAM usage, and battery status
    using the psutil library. Returns a conversational string
    to the Cipher core engine.
"""

import psutil


class SystemMonitorSkill:
    """
    Skill module that handles all system health monitoring commands for Cipher.
    Covers CPU, RAM, battery, and combined system info queries.
    """

    TRIGGER_PHRASES = [
        "battery",
        "cpu",
        "ram",
        "memory",
        "system info",
        "system status",
        "how is my system",
        "check system",
        "processor",
        "how much ram",
        "how much memory",
        "is my battery",
        "battery level",
        "battery status",
        "cpu usage",
        "ram usage",
    ]

    def __init__(self):
        """
        Initializes the SystemMonitorSkill.
        Pre-checks whether a battery interface is available on this machine.
        """
        self.has_battery = psutil.sensors_battery() is not None

    def _is_triggered(self, command: str) -> bool:
        command_lower = command.lower().strip()
        return any(phrase in command_lower for phrase in self.TRIGGER_PHRASES)

    def _get_cpu(self) -> str:
        """Returns current CPU usage as a percentage (1-second interval for accuracy)."""
        try:
            cpu = psutil.cpu_percent(interval=1)
            return f"CPU is at {cpu}%"
        except Exception as e:
            return f"CPU data unavailable ({e})"

    def _get_ram(self) -> str:
        """Returns current RAM usage stats."""
        try:
            ram = psutil.virtual_memory()
            used_gb = ram.used / (1024 ** 3)
            total_gb = ram.total / (1024 ** 3)
            return f"RAM is at {ram.percent}% ({used_gb:.1f} GB used of {total_gb:.1f} GB)"
        except Exception as e:
            return f"RAM data unavailable ({e})"

    def _get_battery(self) -> str:
        """Returns battery percentage and charging status."""
        try:
            battery = psutil.sensors_battery()
            if battery is None:
                return "no battery detected — this appears to be a desktop system"
            percent = battery.percent
            plugged = "charging" if battery.power_plugged else "on battery power"
            time_left = ""
            if not battery.power_plugged and battery.secsleft not in (
                psutil.POWER_TIME_UNLIMITED,
                psutil.POWER_TIME_UNKNOWN,
            ):
                mins = int(battery.secsleft / 60)
                hours, remaining_mins = divmod(mins, 60)
                if hours > 0:
                    time_left = f", approximately {hours}h {remaining_mins}m remaining"
                else:
                    time_left = f", approximately {remaining_mins} minutes remaining"
            return f"battery is at {percent:.0f}% and is {plugged}{time_left}"
        except Exception as e:
            return f"battery data unavailable ({e})"

    def _build_response(self, command: str) -> str:
        """
        Determines which metrics to report based on the command content,
        then assembles a natural conversational response.
        """
        command_lower = command.lower()

        wants_cpu = any(w in command_lower for w in ["cpu", "processor", "system info", "system status", "check system", "how is my system"])
        wants_ram = any(w in command_lower for w in ["ram", "memory", "system info", "system status", "check system", "how is my system"])
        wants_battery = any(w in command_lower for w in ["battery", "system info", "system status", "check system", "how is my system"])

        # If none specifically matched (edge case), report everything
        if not any([wants_cpu, wants_ram, wants_battery]):
            wants_cpu = wants_ram = wants_battery = True

        parts = []
        if wants_cpu:
            parts.append(self._get_cpu())
        if wants_ram:
            parts.append(self._get_ram())
        if wants_battery:
            parts.append(self._get_battery())

        if len(parts) == 1:
            return f"Sir, {parts[0]}."
        elif len(parts) == 2:
            return f"Sir, {parts[0]}, and {parts[1]}."
        else:
            return f"Sir, {parts[0]}, {parts[1]}, and {parts[2]}."

    def execute(self, command: str) -> str | None:
        """
        Entry point called by the Cipher core engine.

        Args:
            command (str): The voice/text command from the Cipher engine.

        Returns:
            str | None: Response string if triggered, None to pass to the next skill.
        """
        if not self._is_triggered(command):
            return None

        try:
            return self._build_response(command)
        except Exception as e:
            return f"Sir, I encountered an error while reading system stats: {e}."