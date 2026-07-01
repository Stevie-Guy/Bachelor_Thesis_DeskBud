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
            self.model = Model(
                wakeword_models=[self.CALE_MODEL], inference_framework="onnx"
            )
        except TypeError:
            try:
                self.model = Model(
                    wakeword_model_paths=[self.CALE_MODEL], inference_framework="onnx"
                )
            except TypeError:
                self.model = Model(wakeword_model_paths=[self.CALE_MODEL])

    def asteapta_trezire(self):
        # CONSUMATOR: citeste chunk-uri din coada thread-ului de captura.
        # Nu mai atinge PortAudio direct -> nu mai poate bloca in stream.read.
        if self.model is None:
            raise RuntimeError("Modelul nu a fost incarcat!")

        ultima_detectie = 0
        self.model.reset()
        contor_print = 0

        self.audio_io.goleste_coada()

        while True:
            try:
                date_16k = self.audio_io.citeste_chunk_ww(self.LUNGIME_CHUNK_OPENWW)
                if date_16k is None:
                    time.sleep(0.05)  # Queue empty (DeskBud vorbeste / mut)
                    continue

                date_int16 = (date_16k * 32767).astype(np.int16)
                predictii = self.model.predict(date_int16)
                scor_maxim = max(predictii.values()) if predictii else 0.0

                contor_print += 1
                if contor_print % 10 == 0 or scor_maxim >= 0.3:
                    print(f"  scor: {scor_maxim:.3f}", end="\r", flush=True)

                if scor_maxim >= self.PRAG_DETECTIE:
                    acum = time.perf_counter()
                    if acum - ultima_detectie > self.COOLDOWN_SECUNDE:
                        ultima_detectie = acum
                        return

            except Exception as e:
                print(f"\n[WAKE] Eroare stream, reincerc: {e}")
                time.sleep(1)
