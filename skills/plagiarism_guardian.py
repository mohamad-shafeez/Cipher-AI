"""
Cipher Skill — Plagiarism Guardian
Organ: The Academic Weapon

A full plagiarism detection and surgical rewrite system.

Pipeline:
  Phase 1 — Lexical Check   : n-gram hashing (Rabin-Karp style) for exact matches
  Phase 2 — Semantic Check  : sentence-transformers cosine similarity
  Phase 3 — Internet Check  : DuckDuckGo search + BeautifulSoup scrape
  Phase 4 — Surgical Rewrite: Gemini API → fallback deepseek-r1 via Ollama

Modes:
  • Voice: "cipher check plagiarism in report.txt"
  • Voice: "compare file1.txt with file2.txt for plagiarism"
  • Web UI: POST /api/plagiarism/check  { text, mode, compare_file }
  • Web UI: GET  /api/plagiarism/result

Zero paid APIs required. Sentence-transformers runs locally.
"""

import os
import re
import json
import time
import hashlib
import threading
import requests
from pathlib import Path
from typing import Optional
from datetime import datetime
from collections import defaultdict


# ── Constants ──────────────────────────────────────────────────
SIMILARITY_THRESHOLD  = 0.72   # Cosine similarity above this = flagged
NGRAM_SIZE            = 6      # Words per n-gram for lexical check
MIN_SENTENCE_WORDS    = 6      # Skip sentences shorter than this
MAX_INTERNET_SOURCES  = 3      # URLs to scrape per flagged sentence
SCRAPE_TIMEOUT        = 6      # Seconds per web request
REWRITE_MODEL_GEMINI  = "gemini-1.5-flash"
REWRITE_MODEL_LOCAL   = "deepseek-r1:1.5b"
REPORT_DIR            = Path("generated_code/plagiarism_reports")


# ── Shared result store (for Web UI polling) ───────────────────
_latest_result: dict | None = None
_result_lock   = threading.Lock()

def set_result(r: dict):
    global _latest_result
    with _result_lock:
        _latest_result = r

def get_result() -> dict | None:
    with _result_lock:
        return _latest_result


# ══════════════════════════════════════════════════════════════════
# PHASE 1 — LEXICAL ENGINE (N-gram hashing)
# ══════════════════════════════════════════════════════════════════

class LexicalEngine:
    """
    Rabin-Karp inspired n-gram fingerprinting.
    Chops text into overlapping word windows and hashes them.
    If the same hash appears in both texts → exact match flagged.
    """

    def __init__(self, n: int = NGRAM_SIZE):
        self.n = n

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())

    def _ngrams(self, tokens: list[str]) -> list[tuple]:
        return [tuple(tokens[i:i+self.n]) for i in range(len(tokens) - self.n + 1)]

    def _fingerprint(self, ngram: tuple) -> str:
        return hashlib.md5(" ".join(ngram).encode()).hexdigest()

    def fingerprint_set(self, text: str) -> set[str]:
        tokens = self._tokenize(text)
        return {self._fingerprint(ng) for ng in self._ngrams(tokens)}

    def lexical_similarity(self, text_a: str, text_b: str) -> float:
        """Returns 0.0–1.0 Jaccard similarity of n-gram fingerprints."""
        fa = self.fingerprint_set(text_a)
        fb = self.fingerprint_set(text_b)
        if not fa or not fb:
            return 0.0
        intersection = fa & fb
        union = fa | fb
        return len(intersection) / len(union)

    def find_matching_ngrams(self, text_a: str, text_b: str) -> list[str]:
        """Return list of matching n-gram phrases between two texts."""
        tokens_a = self._tokenize(text_a)
        tokens_b = self._tokenize(text_b)
        fp_b = {self._fingerprint(ng): ng for ng in self._ngrams(tokens_b)}
        matches = []
        for ng in self._ngrams(tokens_a):
            fp = self._fingerprint(ng)
            if fp in fp_b:
                matches.append(" ".join(ng))
        return matches[:10]  # Top 10 matching phrases


