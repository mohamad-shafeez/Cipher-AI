# core/listen.py — CIPHER OS  (Streaming VAD Edition)
# ============================================================
#  Upgrades over previous version:
#  ✓ Adaptive noise floor — calibrates to YOUR room on boot
#  ✓ Pre-speech ring buffer — never misses first syllable
#  ✓ Smart silence detection — 2.5s pause allowed, won't cut mid-thought
#  ✓ Interrupt flag — say "stop" while Cipher is thinking
#  ✓ Better hallucination filter — expanded noise phrase list
#  ✓ Max recording cap raised to 30s (was 10s)
# ============================================================

import pyaudio
import numpy as np
import threading
import collections
import config
import time 
from faster_whisper import WhisperModel

class Listener:
    def __init__(self):
        print(f">> Initializing Instant Ears for {config.ASSISTANT_NAME}...")

        self.model = WhisperModel(
            config.WHISPER_SIZE,
            device="cpu",
            compute_type="int8"
        )
        self.p = pyaudio.PyAudio()

        # ── Tunable constants ──────────────────────────────────
        self.SILENCE_LIMIT    = 2.5   # seconds of silence before stopping (was 0.8)
        self.MAX_DURATION     = 30.0  # max recording seconds (was 10)
        self.PRE_BUFFER_SECS  = 0.4   # ring buffer before speech starts

        # ── Adaptive threshold ─────────────────────────────────
        # Calibrated at boot — adjusts to your room's noise floor
        self.THRESHOLD = self._calibrate_noise_floor()

        # ── Interrupt system ───────────────────────────────────
        # Set this flag True from another thread to cancel recording
        self.interrupt_flag = threading.Event()

        print(f">> Ears: ONLINE (threshold={self.THRESHOLD}, silence={self.SILENCE_LIMIT}s)")

    # ── Noise floor calibration ────────────────────────────────

    def _calibrate_noise_floor(self) -> int:
        """
        Listen to 0.6s of ambient room noise at boot,
        set threshold at 3× the average to ignore background hum.
        """
        print(">> Calibrating microphone to room noise...")
        try:
            stream = self.p.open(
                format=pyaudio.paInt16, channels=1,
                rate=config.SAMPLE_RATE, input=True,
                frames_per_buffer=config.CHUNK_SIZE
            )
            samples = []
            chunks_needed = int(config.SAMPLE_RATE / config.CHUNK_SIZE * 0.6)
            for _ in range(chunks_needed):
                data = stream.read(config.CHUNK_SIZE, exception_on_overflow=False)
                arr  = np.frombuffer(data, dtype=np.int16)
                samples.append(np.max(np.abs(arr)))
            stream.stop_stream()
            stream.close()

            ambient   = float(np.mean(samples))
            threshold = max(800, int(ambient * 3.0))   # never below 800
            threshold = min(threshold, 3500)            # never above 3500
            print(f">> Ambient noise: {ambient:.0f} → Threshold set: {threshold}")
            return threshold

        except Exception as e:
            print(f">> Calibration failed ({e}), using default threshold 2000")
            return 2000

    # ── Main listen method ─────────────────────────────────────

    def listen(self) -> str:
        """
        Record audio with:
        - Pre-speech ring buffer (never misses first syllable)
        - Smart silence gating (2.5s pause allowed)
        - Interrupt flag support
        Returns transcribed text string.
        """
        stream = self.p.open(
            format=pyaudio.paInt16, channels=1,
            rate=config.SAMPLE_RATE, input=True,
            frames_per_buffer=config.CHUNK_SIZE
        )

        # Pre-speech ring buffer: holds last 0.4s before voice detected
        pre_buffer_size = int(
            config.SAMPLE_RATE / config.CHUNK_SIZE * self.PRE_BUFFER_SECS
        )
        pre_buffer = collections.deque(maxlen=pre_buffer_size)

        frames         = []
        started        = False
        silence_chunks = 0
        max_chunks     = int(config.SAMPLE_RATE / config.CHUNK_SIZE * self.MAX_DURATION)
        silence_limit_chunks = int(
            config.SAMPLE_RATE / config.CHUNK_SIZE * self.SILENCE_LIMIT
        )

        self.interrupt_flag.clear()
        print(f">> {config.ASSISTANT_NAME} is listening...")

        listen_start_time = time.time()
        listen_timeout    = 7.0  # Seconds to wait for a voice before giving up

        while True:
            # ── Interrupt check ────────────────────────────────
            if self.interrupt_flag.is_set():
                print(">> [Ears] Interrupted by flag.")
                break
            # Timeout check: If no voice detected within 7 seconds, stop
            if not started and (time.time() - listen_start_time > listen_timeout):
                print(">> [Ears] No voice detected. Standing down.")
                break

            try:
                data       = stream.read(config.CHUNK_SIZE, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.int16)
                amplitude  = np.max(np.abs(audio_data))

                if amplitude > self.THRESHOLD:
                    if not started:
                        print(">> Voice Detected...")
                        started = True
                        # Prepend pre-buffer so first syllable isn't clipped
                        frames.extend(pre_buffer)
                    frames.append(audio_data)
                    silence_chunks = 0

                elif started:
                    # Post-speech: keep recording through short pauses
                    frames.append(audio_data)
                    silence_chunks += 1
                    if silence_chunks >= silence_limit_chunks:
                        # Genuine end of speech
                        break

                else:
                    # Pre-speech: fill ring buffer
                    pre_buffer.append(audio_data)

                # Hard cap on total recording length
                if len(frames) >= max_chunks:
                    print(">> Max duration reached.")
                    break

            except Exception as e:
                print(f">> Stream error: {e}")
                break

        stream.stop_stream()
        stream.close()

        if not frames:
            return ""

        audio_np = (
            np.concatenate(frames)
            .flatten()
            .astype(np.float32) / 32768.0
        )
        return self.transcribe(audio_np)

# ── Transcription ──────────────────────────────────────────

    def transcribe(self, audio_np: np.ndarray) -> str:
        segments, info = self.model.transcribe(
            audio_np,
            beam_size=3,                     # was 1 — better accuracy with tiny speed cost
            suppress_tokens=[-1],            # <--- ADDED: Prevents hallucinating filler tokens
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=400,  # slightly more forgiving than 300
                threshold=0.55,               # was 0.6 — catches softer speech
                min_speech_duration_ms=200,
            ),
            language="en",
            condition_on_previous_text=False, # prevents hallucination loops
        )

        print(
            f">> Detected: {info.language} "
            f"(confidence: {info.language_probability:.2f})"
        )

        text = " ".join(seg.text for seg in segments).strip()

        # ── Hallucination filter ──────────────────────────────
        NOISE_PHRASES = {
            "you", "thank you", "thanks", "bye", "okay", "ok",
            "hmm", "um", "uh", "ah", "oh", "hey", "hi", "yes",
            "no", "yeah", "nah", "sure", "right", "alright",
            "you.", "thanks.", "okay.", "hey.", "thank you.",
        }
        cleaned = text.lower().strip(". ,!?")
        if len(text) < 3 or cleaned in NOISE_PHRASES:
            return ""

        return text

    # ── Interrupt API ──────────────────────────────────────────

    def interrupt(self):
        """Call from another thread to stop an active listen() call."""
        self.interrupt_flag.set()

    def recalibrate(self):
        """Re-run noise calibration (e.g. after moving rooms)."""
        self.THRESHOLD = self._calibrate_noise_floor()
        return f"Microphone recalibrated. New threshold: {self.THRESHOLD}"