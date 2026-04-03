"""
Cipher - Clock Skill Module
File: skills/clock.py
Author: Claude (Vision & Systems Module Developer)
Team: Cipher AI Dev Team (Lead: Shafeez | Frontend: DeepSeek | Media: ChatGPT | Systems: Claude)

Responsibility:
    Reports the current time and/or date using Python's datetime module.
    Returns a clean, conversational string to the Cipher core engine.
"""

from datetime import datetime


class ClockSkill:
    """
    Skill module that handles all time and date queries for Cipher.
    Covers current time, current date, and combined queries.
    """

    TIME_TRIGGERS = [
        "what time is it",
        "current time",
        "what's the time",
        "whats the time",
        "tell me the time",
        "give me the time",
        "time please",
        "the time",
    ]

    DATE_TRIGGERS = [
        "what is the date",
        "what's the date",
        "whats the date",
        "today's date",
        "todays date",
        "current date",
        "what day is it",
        "what day is today",
        "tell me the date",
        "give me the date",
        "the date",
    ]

    BOTH_TRIGGERS = [
        "time and date",
        "date and time",
        "what time and date",
    ]

    def __init__(self):
        """
        Initializes the ClockSkill.
        Flattens all trigger lists for quick membership checks.
        """
        self.all_triggers = self.TIME_TRIGGERS + self.DATE_TRIGGERS + self.BOTH_TRIGGERS

    def _is_triggered(self, command: str) -> bool:
        command_lower = command.lower().strip()
        return any(phrase in command_lower for phrase in self.all_triggers)

    def _wants_time(self, command: str) -> bool:
        command_lower = command.lower()
        return any(phrase in command_lower for phrase in self.TIME_TRIGGERS + self.BOTH_TRIGGERS)

    def _wants_date(self, command: str) -> bool:
        command_lower = command.lower()
        return any(phrase in command_lower for phrase in self.DATE_TRIGGERS + self.BOTH_TRIGGERS)

    def _format_time(self, now: datetime) -> str:
        """
        Formats time as '2:15 PM' with no leading zero on the hour.
        """
        return now.strftime("%-I:%M %p") if hasattr(now, "strftime") else now.strftime("%I:%M %p").lstrip("0")

    def _format_date(self, now: datetime) -> str:
        """
        Formats date as 'Thursday, April 3rd, 2025'.
        Computes the ordinal suffix (st/nd/rd/th) for the day.
        """
        day = now.day
        if 11 <= day <= 13:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")

        return now.strftime(f"%A, %B {day}{suffix}, %Y")

    def _build_response(self, command: str) -> str:
        """
        Builds the appropriate conversational response based on whether
        the user asked for time, date, or both.
        """
        now = datetime.now()
        wants_time = self._wants_time(command)
        wants_date = self._wants_date(command)

        # If somehow neither matched specifically, default to both
        if not wants_time and not wants_date:
            wants_time = wants_date = True

        if wants_time and wants_date:
            return (
                f"Sir, it is currently {self._format_time(now)}, "
                f"and today is {self._format_date(now)}."
            )
        elif wants_time:
            return f"Sir, it is currently {self._format_time(now)}."
        else:
            return f"Sir, today is {self._format_date(now)}."

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
            return f"Sir, I encountered an error while fetching the time or date: {e}."