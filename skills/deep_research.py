# skills/deep_research.py
# ============================================================
#   CIPHER OS — Autonomous Deep Research Skill
#   Phase 5: Knowledge-Gap Detection → Web Scrape → Synthesis
#
#   Flow:
#     1. Triggered by agent planner OR direct voice command
#     2. Admits knowledge gap to user
#     3. Scrapes DuckDuckGo + target pages via BeautifulSoup
#     4. Synthesizes findings via local LLM into a detailed Markdown report
#     5. Saves report to my_research/ vault
#     6. Indexes into VectorMemory for future RAG recall
#     7. Notifies user on completion
#
#   Triggers: "deep research [topic]", "research [topic] in depth",
#             "learn about [topic]", "study [topic]"
# ============================================================

import os
import re
import time
import requests
from pathlib import Path
from datetime import datetime

import config

# ── Paths & Config ────────────────────────────────────────────
BASE_DIR       = Path(__file__).resolve().parent.parent
RESEARCH_DIR   = BASE_DIR / "my_research"
OLLAMA_URL     = f"{config.OLLAMA_BASE_URL}/api/generate"
SYNTH_MODEL    = "qwen2.5-coder:7b"     # Heavy lifter for synthesis
SYNTH_TIMEOUT  = 180                      # 3 min for detailed reports
REQUEST_TIMEOUT = 10
MAX_URLS        = 5                       # Scrape top 5 sites
MAX_CHARS       = 4000                    # Per-page text cap


