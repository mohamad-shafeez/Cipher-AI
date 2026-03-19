# skills/research.py
import wikipedia
import webbrowser
import config

class ResearchSkills:
    def __init__(self):
        wikipedia.set_lang("en")
        print(">> Research Skills: ONLINE")

    # ─────────────────────────────────────────
    # WIKIPEDIA
    # ─────────────────────────────────────────
    def search_wikipedia(self, query):
        try:
            summary = wikipedia.summary(query, sentences=2, auto_suggest=True)
            return f"According to Wikipedia: {summary}"
        except wikipedia.exceptions.DisambiguationError as e:
            # Try the first suggestion automatically
            try:
                summary = wikipedia.summary(e.options[0], sentences=2)
                return f"According to Wikipedia: {summary}"
            except:
                return f"Multiple results found. Did you mean: {', '.join(e.options[:3])}?"
        except wikipedia.exceptions.PageError:
            return f"I couldn't find a Wikipedia page for {query}."
        except Exception as e:
            return f"Wikipedia search failed: {e}"

    # ─────────────────────────────────────────
    # GOOGLE SEARCH
    # ─────────────────────────────────────────
    def search_google(self, query):
        try:
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            webbrowser.open(url)
            return f"Searching Google for {query}."
        except Exception as e:
            return f"Google search failed: {e}"

    # ─────────────────────────────────────────
    # YOUTUBE SEARCH
    # ─────────────────────────────────────────
    def search_youtube(self, query):
        try:
            url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            webbrowser.open(url)
            return f"Searching YouTube for {query}."
        except Exception as e:
            return f"YouTube search failed: {e}"

    # ─────────────────────────────────────────
    # NEWS SEARCH
    # ─────────────────────────────────────────
    def search_news(self, query):
        try:
            url = f"https://news.google.com/search?q={query.replace(' ', '+')}"
            webbrowser.open(url)
            return f"Opening latest news about {query}."
        except Exception as e:
            return f"News search failed: {e}"

    # ─────────────────────────────────────────
    # EXECUTE — VOICE COMMAND ROUTER
    # ─────────────────────────────────────────
    def execute(self, command):
        command = command.lower()

        # Wikipedia triggers
        if any(w in command for w in ["tell me about", "who is", "what is", "explain", "define", "wikipedia"]):
            topic = command
            for phrase in ["tell me about", "who is", "what is", "explain", "define", "wikipedia", "search"]:
                topic = topic.replace(phrase, "")
            topic = topic.strip()
            if topic:
                return self.search_wikipedia(topic)

        # YouTube triggers
        if any(w in command for w in ["youtube", "play", "watch", "video"]):
            query = command
            for phrase in ["search youtube for", "youtube", "play", "watch", "video about", "find video"]:
                query = query.replace(phrase, "")
            query = query.strip()
            if query:
                return self.search_youtube(query)

        # News triggers
        if any(w in command for w in ["news", "latest", "headlines", "current events"]):
            query = command
            for phrase in ["news about", "latest news on", "headlines about", "current events", "news", "latest"]:
                query = query.replace(phrase, "")
            query = query.strip()
            return self.search_news(query if query else "top headlines")

        # Google triggers
        if any(w in command for w in ["search", "google", "look up", "find"]):
            query = command
            for phrase in ["search for", "search google for", "google", "look up", "find"]:
                query = query.replace(phrase, "")
            query = query.strip()
            if query:
                return self.search_google(query)

        return None