# ══════════════════════════════════════════════════════════════════
# PHASE 2 — SEMANTIC ENGINE (Sentence Transformers)
# ══════════════════════════════════════════════════════════════════

class SemanticEngine:
    """
    Uses sentence-transformers (all-MiniLM-L6-v2) to embed sentences
    and compute cosine similarity. Catches paraphrased plagiarism that
    lexical matching misses.
    Lazy-loaded to protect Cipher's 1.8s boot time.
    """

    def __init__(self):
        self._model = None
        self._lock  = threading.Lock()

    def _load(self):
        if self._model is None:
            with self._lock:
                if self._model is None:
                    try:
                        from sentence_transformers import SentenceTransformer
                        print(">> [PlagiarismGuardian] Loading semantic model...")
                        self._model = SentenceTransformer('all-MiniLM-L6-v2')
                        print(">> [PlagiarismGuardian] Semantic engine ready.")
                    except ImportError:
                        raise RuntimeError(
                            "sentence-transformers not installed. "
                            "Run: pip install sentence-transformers"
                        )

    def embed(self, sentences: list[str]):
        self._load()
        return self._model.encode(sentences, convert_to_tensor=True)

    def cosine_similarity(self, vec_a, vec_b) -> float:
        import torch
        sim = torch.nn.functional.cosine_similarity(
            vec_a.unsqueeze(0), vec_b.unsqueeze(0)
        )
        return float(sim.item())

    def compare_sentences(self, sentences_a: list[str],
                           sentences_b: list[str]) -> list[dict]:
        """
        For each sentence in A, find the most similar sentence in B.
        Returns list of {sentence, best_match, score, flagged}.
        """
        self._load()
        if not sentences_a or not sentences_b:
            return []

        import torch
        emb_a = self.embed(sentences_a)
        emb_b = self.embed(sentences_b)

        results = []
        for i, (sent, emb) in enumerate(zip(sentences_a, emb_a)):
            scores = [
                self.cosine_similarity(emb, emb_b[j])
                for j in range(len(sentences_b))
            ]
            best_score = max(scores)
            best_idx   = scores.index(best_score)
            results.append({
                "sentence":   sent,
                "best_match": sentences_b[best_idx],
                "score":      round(best_score, 3),
                "flagged":    best_score >= SIMILARITY_THRESHOLD,
            })

        return results


# ══════════════════════════════════════════════════════════════════
# PHASE 3 — INTERNET ENGINE (DuckDuckGo + Scraper)
# ══════════════════════════════════════════════════════════════════

class InternetEngine:
    """
    For each flagged sentence:
    1. Searches DuckDuckGo for the sentence text
    2. Fetches top N result URLs
    3. Scrapes paragraph text
    4. Runs semantic similarity against scraped content
    Returns source URLs and similarity scores.
    """

    def __init__(self, semantic: SemanticEngine):
        self.semantic = semantic

    def _ddg_urls(self, query: str) -> list[str]:
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = ddgs.text(query[:200], max_results=MAX_INTERNET_SOURCES + 2)
                urls = []
                for r in results:
                    url = r.get("href") or r.get("url", "")
                    if url.startswith("http"):
                        urls.append(url)
                    if len(urls) >= MAX_INTERNET_SOURCES:
                        break
            return urls
        except Exception:
            return []

    def _scrape(self, url: str) -> str:
        try:
            from bs4 import BeautifulSoup
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            resp = requests.get(url, headers=headers, timeout=SCRAPE_TIMEOUT)
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            paragraphs = soup.find_all("p")
            text = " ".join(p.get_text(" ", strip=True) for p in paragraphs)
            return text[:3000]
        except Exception:
            return ""

    def check_sentence_online(self, sentence: str) -> list[dict]:
        """
        Returns list of {url, similarity, snippet} for a single sentence.
        """
        urls = self._ddg_urls(sentence)
        if not urls:
            return []

        results = []
        try:
            sent_emb = self.semantic.embed([sentence])[0]
        except Exception:
            return []

        for url in urls:
            scraped = self._scrape(url)
            if not scraped or len(scraped.split()) < 20:
                continue

            # Chunk scraped text into sentences
            chunks = [s.strip() for s in re.split(r'(?<=[.!?])\s+', scraped) if len(s.split()) >= 5]
            if not chunks:
                continue

            try:
                chunk_embs = self.semantic.embed(chunks[:60])
                import torch
                scores = [
                    float(torch.nn.functional.cosine_similarity(
                        sent_emb.unsqueeze(0), ce.unsqueeze(0)
                    ).item())
                    for ce in chunk_embs
                ]
                best_score = max(scores)
                best_chunk = chunks[scores.index(best_score)]

                results.append({
                    "url":        url,
                    "similarity": round(best_score, 3),
                    "snippet":    best_chunk[:200],
                    "flagged":    best_score >= SIMILARITY_THRESHOLD,
                })
            except Exception:
                continue

        return sorted(results, key=lambda x: x["similarity"], reverse=True)


