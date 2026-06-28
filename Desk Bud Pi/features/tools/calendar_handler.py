import re
import json
import urllib.parse
import urllib.request
import urllib.error

from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

from features.tools.abstract_tool import ToolHandler


CUVINTE_CONECTARE = (
    "connect calendar",
    "connect google calendar",
)

CUVINTE_CITIRE = (
    "what's on my calendar",
    "whats on my calendar",
    "what is on my calendar",
    "what's on my schedule",
    "whats on my schedule",
    "what is on my schedule",
    "my calendar tomorrow",
    "my calendar today",
    "calendar for today",
    "calendar for tomorrow",
    "is anything on my calendar",
)

CUVINTE_CREARE = (
    "schedule a",
    "schedule an",
    "schedule the",
    "scheduled a",
    "scheduled an",
    "scheduled the",
    "schedule meeting",
    "scheduled meeting",
    "add an event",
    "add a meeting",
    "add the event",
    "add the meeting",
    "add appointment",
    "add an appointment",
    "add the appointment",
    "add to my calendar",
    "create an event",
    "create a event",
    "create the event",
    "create event",
    "create a meeting",
    "create the meeting",
    "book a meeting",
    "book the meeting",
    "set up a meeting",
    "set a meeting",
    "set the meeting",
    "put on my calendar",
)

ZONA_LOCAL = ZoneInfo("Europe/Bucharest")
GOOGLE_CAL_BASE = "https://www.googleapis.com/calendar/v3/calendars/primary/events"

# Regexuri compilate o singura data (parser rapid fara LLM)
RE_PM = re.compile(r"\bp\.?\s?m\.?(?![a-z])")
RE_AM = re.compile(r"\ba\.?\s?m\.?(?![a-z])")
RE_ORA = re.compile(
    r"\bat\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b|\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b"
)
LUNI = (
    "january|february|march|april|may|june|july|august|september|october|"
    "november|december|jan|feb|mar|apr|jun|jul|aug|sept|sep|oct|nov|dec"
)
RE_LUNA_ZI = re.compile(r"\b(" + LUNI + r")\b\s+(\d{1,2})(?:st|nd|rd|th)?\b")
RE_ZI_LUNA = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(" + LUNI + r")\b")

RE_TITLU = re.compile(
    r"\b(?:called|titled|named)\s+(.+?)"
    r"(?=\s+(?:at|on|for|tomorrow|today|tonight|next|"
    r"monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b"
    r"|\s+\d|$)"
)
NON_TITLU = {"at", "on", "for", "to", "the", "a", "an", "this"}

RE_DURATA_NUM = re.compile(r"\bfor\s+(\d+)\s*(hours?|hrs?|minutes?|mins?)\b")
RE_DURATA_CUV = re.compile(
    r"\bfor\s+(one|two|three|four|five|six|seven|eight|nine|ten|an|a)\s+"
    r"(hours?|hrs?|minutes?|mins?)\b"
)
MON3 = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}
CUV_NUM = {
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
    "an": 1,
    "a": 1,
}


