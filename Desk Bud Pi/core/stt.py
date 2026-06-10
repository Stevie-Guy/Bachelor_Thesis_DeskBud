"""
Implementam cele 5 tehnici de protectie (Vexa, GitHub openai/whisper):
1. Silero VAD ca pre-gate(faster-whisper il inregistreaza nativ)
2. condition_on_previous_text = False - opreste cascada de halucinari
3. Blacklist pentru fraze cunoscute de halucinare
4. Detectie de loop-uri repetitive
5. beam_size=1 - greedy decode, esueaza rapid pe tacere
"""

import os
import re
import tempfile
import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel


class SpeechToText:
    MODEL_SIZE = "base"
    LANGUAGE = "en"
    COMPUTE_TYPE = "int8"
    SAMPLE_RATE = 44100

    # Parametri Whisper anti-halucinare
    BEAM_SIZE = 1
    CONDITION_ON_PREVIOUS = False
    PRAG_NO_SPEECH = 0.6
    PRAG_LOGPROB = -1.0

    VAD_PARAMS = {
        "threshold": 0.5,
        "min_silence_duration_ms": 500,
        "speech_pad_ms": 200,
    }

    HALUCINARI = (
        # Outro-uri YouTube
        "thanks for watching",
        "thanks for watching!",
        "thank you for watching",
        "thank you for watching!",
        "thanks for watching, and i'll see you in the next video",
        "thanks for watching, and i'll see you next time",
        "i'll see you in the next video",
        "i'll see you next time",
        "see you in the next video",
        "see you next video",
        "see you all in the next video",
        # Cereri subscribe
        "subscribe",
        "please subscribe",
        "don't forget to subscribe",
        "like and subscribe",
        "subscribe to the channel",
        "please like and subscribe",
        "make sure to subscribe",
        # Halucinari multumiri YT
        "thank you so much for joining us",
        "thank you for joining us",
        "thanks so much",
        "thank you all",
        "thanks for your time",
        "thank you for your time",
        "thanks",
        # Markeri de subtitrare
        "subtitles by the amara.org community",
        "subtitled by the amara.org community",
        "translated by the amara.org community",
        "subtitles by",
        "captions by",
        "captioning by",
        "transcription by castingwords",
        "transcribed by",
        # Markeri de sunet pe tacere
        "[music]",
        "[applause]",
        "[laughter]",
        "[silence]",
        "[no audio]",
        "(music)",
        "(applause)",
        "(silence)",
        "music playing",
        "music is playing",
        "♪",
        "♪♪",
        "♪♪♪",
        # Fraze de inchidere
        "bye-bye",
        "bye bye",
        # Single tokens problematice (apar la zgomot)
        "the",
        ".",
        "..",
        "...",
        "....",
        # Diverse din productie
        "www.mooji.org",
        "amara.org",
    )

    TIPAR_LOOP = re.compile(
        r"^(.{3,60}?)(\s*\1){2,}\s*\.?$",
        re.IGNORECASE | re.DOTALL,
    )

    TIPAR_CUVINTE_REPETAT = re.compile(
        r"^(\b\w+\b[\s.,!?]*)\1{3,}$",
        re.IGNORECASE,
    )

    def __init__(self):
        self.model = None

    def incarca_model(self):
        # Incarca modelul Whisper in RAM. Apelat o singura data la pornire.
        self.model = WhisperModel(
            self.MODEL_SIZE,
            device="cpu",
            compute_type=self.COMPUTE_TYPE,
        )

    def transcrie(self, audio: np.ndarray) -> str:
        # Transcrie audio (numpy float32). Returneaza '' daca halucineaza

        if self.model is None:
            raise RuntimeError(
                "Model nu a fost incarcat. Apeleaza incarca_model() inainte"
            )

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            cale_wav = f.name
        sf.write(cale_wav, audio, self.SAMPLE_RATE)

        try:
            segmente, _ = self.model.transcribe(
                cale_wav,
                language=self.LANGUAGE,
                beam_size=self.BEAM_SIZE,
                condition_on_previous_text=self.CONDITION_ON_PREVIOUS,
                vad_filter=True,
                vad_parameters=self.VAD_PARAMS,
                no_speech_threshold=self.PRAG_NO_SPEECH,
                log_prob_threshold=self.PRAG_LOGPROB,
            )

            segmente_valide = [
                s.text.strip() for s in segmente if self.segment_valid(s)
            ]

            text = " ".join(segmente_valide).strip()

        finally:
            os.remove(cale_wav)

        if not self.text_valid(text):
            return ""

        return text

    # Filtre interne
    def segment_valid(self, segment) -> bool:
        # Verifica metric-urile interne Whisper pe un segment
        if getattr(segment, "no_speech_prob", 0) > self.PRAG_NO_SPEECH:
            return False
        if getattr(segment, "avg_logprob", 0) < self.PRAG_LOGPROB:
            return False
        return True

    def text_valid(self, text: str) -> bool:
        # Filtre pe textul final: black list + detectie de loop
        if not text:
            return False

        text_curat = text.strip().lower().rstrip(".,!?:;")

        if text_curat in self.HALUCINARI:
            return False

        if self.TIPAR_LOOP.match(text):
            return False
        if self.TIPAR_CUVINTE_REPETAT.match(text):
            return False

        return True