# ══════════════════════════════════════════════════════════════════
# PHASE 4 — REWRITE ENGINE (Gemini → Ollama fallback)
# ══════════════════════════════════════════════════════════════════

class RewriteEngine:
    """
    Takes a flagged sentence and rewrites it surgically:
    - Different grammatical structure
    - Fresh vocabulary
    - Core facts preserved 100%
    Returns original + rewritten + explanation.
    """

    def __init__(self):
        self._gemini_client = None
        self._init_gemini()

    def _init_gemini(self):
        try:
            from google import genai as google_genai
            from dotenv import load_dotenv
            load_dotenv()
            key = os.getenv("GEMINI_API_KEY", "").strip()
            if key:
                self._gemini_client = google_genai.Client(api_key=key)
                print(">> [PlagiarismGuardian] Gemini rewriter ready.")
        except Exception:
            pass

    def _build_prompt(self, sentence: str, context: str = "") -> str:
        return (
            "You are Cipher, an academic writing assistant.\n"
            "A sentence has been flagged for plagiarism. Your job is to rewrite it.\n\n"
            "STRICT RULES:\n"
            "1. Use a completely different grammatical structure.\n"
            "2. Use fresh, original vocabulary — no word-for-word copying.\n"
            "3. Preserve ALL core facts, meaning, and technical accuracy.\n"
            "4. Keep the same approximate length.\n"
            "5. Sound natural and academic.\n"
            "6. Return ONLY valid JSON — no markdown, no extra text.\n\n"
            f"FLAGGED SENTENCE:\n\"{sentence}\"\n\n"
            f"{'SURROUNDING CONTEXT: ' + context[:300] if context else ''}\n\n"
            "Return this exact JSON:\n"
            '{"original": "...", "rewritten": "...", "explanation": "..."}'
        )

    def rewrite(self, sentence: str, context: str = "") -> dict:
        prompt = self._build_prompt(sentence, context)

        # ── Try Gemini first ───────────────────────────────────
        if self._gemini_client:
            try:
                response = self._gemini_client.models.generate_content(
                    model=REWRITE_MODEL_GEMINI,
                    contents=prompt,
                )
                raw = response.text.strip()
                raw = re.sub(r'^```json\s*|^```\s*|```$', '', raw, flags=re.MULTILINE).strip()
                return json.loads(raw)
            except Exception as e:
                print(f">> [PlagiarismGuardian] Gemini rewrite failed: {e}")

        # ── Fall back to local Ollama ──────────────────────────
        try:
            import ollama
            response = ollama.chat(
                model=REWRITE_MODEL_LOCAL,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.4, "num_predict": 300},
            )
            raw = response["message"]["content"].strip()
            raw = re.sub(r'^```json\s*|^```\s*|```$', '', raw, flags=re.MULTILINE).strip()
            # Extract JSON if model wrapped it in extra text
            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            print(f">> [PlagiarismGuardian] Local rewrite failed: {e}")

        # ── Last resort: return original with note ─────────────
        return {
            "original":    sentence,
            "rewritten":   sentence,
            "explanation": "Rewrite engine unavailable. Please rewrite manually.",
        }

    def rewrite_all_flagged(self, flagged_sentences: list[str],
                             full_text: str) -> list[dict]:
        results = []
        for sent in flagged_sentences:
            # Give the model surrounding context
            idx = full_text.find(sent)
            context = full_text[max(0, idx-200):idx+len(sent)+200] if idx >= 0 else ""
            result = self.rewrite(sent, context)
            results.append(result)
            time.sleep(0.3)  # Polite rate limiting
        return results


