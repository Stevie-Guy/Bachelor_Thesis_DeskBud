import sys
import time

from core.slm import MotorSLM
from core.router import ModelRouter

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
    "new conversation",
    "open a new chat",
}
CUVINTE_EXPLICATIVE = (
    "explain",
    "detail",
    "details",
    "elaborate",
    "in depth",
)


class DeskBud:
    STARE_IDLE = "idle"
    STARE_ACTIV = "activ"

    def __init__(self):
        self.stare = self.STARE_IDLE
        self.timp_ultimul_prompt = None
        self.timeout_activ = 600

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
        if not self.verifica_modele():
            sys.exit(1)

        self.pregateste_modele()
        print(
            "\nDeskBud is ready. Type your message ('exit' to quit, 'reset' to clear history).\n"
        )

        try:
            while True:
                prompt_utilizator = self.citeste_input()
                if not prompt_utilizator:
                    continue

                if prompt_utilizator.lower() in EXIT_COMMANDS:
                    print("\nDeskBud: Bye! Have a great day.\n")
                    break

                if prompt_utilizator.lower() in RESET_COMMANDS:
                    self.reseteaza_istoric()
                    print("\nIstoric resetat.\n")
                    continue

                self.gestioneaza_mesaje(prompt_utilizator)
        except KeyboardInterrupt:
            print("\n\nDeskBud: Shutting down. Bye!\n")

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

        try:
            for token in motor.chat(
                mesaj_utilizator=prompt_utilizator, num_tokens=limita
            ):
                if timp_primul_token is None:
                    timp_primul_token = time.perf_counter() - t_start
                print(token, end="", flush=True)
                nr_tokeni += 1
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
    def citeste_input(self) -> str:
        try:
            return input("You: ").strip()
        except EOFError as e:
            print(f"X A aparut o eroare la citire: {e}")
            return "exit"

    def verifica_modele(self) -> bool:
        print("Verifying models installation.")
        for nume, motor in self.motoare_slm.items():
            if motor.este_disponibil():
                print(f"Modelul {nume} merge")
            else:
                print(f"X Modelul {nume} nu a fost gasit")
                return False
        return True

    def pregateste_modele(self):
        print("\nWelcome back at the desk! Waking up DeskBud.")
        for nume, motor in self.motoare_slm.items():
            t = time.perf_counter()
            motor.incarcare_model_in_ram()
            print(f"Model {nume} incarcat in {time.perf_counter() - t:.2f}s")

    def reseteaza_istoric(self):
        self.istoric.clear()
