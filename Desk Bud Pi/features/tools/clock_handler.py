from datetime import datetime
from zoneinfo import ZoneInfo
import random

from features.tools.abstract_tool import ToolHandler

TIMEZONE = "Europe/Bucharest"

CUVINTE_ORA = (
    "what time is it",
    "but time is it",
    "what's the time",
    "whats the time",
    "what is the time",
    "but is the time",
    "tell me the time",
    "current time",
    "the time now",
    "what's the clock",
    "but is the clock",
    "whats the clock",
    "what is the clock",
    "tell me the clock",
    "the clock now",
)


class ClockHandler(ToolHandler):
    def proceseaza(self, text):
        if not any(cuvant in text for cuvant in CUVINTE_ORA):
            return None

        acum = datetime.now(ZoneInfo(TIMEZONE))
        ora_formatata = acum.strftime("%I:%M %p").lstrip("0")
        ora_formatata = ora_formatata.replace("AM", "A.M").replace("PM", "P.M")
        mesaje_posibile = [
            f"It is currently {ora_formatata}.",
            f"Right now it is {ora_formatata}.",
            f"The time is {ora_formatata}.",
            f"The clock is {ora_formatata}.",
        ]

        mesaj = random.choice(mesaje_posibile)
        return mesaj
