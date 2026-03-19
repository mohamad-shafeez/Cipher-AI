# core/listen.py
import pyaudio
import numpy as np
from faster_whisper import WhisperModel
import config

class Listener:
    def __init__(self):
        print(f">> Initializing Instant Ears for {config.ASSISTANT_NAME}...")
        self.model = WhisperModel(config.WHISPER_SIZE, device="cpu", compute_type="int8")
        self.p = pyaudio.PyAudio()
        self.THRESHOLD = 2000    # ← lower = catches more of your voice
        self.SILENCE_LIMIT = 0.8 # ← longer = catches full words   

    def listen(self):
        stream = self.p.open(format=pyaudio.paInt16, channels=1, 
                             rate=config.SAMPLE_RATE, input=True, 
                             frames_per_buffer=config.CHUNK_SIZE)
        
        frames = []
        started = False
        silence_chunks = 0
        print(f">> {config.ASSISTANT_NAME} is waiting...")

        while True:
            try:
                data = stream.read(config.CHUNK_SIZE, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.int16)
                amplitude = np.max(np.abs(audio_data))

                if amplitude > self.THRESHOLD:
                    if not started:
                        print(">> Voice Detected...")
                        started = True
                    frames.append(audio_data)
                    silence_chunks = 0
                elif started:
                    frames.append(audio_data)
                    silence_chunks += 1
                    if silence_chunks > (config.SAMPLE_RATE / config.CHUNK_SIZE * self.SILENCE_LIMIT):
                        break
                
                if len(frames) > (config.SAMPLE_RATE / config.CHUNK_SIZE * 10):
                    break
            except Exception as e:
                print(f"Streaming Error: {e}")
                break
        
        stream.stop_stream()
        stream.close()

        if not frames:
            return ""

        audio_np = np.concatenate(frames).flatten().astype(np.float32) / 32768.0
        return self.transcribe(audio_np)

    def transcribe(self, audio_np):
        segments, info = self.model.transcribe(
            audio_np,
            beam_size=1,           # ← increased from 1 for better accuracy
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=300,
                threshold=0.6,     # ← stricter voice detection
                min_speech_duration_ms=250  # ← ignore very short sounds
            ),
            language="en",         # ← force English only
            condition_on_previous_text=False  # ← prevents hallucinations
        )

        print(f">> Detected language: {info.language} (confidence: {info.language_probability:.2f})")
        
        text = " ".join([seg.text for seg in segments]).strip()

        # Enhanced hallucination filter
        noise_phrases = [
            "you", "thank you", "bye", ".", "thanks", 
            "thank you.", "okay", "hmm", "um", "uh",
            "you.", "thanks.", "okay.", "hey."
        ]
        if len(text) < 3 or text.lower().strip(".") in [p.strip(".") for p in noise_phrases]:
            return ""
            
        return text