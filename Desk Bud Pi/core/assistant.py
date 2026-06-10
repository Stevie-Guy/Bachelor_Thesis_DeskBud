import sys
import time

from core.slm import MotorSLM
from core.router import ModelRouter
from core.audio_io import AudioIO
from core.stt import SpeechToText
from core.tts import TextToSpeech

SYSTEM_PROMPT = (
    "You are DeskBud, a smart and friendly desk assistant. "
    "Always reply in English. "
    "Never ramble. If asked about calendars, tasks, or reminders, extract key info clearly. "
)

MODEL_RAPID = "llama3.2:1b"
MODEL_SMART = "llama3.2:3b"

LIMITE_TOKENI = {
    MODEL_RAPID: 100,
    MODEL_SMART: 200,
}
LIMITA_TOKENI_EXPLICATIV = 400

EXIT_COMMANDS = {
    "exit",
    "quit",
    "bye",
    "goodbye",
    "stop",
    "shut up",
    "quiet",
    "silence",
    "enough",
}
RESET_COMMANDS = {
    "reset",
    "reset conversation",
    "reset the conversation",
    "reset chat",
    "reset history",
    "clear",
    "clear history",
    "clear the history",
    "clear conversation",
    "clear chat",
    "new chat",
    "a new chat",
    "the new chat",
    "new conversation",
    "the new conversation",
    "a new conversation",
    "open a new chat",
}
CUVINTE_EXPLICATIVE = (
    "explain",
    "detail",
    "details",
    "elaborate",
    "in depth",
)
SEMNE_SFARSIT = {
    ".",
    "!",
    "?",
    "\n",
}


class DeskBud:
    STARE_IDLE = "idle"
    STARE_ACTIV = "activ"

    def __init__(self):
        self.stare = self.STARE_IDLE
        self.timp_ultimul_prompt = None
        self.timeout_activ = 600

        self.audio_io = AudioIO()
        self.stt = SpeechToText()
        self.tts = TextToSpeech(self.audio_io)

        self.istoric = []  # istoric comun intre toate modelele

        self.router = ModelRouter(model_rapid=MODEL_RAPID, model_smart=MODEL_SMART)
        self.motoare_slm = {
            MODEL_RAPID: MotorSLM(MODEL_RAPID, sys_prompt=SYSTEM_PROMPT),
            MODEL_SMART: MotorSLM(MODEL_SMART, sys_prompt=SYSTEM_PROMPT),
        }

        for motor in self.motoare_slm.values():
            motor.istoric = self.istoric

    # ── lifecycle ──────────────────────────────────────────────────────────────

    def ruleaza(self):
        if not self.verifica_componente():
            sys.exit(1)

        self.pregateste_componente()
        print("\nDeskBud is ready. Try to ask something!\n")

        mesaj_pornire = "DeskBud ready. I'm listening."
        self.tts.vorbeste(mesaj_pornire)

        try:
            while True:
                prompt_utilizator = self.asculta()
                if not prompt_utilizator:
                    print("Utilizatorul nu a vorbit sau Whisper a halucinat.\n")
                    continue

                print(f"Prompt auzit: {prompt_utilizator}")
                prompt_lower = prompt_utilizator.lower().rstrip(".!?,;:")

                if prompt_lower in EXIT_COMMANDS:
                    mesaj_iesire = "Have a great day. Goodbye!"
                    print(f"DeskBud: {mesaj_iesire}.")
                    self.tts.vorbeste(mesaj_iesire)
                    break

                if prompt_utilizator.lower() in RESET_COMMANDS:
                    self.reseteaza_istoric()
                    mesaj_reset = "New conversation started."
                    print(f"  → {mesaj_reset}\n")
                    self.tts.vorbeste(mesaj_reset)
                    continue

                self.gestioneaza_mesaje(prompt_utilizator)
        except KeyboardInterrupt:
            print("\n\nDeskBud: Shutting down. Bye!\n")

    def asculta(self) -> str:
        # Asculta pana cand userul termina de vorbit, returneaza text transcris
        print("Listening...")
        audio = self.audio_io.inregistreaza()

        if len(audio) == 0:
            return ""

        print("Transcribing...")
        return self.stt.transcrie(audio)

    # ── flux principal ─────────────────────────────────────────────────────────

    def gestioneaza_mesaje(self, prompt_utilizator: str):
        model = self.router.alege_model(prompt=prompt_utilizator)
        motor = self.motoare_slm[model]

        if any(cuvant in prompt_utilizator.lower() for cuvant in CUVINTE_EXPLICATIVE):
            limita = LIMITA_TOKENI_EXPLICATIV
        else:
            limita = LIMITE_TOKENI[model]
        eticheta = "rapid" if model == MODEL_RAPID else "smart"
        print(f"Model {eticheta}: ", end="", flush=True)

        t_start = time.perf_counter()
        timp_primul_token = None
        nr_tokeni = 0

        propozitie_curenta = ""

        try:
            for token in motor.chat(
                mesaj_utilizator=prompt_utilizator, num_tokens=limita
            ):
                if timp_primul_token is None:
                    timp_primul_token = time.perf_counter() - t_start
                print(token, end="", flush=True)

                # Adaugam token-ul la propozitia curenta
                propozitie_curenta += token

                if any(semn in token for semn in SEMNE_SFARSIT):
                    if propozitie_curenta.strip():
                        self.tts.vorbeste(propozitie_curenta.strip())
                    # Golim propozitia pentru a incepe urmatoarea
                    propozitie_curenta = ""

                nr_tokeni += 1
            if propozitie_curenta.strip():
                self.tts.vorbeste(propozitie_curenta.strip())
        except Exception as e:
            print(f"\n !! A aparut o eroare: {e}")
            return

        timp_total = time.perf_counter() - t_start
        tokeni_pe_secunda = nr_tokeni / timp_total if timp_total > 0 else 0

        print(
            f"\n{model} | {timp_primul_token:.2f}s primul token | "
            f"{timp_total:.2f}s total | {tokeni_pe_secunda:.1f} tok/s\n"
        )

    # ── helpers ────────────────────────────────────────────────────────────────
    # def citeste_input(self) -> str:
    #     try:
    #         return input("You: ").strip()
    #     except EOFError as e:
    #         print(f"X A aparut o eroare la citire: {e}")
    #         return "exit"

    def verifica_componente(self) -> bool:
        print("Verifying components...")

        if not self.audio_io.este_disponibil():
            print("  X AudioIO — microfon sau difuzor lipsa")
            return False

        if not self.tts.este_disponibil():
            print("  X TTS Piper — binar sau model lipsa")
            return False

        for nume, motor in self.motoare_slm.items():
            if not motor.este_disponibil():
                print(f"X Modelul {nume} nu a fost gasit")
                return False

        return True

    def pregateste_componente(self):
        print("\nWelcome back at the desk! Waking up DeskBud.")

        t = time.perf_counter()
        self.stt.incarca_model()
        print(f"  ✓ Whisper STT in {time.perf_counter() - t:.2f}s")

        t = time.perf_counter()
        self.audio_io.incarca_vad()
        print(f"  ✓ Silero VAD in {time.perf_counter() - t:.2f}s")

        for nume, motor in self.motoare_slm.items():
            t = time.perf_counter()
            motor.incarcare_model_in_ram()
            print(f"Model {nume} incarcat in {time.perf_counter() - t:.2f}s")

    def reseteaza_istoric(self):
        self.istoric.clear()
