import re

from features.tools.abstract_tool import ToolHandler


CUVINTE_PRAG = (
    "set break reminder to",
    "set break reminder",
    "change break reminder to",
    "change break reminder",
    "set sedentary reminder to",
    "set sitting reminder to",
    "set my break reminder to",
)

CUV_NUM = {
    "thirty": 30,
    "forty": 40,
    "forty five": 45,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "ninety": 90,
    "an hour": 60,
    "one hour": 60,
    "two hours": 120,
}

CUVINTE_TIMP_REMINDER = (
    "how long until my next break",
    "how long until the next break",
    "how long until my next warning",
    "how long until the next warning",
    "how long until my next reminder",
    "how long until the next reminder",
    "how much time until my next break",
    "how much time until the next break",
    "how much time until my next warning",
    "how much time until the next warning",
    "how much time until my next reminder",
    "how much time until the next reminder",
    "when is my next break reminder",
    "when is the next break reminder",
    "when is my next break",
    "when is the next break",
    "when is the next reminder",
    "when is my next reminder",
    "when is the next warning",
    "when is my next warning",
    "when is the next sitting warning",
    "when is my next sitting warning",
    "time until next break",
)


class PresenceHandler(ToolHandler):
    """
    Comanda vocala pentru pragul de sedentarism:
    "set break reminder to 45 minutes" -> 30..180 min, aplicat imediat.
    Rule-based (fara LLM) - extragere simpla de numar.
    """

    def __init__(self, monitor_prezenta):
        self.monitor = monitor_prezenta

    def proceseaza(self, text):
        if any(cuvant in text for cuvant in CUVINTE_TIMP_REMINDER):
            return self.raspuns_timp_pana_la_reminder()
        if not any(cuvant in text for cuvant in CUVINTE_PRAG):
            return None

        minute = self.extrage_minute(text)
        if minute is None:
            return "Please tell me how many minutes, like 45 or 90."
        if minute < 30 or minute > 180:
            return "The break reminder must be between 30 and 180 minutes."

        self.monitor.seteaza_prag_minute(minute)
        return f"Break reminder set to {minute} minutes."

    def extrage_minute(self, text):
        m = re.search(r"\b(\d{1,3})\b", text)
        if m:
            return int(m.group(1))
        for cuvant, valoare in CUV_NUM.items():
            if cuvant in text:
                return valoare
        return None

    def raspuns_timp_pana_la_reminder(self):
        ramas = self.monitor.secunde_pana_la_reminder()
        if ramas is None:
            return "You just got back to your desk, so the timer is reset."
        minute = int(ramas // 60)
        if minute <= 0:
            return "Your next reminder is due any moment now."
        if minute <= 1:
            return "Your next break reminder is in about one minute."
        return f"Your next break reminder is in about {minute} minutes."