class CalendarHandler(ToolHandler):
    """
    Procesarea comenzilor pentru Google Calendar.
    - "connect calendar"          -> indrumare catre aplicatie
    - "what's on my calendar..."  -> citire (rule-based)
    - "schedule/add/create..."    -> creare: intai parser rapid (fara LLM),
                                     LLM doar pentru cazurile fuzzy
    """

    def __init__(self, calendar_auth, slm):
        self.auth = calendar_auth
        self.slm = slm

    def proceseaza(self, text):
        text = self.normalizeaza(text)

        if any(cuvant in text for cuvant in CUVINTE_CONECTARE):
            return self.raspuns_conectare()

        este_citire = any(cuvant in text for cuvant in CUVINTE_CITIRE)
        este_creare = any(cuvant in text for cuvant in CUVINTE_CREARE)
        if not este_citire and not este_creare:
            return None

        if not self.auth.este_conectat():
            return "Calendar isn't connected yet. Open the DeskBud app to connect it."

        if este_citire:
            return self.citeste_evenimente(text)
        return self.creeaza_eveniment(text)

    def normalizeaza(self, text):
        # STT da uneori "a.m."/"p.m."; uniformizam pentru regex si pentru LLM
        text = text.lower()
        text = RE_PM.sub("pm", text)
        text = RE_AM.sub("am", text)
        return text

    def raspuns_conectare(self):
        if not self.auth.este_configurat():
            return "Calendar is not set up on this device yet."
        if self.auth.este_conectat():
            return "Your calendar is already connected."
        return (
            "To connect your calendar, open the DeskBud app, go to the calculator tab, "
            "and tap the Connect Calendar button."
        )

    # ── CITIRE ────────────────────────────────────────────────────────────────
    def citeste_evenimente(self, text):
        if "next" in text:
            evenimente = self.cere_urmatoarele(maxim=1)
            if evenimente is None:
                return "I couldn't reach Google Calendar right now."
            if not evenimente:
                return "You have no upcoming plans."
            return "Next up: " + self.descrie_eveniment(evenimente[0], cu_zi=True) + "."

        pentru_maine = "tomorrow" in text
        time_min, time_max, eticheta_zi = self.fereastra_zi(pentru_maine)
        evenimente = self.cere_evenimente(time_min, time_max)
        if evenimente is None:
            return "I couldn't reach Google Calendar right now."
        if not evenimente:
            return f"You have nothing on your calendar {eticheta_zi}. Want to schedule something?"

        descrieri = [self.descrie_eveniment(e) for e in evenimente[:5]]
        if len(evenimente) == 1:
            return f"You have one event {eticheta_zi}: {descrieri[0]}."
        if len(evenimente) > 5:
            return (
                f"You have {len(evenimente)} events {eticheta_zi}. The first five are: "
                + ", ".join(descrieri[:-1])
                + ", and "
                + descrieri[-1]
                + "."
            )
        return (
            f"You have {len(evenimente)} events {eticheta_zi}: "
            + ", ".join(descrieri[:-1])
            + ", and "
            + descrieri[-1]
            + "."
        )

    def fereastra_zi(self, pentru_maine):
        acum = datetime.now(ZONA_LOCAL)
        zi = acum + (timedelta(days=1) if pentru_maine else timedelta(0))
        inceput = zi.replace(hour=0, minute=0, second=0, microsecond=0)
        sfarsit = inceput + timedelta(days=1)
        eticheta = "tomorrow" if pentru_maine else "today"
        return inceput.isoformat(), sfarsit.isoformat(), eticheta

    def cere_evenimente(self, time_min, time_max):
        access = self.auth.returneaza_access_token()
        if not access:
            return None
        url = (
            f"{GOOGLE_CAL_BASE}"
            f"?timeMin={urllib.parse.quote(time_min)}"
            f"&timeMax={urllib.parse.quote(time_max)}"
            f"&singleEvents=true&orderBy=startTime&maxResults=10"
        )
        try:
            return self.get_json(url, access).get("items", [])
        except Exception as e:
            print(f"X Eroare cerere evenimente: {e}")
            return None

    def cere_urmatoarele(self, maxim=1):
        access = self.auth.returneaza_access_token()
        if not access:
            return None
        acum = datetime.now(ZONA_LOCAL).isoformat()
        url = (
            f"{GOOGLE_CAL_BASE}"
            f"?timeMin={urllib.parse.quote(acum)}"
            f"&singleEvents=true&orderBy=startTime&maxResults={maxim}"
        )
        try:
            return self.get_json(url, access).get("items", [])
        except Exception as e:
            print(f"X Eroare cerere next: {e}")
            return None

    def get_json(self, url, access):
        req = urllib.request.Request(
            url,
            method="GET",
            headers={"Authorization": f"Bearer {access}"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))

    def descrie_eveniment(self, eveniment, cu_zi=False):
        titlu = eveniment.get("summary", "untitled event")
        start = eveniment.get("start", {})
        if "date" in start:
            if cu_zi:
                zi = datetime.fromisoformat(start["date"]).date()
                return f"{titlu} {self.eticheta_data(zi)}, all day"
            return f"{titlu}, all day"
        dt = datetime.fromisoformat(start["dateTime"]).astimezone(ZONA_LOCAL)
        ora_text = self.formateaza_ora(dt)
        if cu_zi:
            return f"{titlu} {self.eticheta_data(dt.date())} at {ora_text}"
        return f"{titlu} at {ora_text}"

    def formateaza_ora(self, dt):
        h12 = dt.hour % 12 or 12
        suffix = "AM" if dt.hour < 12 else "PM"
        if dt.minute == 0:
            return f"{h12} {suffix}"
        return f"{h12}:{dt.minute:02d} {suffix}"

    def eticheta_data(self, zi):
        azi = datetime.now(ZONA_LOCAL).date()
        if zi == azi:
            return "today"
        if zi == azi + timedelta(days=1):
            return "tomorrow"
        return f"on {zi.strftime('%A, %B %d')}"

    # ── CREARE ────────────────────────────────────────────────────────────────
    def creeaza_eveniment(self, text):
        access = self.auth.returneaza_access_token()
        if not access:
            return "I couldn't access your calendar. Please reconnect it from the app."

        date_ev = self.incearca_parsare_rapida(text)  # fara LLM daca reuseste
        if date_ev is None:
            date_ev = self.extrage_cu_llm(text)
            if date_ev is None:
                return "I couldn't understand the event details. Please spell more clearly."

        try:
            corp = self.construieste_eveniment(date_ev)
        except (ValueError, KeyError) as e:
            print(f"X Date eveniment invalide: {e}")
            return "I couldn't understand the event details. Please spell more clearly."

        try:
            self.posteaza_eveniment(corp, access)
        except urllib.error.HTTPError as e:
            print(f"X Calendar API: {e.read().decode('utf-8', 'ignore')}")
            return "I couldn't create the event right now. Please try again."
        except Exception as e:
            print(f"X Calendar API: {e}")
            return "I couldn't create the event right now. Please try again."

        return self.confirma_creare(date_ev)

    # Parser rapid: doar daca TOATE campurile ies sigur; altfel None -> LLM
    def incearca_parsare_rapida(self, text):
        ora = self.parse_ora(text)
        if ora is None:
            return None
        zi = self.parse_data(text)
        if zi is None:
            return None
        titlu = self.parse_titlu(text)
        if titlu is None:
            return None
        return {
            "title": titlu,
            "date": zi,
            "time": ora,
            "duration_minutes": self.parse_durata(text),
        }

    def parse_ora(self, text):
        m = RE_ORA.search(text)
        if not m:
            return None
        h = int(m.group(1))
        mi = int(m.group(2)) if m.group(2) else 0
        if not (1 <= h <= 12) or mi > 59:
            return None
        ampm = m.group(3)
        if ampm == "am":
            if h == 12:
                h = 0
        else:
            # "pm" SAU fara specificatie -> PM
            if h != 12:
                h += 12
        return f"{h:02d}:{mi:02d}"

    def parse_data(self, text):
        azi = datetime.now(ZONA_LOCAL).date()
        if "tomorrow" in text:
            return (azi + timedelta(days=1)).isoformat()
        if "today" in text or "tonight" in text:
            return azi.isoformat()

        m = RE_LUNA_ZI.search(text)
        if m:
            luna, zi_num = MON3[m.group(1)[:3]], int(m.group(2))
        else:
            m = RE_ZI_LUNA.search(text)
            if not m:
                return azi.isoformat()  # daca nu apare data, default azi
            luna, zi_num = MON3[m.group(2)[:3]], int(m.group(1))

        an = azi.year
        try:
            d = date(an, luna, zi_num)
        except ValueError:
            return azi.isoformat()
        if d < azi:  # data a trecut anul asta -> anul viitor
            try:
                d = date(an + 1, luna, zi_num)
            except ValueError:
                return None
        return d.isoformat()

    def parse_titlu(self, text):
        m = RE_TITLU.search(text)
        if not m:
            return None
        titlu = m.group(1).strip(".,!?")
        if not titlu or titlu in NON_TITLU:
            return None
        return titlu[0].upper() + titlu[1:]

    def parse_durata(self, text):
        m = RE_DURATA_NUM.search(text)
        if m:
            n = int(m.group(1))
            return n * 60 if m.group(2).startswith(("hour", "hr")) else n
        if "half an hour" in text or "half hour" in text:
            return 30
        m = RE_DURATA_CUV.search(text)
        if m:
            n = CUV_NUM[m.group(1)]
            return n * 60 if m.group(2).startswith(("hour", "hr")) else n
        return 30

    # LLM doar pentru cazurile pe care parserul rapid nu le poate confirma
    def extrage_cu_llm(self, text):
        prompt = self.construieste_prompt_creare(text)
        try:
            raspuns_llm = self.slm.extrage(prompt, num_tokens=80)
        except Exception as e:
            print(f"X Eroare LLM: {e}")
            return None
        try:
            return self.extrage_json(raspuns_llm)
        except (ValueError, KeyError) as e:
            print(f"X JSON LLM invalid: {e}; raw: {raspuns_llm!r}")
            return None

    def construieste_prompt_creare(self, text):
        acum = datetime.now(ZONA_LOCAL)
        maine = (acum + timedelta(days=1)).date().isoformat()
        return (
            "Extract calendar event details from the request. "
            "Return only a valid JSON object with these fields:\n"
            "- title: short event title (string)\n"
            "- date: YYYY-MM-DD\n"
            "- time: HH:MM in 24-hour format\n"
            "- duration_minutes: integer (use 30 if not specified)\n\n"
            "Output ONLY the JSON object. Do not write any code, explanation, or comments. "
            "If a field is missing, infer it (use today's date if no date is given, and 12:00 if no time is given).\n\n).\n\n"
            f"Current local time: {acum.strftime('%Y-%m-%d %H:%M, %A')}\n\n"
            "Example 1:\n"
            'Request: "Schedule a meeting tomorrow at 3 pm for one hour"\n'
            f'JSON: {{"title": "Meeting", "date": "{maine}", '
            f'"time": "15:00", "duration_minutes": 60}}\n\n'
            "Example 2:\n"
            'Request: "Remind me to call mom at 8 pm tonight for 15 minutes"\n'
            f'JSON: {{"title": "Call mom", "date": "{acum.date().isoformat()}", '
            f'"time": "20:00", "duration_minutes": 15}}\n\n'
            f'Request: "{text}"\n'
            "JSON:"
        )

    def extrage_json(self, text):
        inceput = text.find("{")
        sfarsit = text.rfind("}")
        if inceput == -1 or sfarsit == -1 or sfarsit < inceput:
            raise ValueError("no JSON object in LLM response")
        return json.loads(text[inceput : sfarsit + 1])

    def construieste_eveniment(self, date_ev):
        titlu = (date_ev.get("title") or "Event").strip()
        durata = int(date_ev.get("duration_minutes") or 30)
        inceput = datetime.fromisoformat(f"{date_ev['date']}T{date_ev['time']}:00")
        inceput = inceput.replace(tzinfo=ZONA_LOCAL)
        sfarsit = inceput + timedelta(minutes=durata)
        return {
            "summary": titlu,
            "start": {"dateTime": inceput.isoformat(), "timeZone": str(ZONA_LOCAL)},
            "end": {"dateTime": sfarsit.isoformat(), "timeZone": str(ZONA_LOCAL)},
        }

    def posteaza_eveniment(self, corp, access):
        body = json.dumps(corp).encode("utf-8")
        req = urllib.request.Request(
            GOOGLE_CAL_BASE,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {access}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))

    def confirma_creare(self, date_ev):
        titlu = (date_ev.get("title") or "Event").strip()
        zi = datetime.fromisoformat(date_ev["date"]).date()
        h, mi = (int(x) for x in date_ev["time"].split(":"))
        h12 = h % 12 or 12
        suffix = "AM" if h < 12 else "PM"
        ora_text = f"{h12} {suffix}" if mi == 0 else f"{h12}:{mi:02d} {suffix}"
        return f"Got it. Added {titlu} {self.eticheta_data(zi)} at {ora_text}."
