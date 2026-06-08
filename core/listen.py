# core/listen.py — CIPHER OS (Neural VAD Edition)
# ============================================================
#  Upgrades over previous version:
#  ✓ Silero VAD — Neural voice detection (replaces amplitude thresholding)
#  ✓ Faster-Whisper INT8 — Low memory transcription
#  ✓ Cross-talk isolation — Sleeps VAD thread while Cipher speaks
# ============================================================

import pyaudio
import numpy as np
import threading
import collections
import time 
import config
from faster_whisper import WhisperModel
from silero_vad import load_silero_vad, get_speech_timestamps
import torch
from core.speak import Speaker

class Listener:
    def __init__(self):
        print(f">> Initializing Neural Ears for {config.ASSISTANT_NAME}...")

        # Load Faster-Whisper
        self.model = WhisperModel(
            config.WHISPER_SIZE,
            device="cpu",
            compute_type="int8"
        )
        
        # Load Silero VAD
        self.vad_model = load_silero_vad()
        
        self.p = pyaudio.PyAudio()

        # ── Tunable constants ──────────────────────────────────
        self.SILENCE_LIMIT    = 1.5   # seconds of silence before stopping
        self.MAX_DURATION     = 30.0  # max recording seconds
        self.PRE_BUFFER_SECS  = 0.5   # ring buffer before speech starts
        self.VAD_THRESHOLD    = 0.5   # probability threshold for speech
        
        # Silero VAD requires 16000 Hz, make sure we use it internally
        self.SAMPLE_RATE = 16000
        self.CHUNK_SIZE = 512

        # ── Interrupt system ───────────────────────────────────
        self.interrupt_flag = threading.Event()
        self.bg_thread = None

        print(f">> Ears: ONLINE (Silero VAD + Faster-Whisper INT8)")

    def _is_speech(self, audio_data: np.ndarray) -> bool:
        """Check if audio chunk contains speech using Silero VAD."""
        # Normalize audio to [-1, 1] for Silero
        audio_float32 = audio_data.astype(np.float32) / 32768.0
        audio_tensor = torch.from_numpy(audio_float32)
        
        speech_prob = self.vad_model(audio_tensor, self.SAMPLE_RATE).item()
        return speech_prob > self.VAD_THRESHOLD

    def listen(self) -> str:
        """
        Record audio with Neural VAD:
        - Stream raw 16kHz audio
        - Use Silero VAD to detect speech
        - Smart silence gating
        - Cross-talk isolation (Speaker().busy)
        """
        stream = self.p.open(
            format=pyaudio.paInt16, channels=1,
            rate=self.SAMPLE_RATE, input=True,
            frames_per_buffer=self.CHUNK_SIZE
        )

        pre_buffer_size = int(self.SAMPLE_RATE / self.CHUNK_SIZE * self.PRE_BUFFER_SECS)
        pre_buffer = collections.deque(maxlen=pre_buffer_size)

        frames         = []
        started        = False
        silence_chunks = 0
        max_chunks     = int(self.SAMPLE_RATE / self.CHUNK_SIZE * self.MAX_DURATION)
        silence_limit_chunks = int(self.SAMPLE_RATE / self.CHUNK_SIZE * self.SILENCE_LIMIT)

        self.interrupt_flag.clear()
        
        from core.state_manager import StateManager
        StateManager.set_status("Listening...")
        
        listen_start_time = time.time()
        listen_timeout    = 7.0  # Wait for a voice before giving up

        while True:
            # ── Interrupt check ────────────────────────────────
            if self.interrupt_flag.is_set():
                print(">> [Ears] Interrupted by flag.")
                break
                
            if not started and (time.time() - listen_start_time > listen_timeout):
                break

            # ── Speaker cross-talk check ────────────────────────
            if getattr(Speaker(), 'busy', False):
                # Discard audio and reset state if Cipher is speaking
                try:
                    stream.read(self.CHUNK_SIZE, exception_on_overflow=False)
                except:
                    pass
                frames = []
                started = False
                time.sleep(0.1) # Sleep thread slightly to save CPU
                continue

            try:
                data = stream.read(self.CHUNK_SIZE, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.int16)

                if self._is_speech(audio_data):
                    if not started:
                        print(">> Voice Detected...")
                        # 🔇 INSTANT VAD INTERRUPTION PROTOCOL
                        try:
                            Speaker().interrupt_stream()
                        except Exception as tts_int_err:
                            print(f">> Failed to interrupt TTS: {tts_int_err}")

                        from core.state_manager import StateManager
                        StateManager.set_status("Speech Detected")
                        started = True
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

        from core.state_manager import StateManager
        StateManager.set_status("Transcribing...")

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
            initial_prompt="Cipher, clipboard, system, mobile, test.py, error, computer",
            beam_size=3,                     
            suppress_tokens=[-1],            
            vad_filter=True, # Keep Faster-Whisper VAD as a secondary filter
            vad_parameters=dict(
                min_silence_duration_ms=400,  
                threshold=0.55,               
                min_speech_duration_ms=200,
            ),
            language="en",
            condition_on_previous_text=False, 
        )

        text = " ".join(seg.text for seg in segments).strip()

        from core.state_manager import StateManager
        StateManager.set_status("Idle")

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

    def start_background_listening(self, callback):
        """
        Global Persistence: Runs the microphone listener in a non-blocking background thread.
        """
        def _loop():
            print(">> Background Listener Active.")
            while not self.interrupt_flag.is_set():
                try:
                    text = self.listen()
                    if text and callback:
                        callback(text)
                except Exception as e:
                    print(f">> [Mic Reset] Recovering audio stream... {e}")
                    try:
                        self.p.terminate()
                    except Exception:
                        pass
                    self.p = pyaudio.PyAudio()
                    continue
                time.sleep(0.1)
        
        self.bg_thread = threading.Thread(target=_loop, daemon=True)
        self.bg_thread.start()
        return self.bg_thread
        
    def recalibrate(self):
        # Silero VAD handles noise adaptation inherently
        return "Neural VAD is active. Manual calibration is no longer required."