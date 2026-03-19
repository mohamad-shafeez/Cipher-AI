# skills/browser.py
import webbrowser
import config

class BrowserSkills:
    def __init__(self):
        self.sites = {
            "google": "https://www.google.com",
            "youtube": "https://www.youtube.com",
            "github": "https://www.github.com",
            "stack overflow": "https://stackoverflow.com",
            "gmail": "https://mail.google.com"
        }

    def open_website(self, site_name):
        site_name = site_name.lower()
        if site_name in self.sites:
            webbrowser.open(self.sites[site_name])
            return f"Opening {site_name}, sir."
        else:
            url = f"https://www.google.com/search?q={site_name}"
            webbrowser.open(url)
            return f"Searching Google for {site_name}."

    def execute(self, command):
        command = command.lower()
        if any(word in command for word in ["open", "go to", "launch", "visit"]):
            site = command
            for word in ["open", "go to", "launch", "visit"]:
                site = site.replace(word, "").strip()
            if site:
                return self.open_website(site)
        return None