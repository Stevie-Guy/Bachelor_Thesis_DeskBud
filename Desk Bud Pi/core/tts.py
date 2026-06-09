import os
import subprocess
import tempfile

from core.audio_io import AudioIO


class TextToSpeech:
    PIPER_BIN = os.path.expanduser("~/piper/piper")
    PIPER_MODEL = os.path.expanduser("~/piper/models/en_US-lessac-medium.onnx")
    TIMEOUT_SECUNDE = 30

    def __init__(self, audio_io: AudioIO):
        self.audio_io = audio_io

    def este_disponibil(self) -> bool:
        return os.path.isfile(self.PIPER_BIN) and os.path.isfile(self.PIPER_MODEL)

    def vorbeste(self, text: str):
        # Reda textul prin difuzor dupa sintetizare
        if not text.strip():
            return

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            cale_wav = f.name

        try:
            rezultat = subprocess.run(
                [
                    self.PIPER_BIN,
                    "--model",
                    self.PIPER_MODEL,
                    "--output_file",
                    cale_wav,
                ],
                input=text,
                capture_output=True,
                text=True,
                timeout=self.TIMEOUT_SECUNDE,
            )

            if rezultat.returncode != 0:
                print(f"X Piper eroare: {rezultat.stderr.strip()}")
                return

            self.audio_io.redare_wav(cale_wav)

        except subprocess.TimeoutExpired:
            print(f"X Piper timeout (peste {self.TIMEOUT_SECUNDE}s)")
        except Exception as e:
            print(f"X Eroare TTS: {e}")
        finally:
            if os.path.exists(cale_wav):
                os.remove(cale_wav)
