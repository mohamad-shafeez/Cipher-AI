import pyautogui

class MediaSkill:
    def __init__(self):
        """
        MediaSkill initializes any required state.
        Currently minimal since pyautogui works statelessly.
        """
        self.triggers = {
            "play": ["play music", "play song", "resume music", "resume playback"],
            "pause": ["pause music", "pause song", "pause playback"],
            "toggle": ["play pause", "toggle music", "toggle playback"],
            "next": ["next track", "next song", "skip song", "skip track"],
            "previous": ["previous track", "previous song", "go back song"]
        }

    def execute(self, command: str) -> str | None:
        """
        Executes media control commands based on user input.

        :param command: str - user voice/text command
        :return: str - response message or None if not a media command
        """
        try:
            if not command:
                return None

            command = command.lower().strip()

            # PLAY
            if any(trigger in command for trigger in self.triggers["play"]):
                pyautogui.press('playpause')
                return "Sir, playing your media."

            # PAUSE
            if any(trigger in command for trigger in self.triggers["pause"]):
                pyautogui.press('playpause')
                return "Sir, pausing your media."

            # TOGGLE (explicit)
            if any(trigger in command for trigger in self.triggers["toggle"]):
                pyautogui.press('playpause')
                return "Sir, toggling playback."

            # NEXT TRACK
            if any(trigger in command for trigger in self.triggers["next"]):
                pyautogui.press('nexttrack')
                return "Sir, skipping to the next track."

            # PREVIOUS TRACK
            if any(trigger in command for trigger in self.triggers["previous"]):
                pyautogui.press('prevtrack')
                return "Sir, going back to the previous track."

            # Not a media command, let the Cipher engine check other skills
            return None

        except Exception as e:
            # Only return an error if we actually tried to execute a media command and failed
            print(f"[MediaSkill Error] {str(e)}")
            return None