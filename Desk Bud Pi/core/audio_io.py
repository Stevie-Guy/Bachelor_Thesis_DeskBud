import numpy as np
import sounddevice as sd
import soundfile as sf
import threading


class AudioIO:
    SAMPLE_RATE_INPUT = 44100  # microfonul USB nu suporta 16000
    SAMPLE_RATE_VAD = 16000  # Silero VAD lucreaza la 16kHz

    VAD_CHUNK_SAMPLES_16K = 512
    VAD_THRESHOLD = 0.5

    SECUNDE_TACERE_FINAL = 1.5

    # Cat asteptam pana renuntam daca userul nu vorbeste deloc
    SECUNDE_TIMEOUT_FARA_VORBIRE = 5

    CUVINTE_CHEIE_MIC = ("usb", "microphone", "mic")
    CUVINTE_CHEIE_HAT = ("wm8960", "seede", "hat", "snd_rpi")

    def __init__(self):
        self.id_microfon = self.gaseste_dispozitiv(self.CUVINTE_CHEIE_MIC, tip="input")
        self.id_difuzor = self.gaseste_dispozitiv(self.CUVINTE_CHEIE_HAT, tip="output")
        self.model_vad = None  # lazy
        self.lock_microfon = threading.Lock()

    def este_disponibil(self) -> bool:
        return self.id_microfon is not None and self.id_difuzor is not None

    def incarca_vad(self):
        if self.model_vad is None:
            from silero_vad import load_silero_vad

            self.model_vad = load_silero_vad(onnx=True)

    def inregistreaza(self) -> np.ndarray:
        """
        Asculta continuu si returneaza audio-ul vorbit.
        Se opreste cand detecteaza tacere dupa ce userul a vorbit.
        Returneaza array gol daca userul nu a vorbit deloc (timeout).
        """
        with self.lock_microfon:
            if self.model_vad is None:
                self.incarca_vad()

            # Cate sample-uri la 44100 corespund unui chunk VAD de 512 @ 16000
            chunk_44k = int(
                self.VAD_CHUNK_SAMPLES_16K
                * self.SAMPLE_RATE_INPUT
                / self.SAMPLE_RATE_VAD
            )

            max_chuncks_tacere = int(
                self.SECUNDE_TACERE_FINAL
                * self.SAMPLE_RATE_VAD
                / self.VAD_CHUNK_SAMPLES_16K
            )

            max_chunks_timeout = int(
                self.SECUNDE_TIMEOUT_FARA_VORBIRE
                * self.SAMPLE_RATE_VAD
                / self.VAD_CHUNK_SAMPLES_16K
            )

            buffer_audio = []
            a_vorbit_vreodata = False
            chunks_tacere = 0
            chunks_timeout = 0

            stream = sd.InputStream(
                samplerate=self.SAMPLE_RATE_INPUT,
                channels=1,
                device=self.id_microfon,
                dtype="float32",
                blocksize=chunk_44k,
            )

            stream.start()

            try:
                while True:
                    bloc, _ = stream.read(chunk_44k)
                    bloc = bloc.flatten()
                    buffer_audio.append(bloc)

                    # Resample VAD
                    bloc_16k = self.resample_la_16k(bloc)
                    bloc_16k = self.ajusteaza_lungime(
                        bloc_16k, self.VAD_CHUNK_SAMPLES_16K
                    )

                    # Interfata VAD
                    probabilitate = self.verifica_vorbire(bloc_16k)
                    este_vorbire = probabilitate >= self.VAD_THRESHOLD

                    if este_vorbire:
                        if not a_vorbit_vreodata:
                            print("Speech detected")
                            a_vorbit_vreodata = True
                        chunks_tacere = 0
                    else:
                        if a_vorbit_vreodata:
                            chunks_tacere += 1
                            if chunks_tacere >= max_chuncks_tacere:
                                break
                        else:
                            chunks_timeout += 1
                            if chunks_timeout >= max_chunks_timeout:
                                stream.stop()
                                stream.close()
                                return np.array([], dtype=np.float32)
            finally:
                stream.stop()
                stream.close()

            return np.concatenate(buffer_audio)

    # Redare
    def redare_array(self, audio: np.ndarray, sample_rate: int):
        # Reda un array numpy prin difuzor
        sd.play(audio, samplerate=sample_rate, device=self.id_difuzor)
        sd.wait()

    def redare_wav(self, cale_wav: str):
        # Reda un fisier WAV prin difuzor
        date, sample_rate = sf.read(cale_wav, dtype="float32")
        self.redare_array(date, sample_rate=sample_rate)

    # Helperi privati
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

    def verifica_vorbire(self, audio_16k: np.array) -> float:
        # Returneaza probabilitatea ca audio-ul sa contina vorbire (0.0-1.0)
        import torch

        tensor = torch.from_numpy(audio_16k)
        with torch.no_grad():
            prob = self.model_vad(tensor, self.SAMPLE_RATE_VAD).item()
        return prob

    def resample_la_16k(self, audio: np.ndarray) -> np.ndarray:
        # Downsample prin interpolare liniara. Suficient pentru vad
        nr_sample_16k = int(len(audio) * self.SAMPLE_RATE_VAD / self.SAMPLE_RATE_INPUT)
        if nr_sample_16k == 0:
            return np.array([], dtype=np.float32)
        indici = np.linspace(0, len(audio) - 1, nr_sample_16k)
        return np.interp(indici, np.arange(len(audio)), audio).astype(np.float32)

    def ajusteaza_lungime(self, audio: np.ndarray, lungime_dorita: int) -> np.ndarray:
        # Padding sau truncare la lungimea exacta ceruta de Silero, altfel crapa
        if len(audio) < lungime_dorita:
            return np.pad(audio, (0, lungime_dorita - len(audio)))
        return audio[:lungime_dorita]

    def deschide_stream_microfon(self, lungime_16k: int = None):
        # Returneaza un context manager pentru un stream de microfon constinuu
        if lungime_16k is None:
            lungime_16k = self.VAD_CHUNK_SAMPLES_16K

        chunk_44k = int(lungime_16k * self.SAMPLE_RATE_INPUT / self.SAMPLE_RATE_VAD)
        return sd.InputStream(
            samplerate=self.SAMPLE_RATE_INPUT,
            channels=1,
            device=self.id_microfon,
            dtype="float32",
            blocksize=chunk_44k,
        )

    def citeste_chunk(self, stream, lungime_16k: int = None):
        # Citeste chunk de la mic, face resample si ajusteaza la marimea ceruta
        if lungime_16k is None:
            lungime_16k = self.VAD_CHUNK_SAMPLES_16K

        chunk_44k = int(lungime_16k * self.SAMPLE_RATE_INPUT / self.SAMPLE_RATE_VAD)
        bloc, _ = stream.read(chunk_44k)
        bloc = bloc.flatten()
        bloc_16k = self.resample_la_16k(bloc)
        return self.ajusteaza_lungime(bloc_16k, lungime_16k)
