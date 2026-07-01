import time
import queue
import threading

import numpy as np
import sounddevice as sd
import soundfile as sf


def log_dbg(eticheta, mesaj=""):
    t = time.strftime("%H:%M:%S")
    ms = int((time.time() % 1) * 1000)
    print(f"[{t}.{ms:03d}] [{eticheta}] {mesaj}", flush=True)


class AudioIO:
    SAMPLE_RATE_INPUT = 44100  # microfonul USB nu suporta 16000
    SAMPLE_RATE_VAD = 16000  # Silero VAD lucreaza la 16kHz

    VAD_CHUNK_SAMPLES_16K = 512
    VAD_THRESHOLD = 0.5

    SECUNDE_TACERE_FINAL = 1.5

    # Cat asteptam pana renuntam daca userul nu vorbeste deloc
    SECUNDE_TIMEOUT_FARA_VORBIRE = 15

    # Chunk-ul thread-ului de captura, in sample 16k. Mic, ca thread-ul
    # producator sa goleasca buffer-ul hardware foarte des si ALSA sa nu intre
    # niciodata in overflow (cauza confirmata a blocajelor).
    CHUNK_NATIV_16K = 512

    CUVINTE_CHEIE_MIC = ("usb", "microphone", "mic")
    CUVINTE_CHEIE_HAT = ("wm8960", "seede", "hat", "snd_rpi")

    def __init__(self):
        self.id_microfon = None

        self.id_microfon = self.gaseste_dispozitiv(self.CUVINTE_CHEIE_MIC, tip="input")
        self.id_difuzor = self.gaseste_dispozitiv(self.CUVINTE_CHEIE_HAT, tip="output")
        self.model_vad = None  # lazy

        # Lock doar pentru redare (TTS). Captura NU mai foloseste lock: un singur
        # thread (producatorul) atinge microfonul, deci nu exista concurenta.
        self.lock_audio = threading.RLock()

        # Coada producer-consumer: thread-ul de captura pune chunk-uri 16k aici,
        # consumatorii (wake word, inregistreaza) le scot.
        self.coada_audio = queue.Queue(maxsize=200)
        self.thread_captura = None
        self.captura_activa = False

        # Cat e set, chunk-urile sunt ARUNCATE (DeskBud vorbeste -> anti-ecou).
        self.mut = threading.Event()
        self.cache_resample = {}

    @property
    def lock_microfon(self):
        return self.lock_audio

    def este_disponibil(self) -> bool:
        return self.id_microfon is not None and self.id_difuzor is not None

    def incarca_vad(self):
        if self.model_vad is None:
            from silero_vad import load_silero_vad

            self.model_vad = load_silero_vad(onnx=True)

    def porneste_captura(self):
        # orneste thread-ul care detine microfonul. Apelat O DATA la pornire.
        if self.captura_activa:
            return
        if self.model_vad is None:
            self.incarca_vad()
        self.captura_activa = True
        self.thread_captura = threading.Thread(target=self.bucla_captura, daemon=True)
        self.thread_captura.start()
        log_dbg("CAPT", "thread producator pornit (microf permanent)")

    def opreste_captura(self):
        self.captura_activa = False

    def bucla_captura(self):
        chunk_44k = int(
            self.VAD_CHUNK_SAMPLES_16K * self.SAMPLE_RATE_INPUT / self.SAMPLE_RATE_VAD
        )
        while self.captura_activa:
            try:
                with sd.InputStream(
                    samplerate=self.SAMPLE_RATE_INPUT,
                    channels=1,
                    device=self.id_microfon,
                    dtype="float32",
                    blocksize=chunk_44k,
                    latency=0.2,
                ) as stream:
                    log_dbg("CAPT", "stream deschis, captez continuu")
                    while self.captura_activa:
                        bloc, overflowed = stream.read(chunk_44k)
                        if overflowed:
                            log_dbg("CAPT", "OVERFLOW (buffer hardware plin)")
                        if self.mut.is_set():
                            continue  # DeskBud vorbeste -> ignoram intrarea

                        try:
                            self.coada_audio.put_nowait(bloc.flatten())
                        except queue.Full:
                            try:
                                self.coada_audio.get_nowait()
                                self.coada_audio.put_nowait(bloc.flatten())
                            except queue.Empty:
                                pass
            except Exception as e:
                log_dbg("CAPT", f"EXCEPTIE stream, reincerc: {e}")
                time.sleep(1)

    def goleste_coada(self):
        while not self.coada_audio.empty():
            try:
                self.coada_audio.get_nowait()
            except queue.Empty:
                break

    def citeste_din_coada(self, timeout=1.0):
        try:
            while True:
                return self.coada_audio.get(timeout=timeout)
        except queue.Empty:
            return None

    def inregistreaza(self) -> np.array:
        max_chunks_tacere = int(
            self.SECUNDE_TACERE_FINAL
            * self.SAMPLE_RATE_VAD
            / self.VAD_CHUNK_SAMPLES_16K
        )
        max_chunks_timeout = int(
            self.SECUNDE_TIMEOUT_FARA_VORBIRE
            * self.SAMPLE_RATE_VAD
            / self.VAD_CHUNK_SAMPLES_16K
        )

        self.goleste_coada()  # ca sa nu proceseze zgomot vechi

        buffer_audio = []
        a_vorbit_vreodata = False
        chunks_tacere = 0
        chunkstimeout = 0

        while True:
            bloc_44k = self.citeste_din_coada()
            if bloc_44k is None:
                continue  # coada goala

            bloc_16k = self.resample_la_16k(bloc_44k)
            bloc_16k = self.ajusteaza_lungime(bloc_16k, self.VAD_CHUNK_SAMPLES_16K)
            buffer_audio.append(bloc_16k)
            probabilitate = self.verifica_vorbire(bloc_16k)
            este_vorbire = probabilitate >= self.VAD_THRESHOLD

            if este_vorbire:
                if not a_vorbit_vreodata:
                    print("Speech detected", flush=True)
                    a_vorbit_vreodata = True
                chunks_tacere = 0
            else:
                if a_vorbit_vreodata:
                    chunks_tacere += 1
                    if chunks_tacere >= max_chunks_tacere:
                        break
                else:
                    chunkstimeout += 1
                    if chunkstimeout >= max_chunks_timeout:
                        return np.array([], dtype=np.float32)

        return np.concatenate(buffer_audio)

    # Redare
    def redare_array(self, audio: np.ndarray, sample_rate: int):
        # Reda un array numpy prin difuzor
        with self.lock_audio:
            self.mut.set()
            try:
                sd.play(audio, samplerate=sample_rate, device=self.id_difuzor)
                sd.wait()
            finally:
                time.sleep(0.2)  # nu prindem coada propriei voci
                self.goleste_coada()
                self.mut.clear()

    def redare_wav(self, cale_wav: str):
        # Reda un fisier WAV prin difuzor
        date, sample_rate = sf.read(cale_wav, dtype="float32")
        self.redare_array(date, sample_rate=sample_rate)

    # Consumator wake word
    def citeste_chunk_ww(self, lungime_16k):
        adunat = []
        total = 0
        while total < lungime_16k:
            bloc_44k = self.citeste_din_coada()
            if bloc_44k is None:
                if not adunat:
                    return None
                break
            bloc_16k = self.resample_la_16k(bloc_44k)
            adunat.append(bloc_16k)
            total += len(bloc_16k)

        if not adunat:
            return None
        return self.ajusteaza_lungime(np.concatenate(adunat), lungime_16k)

    # Helperi
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
        # Downsample prin interpolare liniara. Suficient pentru VAD si wake word.
        # Indicii depind doar de lungimea blocului (mereu constanta: 1411 sau 3528),
        # asa ca ii cache-uim ca sa nu mai alocam linspace + arange la fiecare chunk.
        lungime_audio = len(audio)
        nr_sample_16k = int(
            lungime_audio * self.SAMPLE_RATE_VAD / self.SAMPLE_RATE_INPUT
        )
        if nr_sample_16k == 0:
            return np.array([], dtype=np.float32)

        cache = self.cache_resample.get(lungime_audio)
        if cache is None:
            indici = np.linspace(0, lungime_audio - 1, nr_sample_16k)
            xp = np.arange(lungime_audio)
            self.cache_resample[lungime_audio] = (indici, xp)
        else:
            indici, xp = cache
        return np.interp(indici, xp, audio).astype(np.float32)

    def ajusteaza_lungime(self, audio: np.ndarray, lungime_dorita: int) -> np.ndarray:
        # Padding sau truncare la lungimea exacta ceruta de Silero, altfel crapa
        if len(audio) < lungime_dorita:
            return np.pad(audio, (0, lungime_dorita - len(audio)))
        return audio[:lungime_dorita]
