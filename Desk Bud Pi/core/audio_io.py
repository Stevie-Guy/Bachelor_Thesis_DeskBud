import numpy as np
import sounddevice as sd
import soundfile as sf


class AudioIO:
    SAMPLE_RATE_INPUT = 44100  # microfonul USB nu suporta 16000

    CUVINTE_CHEIE_MIC = ("usb", "microphone", "mic")
    CUVINTE_CHEIE_HAT = ("wm8960", "seede", "hat", "snd_rpi")

    def __init__(self):
        self.id_microfon = self.gaseste_dispozitiv(self.CUVINTE_CHEIE_MIC, tip="input")
        self.id_difuzor = self.gaseste_dispozitiv(self.CUVINTE_CHEIE_HAT, tip="output")

    def este_disponibil(self) -> bool:
        return self.id_microfon is not None and self.id_difuzor is not None

    def inregistreaza(self, durata_secunde: float) -> np.ndarray:
        # Inregistreaza audio mono de la microfon, returneaza array float32.
        audio = sd.rec(
            int(durata_secunde * self.SAMPLE_RATE_INPUT),
            samplerate=self.SAMPLE_RATE_INPUT,
            channels=1,
            device=self.id_microfon,
            dtype="float32",
        )

        sd.wait()
        return audio.flatten()

    def redare_array(self, audio: np.ndarray, sample_rate: int):
        # Reda un array numpy prin difuzor
        sd.play(audio, samplerate=sample_rate, device=self.id_difuzor)
        sd.wait()

    def redare_wav(self, cale_wav: str):
        # Reda un fisier WAV prin difuzor
        date, sample_rate = sf.read(cale_wav, dtype="float32")
        self.redare_array(date, sample_rate=sample_rate)

    def gaseste_dispozitiv(self, cuvinte_cheie: tuple, tip: str):
        try:
            dispozitive = sd.query_devices()
            for i, dispozitiv in enumerate(dispozitive):
                nume = dispozitiv["name"].lower()
                if any(key_word in nume for key_word in cuvinte_cheie):
                    if tip == "input" and dispozitiv["max_input_channels"] > 0:
                        return i
                    if tip == "output" and dispozitiv["max_output_channels"] > 0:
                        return i
        except Exception as e:
            print(f"X Eroare la gasirea dispozitivelor: {e}")

        return None