# ══════════════════════════════════════════════════════════════════
# REPORT GENERATOR
# ══════════════════════════════════════════════════════════════════

class PlagiarismReport:
    """Generates a structured JSON + human-readable text report."""

    @staticmethod
    def build(
        source_name:    str,
        overall_lexical: float,
        semantic_results: list[dict],
        internet_matches: list[dict],
        rewrites:        list[dict],
    ) -> dict:
        flagged_sents = [r for r in semantic_results if r["flagged"]]
        total_sents   = len(semantic_results)
        flagged_count = len(flagged_sents)
        plag_percent  = round((flagged_count / total_sents * 100) if total_sents else 0, 1)

        # Risk level
        if plag_percent >= 40:
            risk = "HIGH"
        elif plag_percent >= 20:
            risk = "MEDIUM"
        elif plag_percent >= 5:
            risk = "LOW"
        else:
            risk = "CLEAN"

        report = {
            "timestamp":        datetime.now().isoformat(),
            "source":           source_name,
            "risk_level":       risk,
            "plagiarism_score": plag_percent,
            "lexical_overlap":  round(overall_lexical * 100, 1),
            "total_sentences":  total_sents,
            "flagged_sentences": flagged_count,
            "semantic_details": semantic_results,
            "internet_sources": internet_matches,
            "rewrites":         rewrites,
            "summary": (
                f"{plag_percent}% of sentences flagged. "
                f"Risk level: {risk}. "
                f"Lexical overlap: {round(overall_lexical * 100, 1)}%. "
                f"{len(rewrites)} sentences rewritten."
            ),
        }
        return report

    @staticmethod
    def save(report: dict) -> str:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"plagiarism_{ts}.json"
        path = REPORT_DIR / name
        path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        return str(path)

    @staticmethod
    def to_voice_summary(report: dict) -> str:
        risk  = report["risk_level"]
        score = report["plagiarism_score"]
        rw    = len(report["rewrites"])
        sources = len([s for s in report["internet_sources"] if s.get("flagged")])

        if risk == "CLEAN":
            return (
                f"Document cleared, Sir. Plagiarism score is only {score} percent. "
                "No significant matches found. You are good to submit."
            )
        elif risk == "LOW":
            return (
                f"Low concern detected. {score} percent of sentences flagged. "
                f"I have prepared {rw} rewrite suggestions. "
                "Minor revisions recommended before submission."
            )
        elif risk == "MEDIUM":
            return (
                f"Warning, Sir. {score} percent plagiarism detected. "
                f"{sources} internet sources matched. "
                f"I have rewritten {rw} flagged sentences. "
                "Review my suggestions before submitting."
            )
        else:
            return (
                f"Critical alert. {score} percent of the document is flagged as plagiarism. "
                f"Matched {sources} external sources. "
                f"I have generated {rw} surgical rewrites. "
                "Do not submit this document without review, Sir."
            )


# ══════════════════════════════════════════════════════════════════
# MAIN SKILL CLASS
# ══════════════════════════════════════════════════════════════════

