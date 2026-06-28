# Comenzi vocale pentru hidratare

import re
import random

from features.tools.abstract_tool import ToolHandler

CUVINTE_STATUS_APA = (
    "how much water",
    "how much have i drunk",
    "how much did i drink",
    "water intake",
    "water status",
    "hydration status",
    "water progress",
    "have i drunk today",
    "did i drink today",
    "what is my water goal",
    "what is my water gold",
    "but is my water goal",
    "but is my water gold",
    "what is my daily water goal",
    "what is my daily water gold",
    "but is my daily water goal",
    "but is my daily water gold",
    "how much water do i need to drink",
    "how much water do i have to drink",
    "how many mililiters did i drink",
    "what is my water intake percent",
    "what is my water intake percentage",
    "what percentage have i achieved",
)

CUVINTE_SET_ORA_START_REMINDERE = (
    "set reminder start hour",
    "set reminder start time",
    "set water reminder start hour",
    "set water reminder start time",
    "set hydration reminder start hour",
    "set hydration reminder start time",
    "change water reminder start hour",
    "change water reminder start time",
    "change hydration reminder start hour",
    "change hydration reminder start time",
    "start reminders at",
)

CUVINTE_SET_ORA_STOP_REMINDERE = (
    "set reminder end hour",
    "set reminder end time",
    "set reminder last hour",
    "set reminder last time",
    "set water reminder last hour",
    "set water reminder end time",
    "set hydration reminder end hour",
    "set hydration reminder end time",
    "change water reminder end hour",
    "change water reminder end time",
    "change hydration reminder end hour",
    "change hydration reminder end time",
    "stop reminders at",
    "stop water reminders at",
    "end reminders at",
    "end water reminders at",
)

CUVINTE_SET_NUMAR_REMINDERE = (
    "set number of reminders to",
    "set the number of reminders to",
    "set number of water reminders to",
    "set the number of water reminders to",
    "set number of hydration reminders to",
    "set the number of hydration reminders to",
    "set number of daily reminders to",
    "set the number of daily reminders to",
    "set number of daily water reminders to",
    "set the number of daily water reminders to",
    "set number of daily hydration reminders to",
    "set the number of daily hydration reminders to",
    "change water reminders to",
    "change daily water reminders to",
    "change hydration reminders to",
    "change number of reminders to",
    "change number of water reminders to",
    "change number of hydration reminders to",
    "change the number of reminders to",
    "change the number of water reminders to",
    "change the number of hydration reminders to",
    "change number of daily reminders to",
    "change number of daily water reminders to",
    "change number of daily hydration reminders to",
    "change the number of daily reminders to",
    "change the number of daily water reminders to",
    "change the number of daily hydration reminders to",
    "number of reminders to",
    "remind me of water intakeremind me of hydration",
)


class HydrationHandler(ToolHandler):
    def __init__(self, hydra_server):
        self.hydra_server = hydra_server

        self.sub_handlere = [
            self.handler_status,
            self.handler_set_ora_start,
            self.handler_set_ora_final,
            self.handler_set_numar_remindere,
        ]

    def proceseaza(self, text):
        for sub_handler in self.sub_handlere:
            raspuns = sub_handler(text)
            if raspuns is not None:
                return raspuns
        return None

    def handler_status(self, text: str) -> str | None:
        if not any(cuvant in text for cuvant in CUVINTE_STATUS_APA):
            return None

        status = self.hydra_server.status_curent
        if not status["ultima_actualizare"]:
            return "I haven't received any hydration data from the app yet."

        mesaje_posibile = [
            f"Right now you are at {status['procent']} percent of your water intake goal. You drank {status['ml_bauti']} mililiters and your goal is {status['goal']} mililiters.",
            f"You've hit {status['procent']} percent of your water goal for today. You've had {status['ml_bauti']} mililiters so far out of your {status['goal']} mililiters target.",
            f"Your daily goal is {status['goal']}! You are at {status['procent']} percent right now, which means you drank {status['ml_bauti']} mililiters.",
            f"You've drunk {status['ml_bauti']} mililiters today so far. That brings you to {status['procent']} percent of your {status['goal']} mililiters goal.",
            f"You are currently at {status['procent']} percent of your target, with {status['ml_bauti']} mililiters drank out of {status['goal']} mililiters.",
        ]

        mesaj = random.choice(mesaje_posibile)

        return mesaj

    def handler_set_ora_start(self, text: str) -> str | None:
        if not any(cuvant in text for cuvant in CUVINTE_SET_ORA_START_REMINDERE):
            return None

        ora = self.extrage_ora(text)
        if ora is None:
            return "Please tell me a specific hour, like 13 or 1 PM."

        if ora < 10 or ora > 14:
            return (
                "Hour for the first hydration reminder must be between 10 AM and 2 PM"
            )

        self.hydra_server.config["ora_start"] = ora
        self.hydra_server.salveaza_config()
        self.hydra_server.programeaza_remindere()
        return f"Start hour for water reminders set at {ora}."

    def handler_set_ora_final(self, text: str) -> str | None:
        if not any(cuvant in text for cuvant in CUVINTE_SET_ORA_STOP_REMINDERE):
            return None

        ora = self.extrage_ora(text)
        if ora is None:
            return "Please tell me a specific hour, like 20 or 8 PM."

        if ora < 20 or ora > 23:
            return "Hour for the last hydration reminder must be between 8 PM and 11 PM"

        self.hydra_server.config["ora_final"] = ora
        self.hydra_server.salveaza_config()
        self.hydra_server.programeaza_remindere()
        return f"End hour for water reminders set to {ora}."

    def handler_set_numar_remindere(self, text: str) -> str | None:
        if not any(cuvant in text for cuvant in CUVINTE_SET_NUMAR_REMINDERE):
            return None

        numar = self.extrage_numar(text)
        if numar is None:
            return "Please tell me a specific number, like 4 or 7."

        if numar < 3 or numar > 10:
            return "Number of hydration reminders must be between 3 and 10."

        self.hydra_server.config["numar_remindere"] = numar
        self.hydra_server.salveaza_config()
        self.hydra_server.programeaza_remindere()
        return f"Number of daily water reminders set to {numar}."

    # Helperi
    def extrage_numar(self, text: str) -> int | None:
        match = re.search(r"\b(\d{1,2})\b", text)

        if match:
            return int(match.group(1))

        cuvinte_in_numere = {
            "one": 1,
            "two": 2,
            "three": 3,
            "four": 4,
            "five": 5,
            "six": 6,
            "seven": 7,
            "eight": 8,
            "nine": 9,
            "ten": 10,
            "eleven": 11,
            "twelve": 12,
            "thirteen": 13,
            "fourteen": 14,
            "fifteen": 15,
            "sixteen": 16,
            "seventeen": 17,
            "eighteen": 18,
            "nineteen": 19,
            "twenty": 20,
            "twenty one": 21,
            "twenty two": 22,
            "twenty three": 23,
            "twenty four": 24,
        }

        for cuvant, valoare in cuvinte_in_numere.items():
            if cuvant in text:
                return valoare
        return None

    def extrage_ora(self, text: str) -> int | None:
        numar = self.extrage_numar(text)
        if numar is None:
            return None

        if "pm" in text and numar < 12:
            numar += 12
        elif "evening" in text and numar < 12:
            numar += 12
        elif "night" in text and numar < 12:
            numar += 12
        return numar
