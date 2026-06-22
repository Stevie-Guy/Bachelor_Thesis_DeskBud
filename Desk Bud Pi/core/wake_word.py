import time
import numpy as np
from openwakeword.model import Model

from core.audio_io import AudioIO


class DetectorWakeWord:
    CALE_MODEL = "data/models/wakeword/deskbud_wake.onnx"
    PRAG_DETECTIE = 0.5
    COOLDOWN_SECUNDE = 1.5  # pentru evitarea detectiei multiple
    LUNGIME_CHUNK_OPENWW = 1280

    def __init__(self, audio_io: AudioIO):
        self.audio_io = audio_io
        self.model = None

    def incarca_model(self):
        try:
            # Incearca varianta noua (de pe Colab)
            self.model = Model(
                wakeword_models=[self.CALE_MODEL], inference_framework="onnx"
            )
        except TypeError:
            try:
                # Incearca varianta stabila (din pip)
                self.model = Model(
                    wakeword_model_paths=[self.CALE_MODEL], inference_framework="onnx"
                )
            except TypeError:
                # Incearca varianta si mai veche (fara argumentul de framework)
                self.model = Model(wakeword_model_paths=[self.CALE_MODEL])

    def asteapta_trezire(self):
        # Returneaza cand detecteaza wake word.

        if self.model is None:
            raise RuntimeError("Modelul nu a fost incarcat!")

        ultima_detectie = 0
        self.model.reset()
        DURATA_SESIUNE = 60

        while True:
            t_inceput = time.perf_counter()
            try:
                with self.audio_io.deschide_stream_microfon(
                    self.LUNGIME_CHUNK_OPENWW
                ) as stream:
                    while time.perf_counter() - t_inceput < DURATA_SESIUNE:
                        date_16k = self.audio_io.citeste_chunk(
                            stream, self.LUNGIME_CHUNK_OPENWW
                        )
                        date_int16 = (date_16k * 32767).astype(np.int16)

                        predictii = self.model.predict(date_int16)
                        scor_maxim = max(predictii.values()) if predictii else 0.0

                        print(f"  scor: {scor_maxim:.3f}", end="\r")

                        if scor_maxim >= self.PRAG_DETECTIE:
                            acum = time.perf_counter()
                            if acum - ultima_detectie > self.COOLDOWN_SECUNDE:
                                ultima_detectie = acum
                                return
            except Exception as e:
                print(f"\n  [WAKE] Eroare stream, reincerc: {e}")
                time.sleep(1)