class DeepResearchSkill:
    """
    Cipher's Autonomous Deep Research Organ.
    Detects knowledge gaps, scrapes the web, synthesizes Markdown reports,
    and stores them permanently in the my_research/ vault for future RAG recall.
    """

    def __init__(self):
        RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
        self._vector_memory = None   # Lazy-loaded reference
        print(">> DeepResearchSkill: ONLINE (Autonomous research pipeline active)")

    # ══════════════════════════════════════════════════════════
    #  TRIGGER DETECTION
    # ══════════════════════════════════════════════════════════

    def execute(self, command: str) -> str | None:
        if not command:
            return None

        cmd = command.lower().strip()

        # ── Direct triggers ───────────────────────────────────
        triggers = [
            "deep research", "research in depth", "in-depth research",
            "autonomous research", "full research",
            "study up on", "learn about", "learn everything about",
            "research and save", "investigate deeply",
        ]

        topic = None
        for t in triggers:
            if t in cmd:
                topic = cmd.replace(t, "").strip()
                break

        # ── Prefix triggers (must start with these) ───────────
        if not topic:
            prefix_triggers = [
                "research ", "study ", "investigate ",
            ]
            for t in prefix_triggers:
                if cmd.startswith(t):
                    # Avoid stealing from ResearchV2's triggers
                    if cmd.startswith("research") and not any(
                        w in cmd for w in ["save", "depth", "deep", "permanent", "vault"]
                    ):
                        continue
                    topic = cmd[len(t):].strip()
                    break

        if not topic:
            return None

        # Remove noise words
        for noise in ["on", "about", "regarding", "for me", "please"]:
            topic = topic.replace(noise, "").strip()

        if len(topic) < 3:
            return "Sir, please provide a more specific topic for deep research."

        return self.run_research(topic)

    # ══════════════════════════════════════════════════════════
    #  CORE RESEARCH PIPELINE
    # ══════════════════════════════════════════════════════════

    def run_research(self, topic: str) -> str:
        """
        Full autonomous research pipeline.
        Called by execute() or directly by the agent planner.
        """
        print(f"\n>> [DeepResearch] ═══════════════════════════════════")
        print(f">> [DeepResearch] Topic: {topic}")
        print(f">> [DeepResearch] ═══════════════════════════════════")

        # ── Step 0: Admit knowledge gap ───────────────────────
        print(f'>> [DeepResearch] Admitting gap: "I don\'t have complete knowledge on this. Initiating research..."')

        # ── Step 1: Web scraping ──────────────────────────────
        print(f">> [DeepResearch] Phase 1: Web scraping via DuckDuckGo...")
        urls = self._ddg_search(topic)
        if not urls:
            return (
                f"Sir, I attempted to research '{topic}' but could not find "
                f"any web results. Please check your internet connection."
            )

        print(f">> [DeepResearch] Found {len(urls)} sources. Extracting content...")
        scraped_sections = []
        sources_used = []
        for url in urls[:MAX_URLS]:
            text = self._scrape_url(url)
            if text and len(text) > 100:
                scraped_sections.append(f"[Source: {url}]\n{text}")
                sources_used.append(url)

        if not scraped_sections:
            return (
                f"Sir, I found URLs for '{topic}' but firewalls prevented "
                f"text extraction. The research could not be completed."
            )

        combined_raw = "\n\n---\n\n".join(scraped_sections)
        print(f">> [DeepResearch] Phase 1 complete: {len(combined_raw)} chars from {len(sources_used)} sources.")

        # ── Step 2: LLM synthesis into Markdown report ────────
        print(f">> [DeepResearch] Phase 2: Synthesizing via {SYNTH_MODEL}...")
        report = self._synthesize_report(topic, combined_raw, sources_used)
        if not report:
            return (
                f"Sir, I scraped the web data for '{topic}' but the neural "
                f"brain failed to synthesize the report."
            )

        # ── Step 3: Save to my_research/ vault ────────────────
        filename = self._topic_to_filename(topic)
        filepath = RESEARCH_DIR / filename
        filepath.write_text(report, encoding="utf-8")
        print(f">> [DeepResearch] Phase 3: Report saved → {filepath}")

        # ── Step 4: Index into VectorMemory for RAG ───────────
        self._index_into_vector_memory(topic, report)
        print(f">> [DeepResearch] Phase 4: Indexed into VectorMemory for future RAG recall.")

        # ── Step 5: Completion ────────────────────────────────
        word_count = len(report.split())
        print(f">> [DeepResearch] ✓ COMPLETE — {word_count} words, {len(sources_used)} sources")

        return (
            f"Sir, I have completed my research on '{topic}' and added it "
            f"to my permanent memory. The report ({word_count} words from "
            f"{len(sources_used)} sources) has been saved to "
            f"my_research/{filename}. I can now answer questions about this "
            f"topic from memory."
        )

    # ══════════════════════════════════════════════════════════
    #  WEB SCRAPING
    # ══════════════════════════════════════════════════════════

    def _ddg_search(self, query: str) -> list[str]:
        """Search DuckDuckGo for URLs related to the topic."""
        try:
            from duckduckgo_search import DDGS
            urls = []
            with DDGS() as ddgs:
                results = ddgs.text(query, max_results=MAX_URLS + 3)
                for r in results:
                    href = r.get("href") or r.get("url", "")
                    if href and href.startswith("http"):
                        urls.append(href)
                    if len(urls) >= MAX_URLS:
                        break
            return urls
        except ImportError:
            print(">> [DeepResearch] ERROR: duckduckgo_search not installed.")
            return []
        except Exception as e:
            print(f">> [DeepResearch] DDG search error: {e}")
            return []

    def _scrape_url(self, url: str) -> str | None:
        """Scrape a single URL and extract paragraph text."""
        try:
            from bs4 import BeautifulSoup

            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                )
            }
            resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "html.parser")
            # Remove non-content elements
            for tag in soup(["script", "style", "nav", "footer", "header",
                             "aside", "form", "button", "iframe"]):
                tag.decompose()

            # Extract paragraph text
            paragraphs = soup.find_all("p")
            text = " ".join(
                p.get_text(separator=" ", strip=True) for p in paragraphs
            )
            text = re.sub(r'\s+', ' ', text).strip()
            return text[:MAX_CHARS] if text else None

        except Exception as e:
            print(f">> [DeepResearch] Scrape failed for {url[:60]}: {e}")
            return None

    # ══════════════════════════════════════════════════════════
    #  LLM SYNTHESIS
    # ══════════════════════════════════════════════════════════

    def _synthesize_report(self, topic: str, raw_data: str,
                           sources: list[str]) -> str | None:
        """
        Feed scraped data to the local LLM and generate a comprehensive
        Markdown research report.
        """
        sources_block = "\n".join(f"- {url}" for url in sources)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        prompt = f"""You are Cipher's Deep Research Engine. You have been given raw web data about a topic.
Your job is to synthesize this into a comprehensive, well-structured Markdown research report.

TOPIC: {topic}

RAW WEB DATA:
{raw_data}

REPORT REQUIREMENTS:
1. Start with a top-level heading: # Research Report: {topic}
2. Add metadata: Date, Sources count, Status: Complete
3. Include these sections with ## headings:
   - Overview (2-3 paragraph executive summary)
   - Key Concepts (bullet points of the most important ideas)
   - Detailed Analysis (the deep dive — multiple paragraphs)
   - Technical Details (if applicable — specific data, numbers, processes)
   - Common Misconceptions (if any)
   - Practical Applications (real-world uses)
   - Further Reading (suggest related topics)
4. End with a Sources section listing all URLs
5. Write in a scholarly but accessible tone
6. Be FACTUAL — only use information from the provided web data
7. Do NOT add markdown code fences around the report
8. Minimum 500 words

Generate the complete Markdown report now:"""

        try:
            resp = requests.post(
                OLLAMA_URL,
                json={
                    "model": SYNTH_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "keep_alive": "5m",
                    "options": {
                        "num_predict": 4096,
                        "temperature": 0.3,
                        "top_p": 0.8,
                    }
                },
                timeout=SYNTH_TIMEOUT,
            )

            if resp.status_code != 200:
                print(f">> [DeepResearch] LLM error: HTTP {resp.status_code}")
                return None

            report = resp.json().get("response", "").strip()
            if not report:
                return None

            # Strip code fences if the model wraps them
            if report.startswith("```"):
                report = re.sub(r'^```\w*\n?', '', report)
                report = re.sub(r'\n?```$', '', report)

            # Append sources footer if not already present
            if "## Sources" not in report and "## References" not in report:
                report += f"\n\n---\n\n## Sources\n\n{sources_block}"

            # Append generation metadata
            report += (
                f"\n\n---\n\n*Generated by Cipher OS Deep Research Engine on "
                f"{timestamp}. Synthesized from {len(sources)} web sources.*\n"
            )

            return report

        except requests.exceptions.Timeout:
            print(f">> [DeepResearch] LLM synthesis timed out after {SYNTH_TIMEOUT}s")
            return None
        except Exception as e:
            print(f">> [DeepResearch] Synthesis error: {e}")
            return None

    # ══════════════════════════════════════════════════════════
    #  VECTOR MEMORY INTEGRATION (RAG)
    # ══════════════════════════════════════════════════════════

    def _index_into_vector_memory(self, topic: str, report: str):
        """
        Save the research report into VectorMemory's knowledge table
        so future queries about this topic get instant RAG recall.
        """
        try:
            import sqlite3
            db_path = os.path.join(BASE_DIR, "cipher_data", "memory.db")
            conn = sqlite3.connect(db_path)

            # Store in chunks for better retrieval granularity
            chunks = self._chunk_report(report)
            timestamp = datetime.now().isoformat()

            for i, chunk in enumerate(chunks):
                conn.execute(
                    "INSERT INTO knowledge (topic, content, timestamp) VALUES (?, ?, ?)",
                    (
                        f"research:{topic}",
                        f"[Deep Research: {topic}] {chunk}",
                        timestamp,
                    )
                )

            conn.commit()
            conn.close()
            print(f">> [DeepResearch] Indexed {len(chunks)} knowledge chunks into VectorMemory.")

        except Exception as e:
            print(f">> [DeepResearch] VectorMemory indexing failed: {e}")

    def _chunk_report(self, report: str, chunk_size: int = 800) -> list[str]:
        """
        Split report into overlapping chunks for better semantic retrieval.
        Splits on section boundaries (##) first, then by size.
        """
        # Split on ## headings first
        sections = re.split(r'\n(?=## )', report)
        chunks = []

        for section in sections:
            section = section.strip()
            if not section:
                continue
            if len(section) <= chunk_size:
                chunks.append(section)
            else:
                # Split long sections into size-limited chunks
                words = section.split()
                current = []
                current_len = 0
                for word in words:
                    current.append(word)
                    current_len += len(word) + 1
                    if current_len >= chunk_size:
                        chunks.append(" ".join(current))
                        current = []
                        current_len = 0
                if current:
                    chunks.append(" ".join(current))

        return chunks

    # ══════════════════════════════════════════════════════════
    #  UTILITIES
    # ══════════════════════════════════════════════════════════

    def _topic_to_filename(self, topic: str) -> str:
        """Convert a topic string to a safe markdown filename."""
        # Sanitize: lowercase, replace spaces/special chars with underscores
        safe = re.sub(r'[^\w\s-]', '', topic.lower())
        safe = re.sub(r'[\s-]+', '_', safe).strip('_')
        # Truncate to reasonable length
        safe = safe[:60]
        return f"{safe}_research.md"