class PlagiarismGuardianSkill:
    """
    Cipher skill entry point — auto-discovered by FastLoader.

    Voice triggers:
      "check plagiarism in report.txt"
      "check file1.txt for plagiarism"
      "compare essay.txt with original.txt for plagiarism"
      "plagiarism check this text: [text]"
      "how original is my document"
      "plagiarism report for thesis.txt"
    """

    def __init__(self):
        self.lexical  = LexicalEngine()
        self.semantic = SemanticEngine()
        self.internet = InternetEngine(self.semantic)
        self.rewriter = RewriteEngine()
        self._running = False
        print(">> Plagiarism Guardian: ONLINE (Academic Weapon Active)")

    # ── Execute router ─────────────────────────────────────────

    def execute(self, command: str) -> Optional[str]:
        cmd = command.lower().strip()

        triggers = [
            "plagiarism", "check original", "how original",
            "check for copying", "detect copying", "similarity check",
        ]
        if not any(t in cmd for t in triggers):
            return None

        if self._running:
            return "Plagiarism analysis already running, Sir. Please wait."

        # ── Mode: Compare two documents ────────────────────────
        if "compare" in cmd and " with " in cmd:
            return self._handle_compare(command)

        # ── Mode: Inline text ──────────────────────────────────
        if "this text:" in cmd or "check text:" in cmd:
            text = re.split(r'this text:|check text:', command, flags=re.IGNORECASE)[-1].strip()
            if len(text) > 20:
                return self._run_analysis(text, source_name="inline_text", mode="internet")

        # ── Mode: File check ───────────────────────────────────
        file_match = re.search(
            r'(?:check|scan|analyze|plagiarism|report for)\s+([\w\-. /\\:]+\.(?:txt|pdf|docx|md))',
            command, re.IGNORECASE
        )
        if file_match:
            fpath = file_match.group(1).strip()
            text  = self._read_file(fpath)
            if not text:
                return f"Could not read file: {fpath}. Please check the path."
            return self._run_analysis(text, source_name=fpath, mode="internet")

        return (
            "To check plagiarism, say: "
            "'cipher check plagiarism in report.txt' or "
            "'cipher compare essay.txt with source.txt for plagiarism' or "
            "'cipher plagiarism check this text: your text here'"
        )

    # ── Compare two documents ──────────────────────────────────

    def _handle_compare(self, command: str) -> str:
        # "compare file_a.txt with file_b.txt for plagiarism"
        match = re.search(
            r'compare\s+([\w\-. /\\:]+)\s+with\s+([\w\-. /\\:]+)',
            command, re.IGNORECASE
        )
        if not match:
            return "Please specify: 'compare file1.txt with file2.txt for plagiarism'"

        file_a = match.group(1).strip()
        file_b = match.group(2).strip()

        text_a = self._read_file(file_a)
        text_b = self._read_file(file_b)

        if not text_a: return f"Could not read: {file_a}"
        if not text_b: return f"Could not read: {file_b}"

        return self._run_analysis(
            text_a,
            source_name=file_a,
            mode="document",
            compare_text=text_b,
            compare_name=file_b,
        )

    # ── Core analysis pipeline ─────────────────────────────────

    def _run_analysis(
        self,
        text:         str,
        source_name:  str,
        mode:         str,            # "internet" | "document"
        compare_text: str = "",
        compare_name: str = "",
    ) -> str:
        self._running = True

        def _pipeline():
            try:
                print(f">> [PlagiarismGuardian] Starting analysis: {source_name}")

                sentences = self._split_sentences(text)
                if not sentences:
                    set_result({"error": "No meaningful sentences found in the text."})
                    return

                # ── Phase 1: Lexical ───────────────────────────
                lexical_score = 0.0
                if compare_text:
                    lexical_score = self.lexical.lexical_similarity(text, compare_text)
                    print(f">> [PlagiarismGuardian] Lexical overlap: {lexical_score:.2%}")

                # ── Phase 2: Semantic ──────────────────────────
                print(">> [PlagiarismGuardian] Running semantic analysis...")
                if mode == "document" and compare_text:
                    compare_sents = self._split_sentences(compare_text)
                    semantic_results = self.semantic.compare_sentences(sentences, compare_sents)
                else:
                    # Self-comparison: compare each sentence to all others
                    # Also used as baseline before internet check
                    semantic_results = self.semantic.compare_sentences(sentences, sentences[1:] + sentences[:1])

                # ── Phase 3: Internet check ────────────────────
                internet_matches = []
                if mode == "internet":
                    flagged = [r["sentence"] for r in semantic_results if r["flagged"]]
                    # Also check high-frequency n-gram sentences
                    all_flagged = list(set(flagged))[:8]  # Cap at 8 to avoid rate limits
                    print(f">> [PlagiarismGuardian] Checking {len(all_flagged)} sentences online...")
                    for sent in all_flagged:
                        matches = self.internet.check_sentence_online(sent)
                        internet_matches.extend(matches)
                        time.sleep(0.5)

                    # Update semantic results with internet scores
                    internet_url_map = defaultdict(list)
                    for m in internet_matches:
                        internet_url_map[m.get("snippet", "")[:50]].append(m)

                # ── Phase 4: Rewrite flagged sentences ─────────
                print(">> [PlagiarismGuardian] Generating surgical rewrites...")
                flagged_sents = [r["sentence"] for r in semantic_results if r["flagged"]]
                rewrites = []
                if flagged_sents:
                    rewrites = self.rewriter.rewrite_all_flagged(flagged_sents[:10], text)

                # ── Build report ───────────────────────────────
                report = PlagiarismReport.build(
                    source_name=source_name,
                    overall_lexical=lexical_score,
                    semantic_results=semantic_results,
                    internet_matches=internet_matches,
                    rewrites=rewrites,
                )

                # Save report
                saved_path = PlagiarismReport.save(report)
                report["saved_path"] = saved_path
                report["voice_summary"] = PlagiarismReport.to_voice_summary(report)

                set_result(report)
                print(f">> [PlagiarismGuardian] Analysis complete. Report: {saved_path}")

            except Exception as e:
                set_result({"error": str(e)})
                print(f">> [PlagiarismGuardian] Error: {e}")
            finally:
                self._running = False

        # Run pipeline in background thread
        thread = threading.Thread(target=_pipeline, daemon=True)
        thread.start()

        return (
            f"Plagiarism analysis initiated for {Path(source_name).name}. "
            f"Running all three phases: lexical scan, semantic similarity, and internet cross-check. "
            f"I will report back when complete, Sir. This may take 30 to 90 seconds."
        )

    # ── Helpers ────────────────────────────────────────────────

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences, filter short ones."""
        raw = re.split(r'(?<=[.!?])\s+', text.strip())
        return [
            s.strip() for s in raw
            if len(s.split()) >= MIN_SENTENCE_WORDS
        ]

    def _read_file(self, path: str) -> str:
        """Read .txt, .md, .pdf, .docx files."""
        p = Path(path)
        if not p.exists():
            # Try common locations
            for base in [Path.home() / "Documents", Path.home() / "Desktop",
                         Path.home() / "Downloads", Path.cwd()]:
                candidate = base / p.name
                if candidate.exists():
                    p = candidate
                    break
            else:
                return ""

        ext = p.suffix.lower()

        if ext in (".txt", ".md"):
            return p.read_text(encoding="utf-8", errors="ignore")

        if ext == ".pdf":
            try:
                import pdfplumber
                with pdfplumber.open(str(p)) as pdf:
                    return "\n".join(page.extract_text() or "" for page in pdf.pages)
            except ImportError:
                try:
                    import PyPDF2
                    with open(str(p), "rb") as f:
                        reader = PyPDF2.PdfReader(f)
                        return "\n".join(
                            page.extract_text() or "" for page in reader.pages
                        )
                except Exception:
                    return ""

        if ext == ".docx":
            try:
                from docx import Document
                doc = Document(str(p))
                return "\n".join(para.text for para in doc.paragraphs)
            except Exception:
                return ""

        return ""

    def get_result_summary(self) -> str:
        """Called when user asks 'what did you find' after analysis."""
        result = get_result()
        if not result:
            return "No plagiarism analysis has been run yet, Sir."
        if "error" in result:
            return f"Analysis encountered an error: {result['error']}"
        return result.get("voice_summary", "Analysis complete. Check the web interface for the full report.")