#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════╗
║                        HELLO SKILL – ROYAL EDITION                       ║
║  The most advanced, over‑the‑top, personality‑driven greeting system    ║
║  ever written. Supports 6 personalities, live system stats, weather,    ║
║  pending tasks, riddles, motivational AI, and a ghost mode that         ║
║  would make even James Bond jealous.                                    ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import datetime
import random
import os
import sys
import json
import time
import textwrap
import platform
import socket
import subprocess
from collections import deque
from typing import Optional, List, Dict, Any, Tuple

# ----------------------------- optional imports (advanced) -----------------
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ----------------------------- colour & styling ----------------------------
# ANSI escape codes – works on most terminals
class Style:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"

# ----------------------------- configuration --------------------------------
class RoyalConfig:
    """Central configuration – can be overridden by a JSON file."""
    ASSISTANT_NAME = "Cipher"
    USER_NAME = os.getenv("USER", os.getenv("USERNAME", "Commander"))
    ROYAL_TITLE = "Shafeez"          # The name used in royal mode

    # Paths
    TASKS_FILE = "cipher_data/tasks.json"
    HISTORY_FILE = "cipher_data/command_history.json"
    CONFIG_FILE = "cipher_data/royal_config.json"

    # Behaviour
    DEFAULT_PERSONALITY = "royal"     # royal, shakespeare, pirate, tech, casual, dark
    ENABLE_SYSTEM_STATS = True
    ENABLE_WEATHER = False            # Set to True and add API key below
    WEATHER_API_KEY = ""              # OpenWeatherMap key
    WEATHER_CITY = "London"
    ENABLE_ASCII_ART = True
    USE_COLORS = True

    # Response limits
    MAX_HISTORY = 50
    COMMAND_TIMEOUT = 5               # seconds for external calls

    @classmethod
    def load(cls):
        """Load config from JSON if it exists."""
        if os.path.exists(cls.CONFIG_FILE):
            try:
                with open(cls.CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    for key, value in data.items():
                        if hasattr(cls, key):
                            setattr(cls, key, value)
            except Exception:
                pass

    @classmethod
    def save(cls):
        """Save current config to JSON."""
        os.makedirs(os.path.dirname(cls.CONFIG_FILE), exist_ok=True)
        data = {k: v for k, v in cls.__dict__.items()
                if not k.startswith("_") and not callable(v) and k.isupper()}
        with open(cls.CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=2)

RoyalConfig.load()

# ----------------------------- ascii art library ---------------------------
ASCII_ARTS = {
    "welcome": r"""
    ╔══════════════════════════════════════════════════════════════════╗
    ║     ██████╗ ██╗██████╗ ██╗  ██╗███████╗██████╗                  ║
    ║     ██╔══██╗██║██╔══██╗██║  ██║██╔════╝██╔══██╗                  ║
    ║     ██████╔╝██║██████╔╝███████║█████╗  ██████╔╝                  ║
    ║     ██╔═══╝ ██║██╔═══╝ ██╔══██║██╔══╝  ██╔══██╗                  ║
    ║     ██║     ██║██║     ██║  ██║███████╗██║  ██║                  ║
    ║     ╚═╝     ╚═╝╚═╝     ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝                  ║
    ║                   DIGITAL FORTRESS – ROYAL EDITION                ║
    ╚══════════════════════════════════════════════════════════════════╝
    """,
    "goodbye": r"""
    ╔══════════════════════════════════════════════════════════════════╗
    ║          ▄▄▄·  ▄▄▄· ▄▄▄  ▄▄▄ . ▐ ▄ ▄▄▄▄▄▪  ▄▄· ▄▄▄ .            ║
    ║         ▐█ ▀█ ▐█ ▄█▐█ ▀█ ▀▄.▀·•█▌▐█•██  ██ ▐█ ▌▪▀▄.▀·            ║
    ║         ▄█▀▀█ ▐█▀▀█▄█▀▀█ ▐▀▀▪▄▐█▐▐▌ ▐█.▪▐█ ██ ▄▄▐▀▀▪▄            ║
    ║         ▐█ ▪▐▌██▄▪▐█▐█ ▪▐▌▐█▄▄▌██▐█▌ ▐█▌·▐█ ██▌▐▐█▄▄▌            ║
    ║          ▀  ▀ ·▀▀▀▀  ▀  ▀  ▀▀▀ ▀▀ █▪ ▀▀▀  ▀▀▀  ▀  ▀▀▀             ║
    ║                   RETURNING TO THE SHADOWS...                     ║
    ╚══════════════════════════════════════════════════════════════════╝
    """,
    "thinking": r"""
      (•_•)
      <)   )╯
       /   \ 
    """,
}

# ----------------------------- helper functions ----------------------------
def colorize(text: str, color_code: str = Style.WHITE) -> str:
    """Wrap text with ANSI color if enabled."""
    if RoyalConfig.USE_COLORS:
        return f"{color_code}{text}{Style.RESET}"
    return text

def wrap_paragraph(text: str, width: int = 80) -> str:
    """Pretty wrap for long responses."""
    return "\n".join(textwrap.wrap(text, width=width))

def get_system_stats() -> str:
    """Return CPU and RAM usage if psutil is available."""
    if not RoyalConfig.ENABLE_SYSTEM_STATS or not HAS_PSUTIL:
        return ""
    try:
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        return f" [⚙️ CPU {cpu}% | RAM {mem.percent}%]"
    except Exception:
        return ""

def get_network_info() -> str:
    """Get local IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return f" 🌐 {ip}"
    except Exception:
        return ""

def get_weather() -> str:
    """Fetch weather from OpenWeatherMap (optional)."""
    if not RoyalConfig.ENABLE_WEATHER or not HAS_REQUESTS or not RoyalConfig.WEATHER_API_KEY:
        return ""
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={RoyalConfig.WEATHER_CITY}&appid={RoyalConfig.WEATHER_API_KEY}&units=metric"
        resp = requests.get(url, timeout=RoyalConfig.COMMAND_TIMEOUT)
        data = resp.json()
        if resp.status_code == 200:
            temp = data["main"]["temp"]
            desc = data["weather"][0]["description"]
            return f" ☁️ {RoyalConfig.WEATHER_CITY}: {temp}°C, {desc}"
    except Exception:
        pass
    return ""

def get_pending_tasks() -> List[str]:
    """Read tasks from JSON file."""
    tasks_file = RoyalConfig.TASKS_FILE
    if not os.path.exists(tasks_file):
        return []
    try:
        with open(tasks_file, "r") as f:
            data = json.load(f)
            return data.get("pending", [])
    except Exception:
        return []

# ----------------------------- main skill class ----------------------------
class HelloSkill:
    """
    The ultimate greeting and command processor.
    Supports multiple personalities, live data, conversation memory,
    user feedback, and a massive arsenal of responses.
    """

    def __init__(self):
        """Ghost initialization – prints nothing unless in debug mode."""
        self.config = RoyalConfig
        self.name = self.config.ASSISTANT_NAME
        self.user = self.config.USER_NAME
        self.title = self.config.ROYAL_TITLE
        self.personality = self.config.DEFAULT_PERSONALITY

        self.command_history = deque(maxlen=self.config.MAX_HISTORY)
        self.feedback_scores = {}   # command -> avg rating
        self.conversation_context = []

        # Internal response caches
        self._last_greeting_style = None
        self._session_start = datetime.datetime.now()

        # Load history if exists
        self._load_history()
        self._startup_ok = True

    def _load_personality_data(self) -> dict:
        """Loads dialogue from the external JSON core."""
        data_path = "cipher_data/personality.json"
        if os.path.exists(data_path):
            try:
                with open(data_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f">> [Hello] Error loading personality core: {e}")
        return {}

    # ----------------------------- persistence ----------------------------
    def _load_history(self):
        if os.path.exists(self.config.HISTORY_FILE):
            try:
                with open(self.config.HISTORY_FILE, "r") as f:
                    data = json.load(f)
                    self.command_history.extend(data.get("history", []))
            except Exception:
                pass

    def _save_history(self):
        os.makedirs(os.path.dirname(self.config.HISTORY_FILE), exist_ok=True)
        with open(self.config.HISTORY_FILE, "w") as f:
            json.dump({"history": list(self.command_history)}, f, indent=2)

    # ----------------------------- personality switch ---------------------
    def set_personality(self, style: str) -> str:
        """Change the assistant's personality on the fly."""
        valid = ["royal", "shakespeare", "pirate", "tech", "casual", "dark"]
        if style not in valid:
            return f"Invalid personality. Choose from: {', '.join(valid)}"
        self.personality = style
        return f"Personality changed to '{style}'. I shall now address you accordingly."

    # ----------------------------- greeting core --------------------------
    def _get_time_greeting(self) -> Tuple[str, str]:
        """Returns (formal_greeting, time_word) e.g. ('Good morning', 'morning')"""
        hour = datetime.datetime.now().hour
        if hour < 12:
            return "Good morning", "morning"
        elif hour < 18:
            return "Good afternoon", "afternoon"
        else:
            return "Good evening", "evening"

    def _format_greeting(self, template: str) -> str:
        """Inject user, title, time greeting, system stats, tasks, weather."""
        time_greeting, time_word = self._get_time_greeting()
        base = template.format(
            user=self.user,
            title=self.title,
            time_greeting=time_greeting,
            time_word=time_word,
            kernel=platform.release(),
        )
        # Add extra context
        extra = []
        stats = get_system_stats()
        if stats:
            extra.append(stats)
        net = get_network_info()
        if net:
            extra.append(net)
        weather = get_weather()
        if weather:
            extra.append(weather)

        tasks = get_pending_tasks()
        if tasks:
            task_list = ", ".join(tasks[:3])
            count = len(tasks)
            extra.append(f" 📋 {count} pending task{'s' if count != 1 else ''}: {task_list}")

        if extra:
            base += " " + " ".join(extra)

        return base

    def get_royal_greeting(self) -> str:
        """Primary greeting – fetches from personality.json"""
        data = self._load_personality_data()
        greetings_dict = data.get("greetings", {})
        
        # Fallback to royal if personality is missing
        templates = greetings_dict.get(self.personality, greetings_dict.get("royal", ["Hello, Sir."]))
        template = random.choice(templates)
        
        greeting = self._format_greeting(template)

        if self.config.ENABLE_ASCII_ART and self.personality != "tech":
            art = ASCII_ARTS.get("welcome", "")
            greeting = f"{colorize(art, Style.CYAN)}\n{greeting}"

        return colorize(greeting, Style.GREEN)

    # ----------------------------- canned responses -----------------------
    def _get_entertainment_item(self, category: str) -> str:
        """Helper to fetch random dialogue from personality.json"""
        data = self._load_personality_data()
        items = data.get("entertainment", {}).get(category, [])
        return random.choice(items) if items else f"My {category} databanks are empty, {self.title}."

    def tell_joke(self) -> str:
        return colorize(self._get_entertainment_item("jokes"), Style.YELLOW)

    def tell_riddle(self) -> str:
        data = self._load_personality_data()
        riddles = data.get("entertainment", {}).get("riddles", [])
        if riddles:
            riddle = random.choice(riddles)
            self.conversation_context.append(f"riddle_answer:{riddle['a']}")
            return colorize(f"🧩 Riddle: {riddle['q']}\n[Type 'answer' to reveal]", Style.MAGENTA)
        return "I am out of riddles, Sir."

    def reveal_riddle_answer(self, last_riddle_question: str = "") -> str:
        if self.conversation_context and self.conversation_context[-1].startswith("riddle_answer:"):
            answer = self.conversation_context[-1].split(":", 1)[1]
            return colorize(f"The answer is: {answer}", Style.GREEN)
        return "I don't remember asking a riddle recently, Sir."

    def motivate(self) -> str:
        msg = self._get_entertainment_item("motivations")
        return colorize(msg.format(user=self.user, title=self.title), Style.CYAN)

    def fun_fact(self) -> str:
        return colorize(self._get_entertainment_item("facts"), Style.BLUE)

    def compliment(self) -> str:
        msg = self._get_entertainment_item("compliments")
        return colorize(msg.format(user=self.user, title=self.title), Style.MAGENTA)

    def status_report(self) -> str:
        """Full system status report."""
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        uptime = str(datetime.datetime.now() - self._session_start).split('.')[0]
        lines = [
            f"🕒 Time: {now}",
            f"⏱️ Session uptime: {uptime}",
            f"🧠 Personality: {self.personality}",
            f"📜 Command history size: {len(self.command_history)}",
        ]
        if HAS_PSUTIL and self.config.ENABLE_SYSTEM_STATS:
            lines.append(f"💻 CPU: {psutil.cpu_percent()}% | RAM: {psutil.virtual_memory().percent}%")
            lines.append(f"💾 Disk: {psutil.disk_usage('/').percent}% used")
        lines.append(f"🌐 Host: {platform.node()} ({platform.system()} {platform.release()})")
        return colorize("\n".join(lines), Style.CYAN)

    # ----------------------------- command router -------------------------
    def execute(self, command: str) -> Optional[str]:
        """
        Advanced Dispatch Router.
        Replaces massive if/else chains with O(1) dictionary lookups.
        """
        cmd = command.lower().strip()
        self.command_history.append(cmd)
        self._save_history()

        # ----- 1. Complex/Special Commands -----
        if cmd.startswith("personality "):
            return self.set_personality(cmd.split(maxsplit=1)[1])

        if cmd == "answer" and self.conversation_context and "riddle" in self.conversation_context[-1]:
            return self.reveal_riddle_answer()

        # ----- 2. The Smart Dictionary Router -----
        route_map = {
            "joke": self.tell_joke, "funny": self.tell_joke, "laugh": self.tell_joke,
            "riddle": self.tell_riddle,
            "motivate": self.motivate, "inspire": self.motivate, "tired": self.motivate,
            "fact": self.fun_fact,
            "compliment": self.compliment, "praise": self.compliment,
            "status": self.status_report, "report": self.status_report, "stats": self.status_report,
            "help": self.show_help, "commands": self.show_help,
            "bye": self._handle_goodbye, "goodbye": self._handle_goodbye, "dismissed": self._handle_goodbye,
            "hello": self.get_royal_greeting, "wake up": self.get_royal_greeting, "hi": self.get_royal_greeting
        }

        # Scan the input for known trigger words
        for trigger, action_function in route_map.items():
            if trigger in cmd:
                return action_function()

        # ----- 3. Easter Eggs & Fallback -----
        if "42" in cmd or "universe" in cmd:
            return "42, obviously. Now you know the ultimate secret."
        if "sudo" in cmd:
            return "Nice try. But even with sudo, I don't obey that command."
        if "roll dice" in cmd:
            return f"🎲 You rolled a {random.randint(1,6)}."

        # Unknown command: store context and let the main Agent Brain handle it
        self.conversation_context.append(cmd)
        return None

    def _handle_goodbye(self) -> str:
        """Helper for the goodbye routing"""
        msg = f"Understood, {self.title}. Returning to the shadows. Systems standing by."
        if self.config.ENABLE_ASCII_ART:
            return colorize(ASCII_ARTS["goodbye"], Style.RED) + f"\n{msg}"
        return msg

    def show_help(self) -> str:
        """Display available commands with style."""
        help_text = f"""
{Style.BOLD}{Style.CYAN}═════════════════════  COMMAND REFERENCE  ══════════════════════{Style.RESET}

{Style.GREEN}• Greetings{Style.RESET}          hello, hi, hey, wake up, good morning
{Style.GREEN}• Personality{Style.RESET}        personality [royal|shakespeare|pirate|tech|casual|dark]
{Style.GREEN}• Entertainment{Style.RESET}      joke, riddle, answer, fact, compliment
{Style.GREEN}• Motivation{Style.RESET}         motivate, inspiration, i'm tired
{Style.GREEN}• System{Style.RESET}             status, report, stats, how are you
{Style.GREEN}• Goodbye{Style.RESET}            bye, goodbye, exit, dismiss
{Style.GREEN}• Easter eggs{Style.RESET}        'the answer to life the universe and everything', 'roll dice'

{Style.DIM}Tip: I remember your last commands and adapt my style.{Style.RESET}
        """
        return colorize(help_text, Style.WHITE)

# ----------------------------- interactive shell ---------------------------
def main():
    """Run the royal REPL."""
    skill = HelloSkill()

    # Print initial welcome (only once)
    print(colorize(ASCII_ARTS["welcome"], Style.CYAN))
    print(skill.get_royal_greeting())
    print(colorize("\n[Type 'help' for commands or 'bye' to exit]\n", Style.DIM))

    while True:
        try:
            user_input = input(colorize(f"{RoyalConfig.USER_NAME}@fortress:~$ ", Style.GREEN)).strip()
            if not user_input:
                continue
            response = skill.execute(user_input)
            if response:
                print(wrap_paragraph(response))
            else:
                # Polite fallback for unknown commands
                print(colorize(f"I didn't catch that, {skill.title}. Try 'help' for available commands.", Style.YELLOW))
        except KeyboardInterrupt:
            print(colorize("\n\n[Interrupt received. Shutting down gracefully.]", Style.RED))
            break
        except EOFError:
            break

    # Goodbye message
    print(skill.execute("bye"))

if __name__ == "__main__":
    main()