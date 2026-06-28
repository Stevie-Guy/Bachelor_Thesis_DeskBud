import os
import json
import time
import urllib.request
import urllib.parse

from features.tools.abstract_tool import ToolHandler

API_KEY = os.environ.get("WEATHERAPI_KEY")
LOCATIE = "Bucharest"

CUVINTE_VREME_GENERAL = (
    "what's the weather",
    "whats the weather",
    "what is the weather",
    "how's the weather",
    "hows the weather",
    "how is the weather",
    "how will the weather be",
    "weather forecast",
    "weather today",
    "weather tomorrow",
    "weather outside",
    "what's the temperature",
    "whats the temperature",
    "what is the temperature",
    "the temperature outside",
    "the temperature today",
    "how cold is it",
    "is it hot outside",
    "is it cold outside",
    "is it warm outside",
    "is it sunny",
    "is it cloudy",
    "is it windy",
)

CUVINTE_VREME_URATA = (
    "is it raining",
    "is it going to rain",
    "will it rain",
    "chance of rain",
    "do i need an umbrella",
    "should i take an umbrella",
    "is it snowing",
    "is it going to snow",
    "chance of snow",
)


class WeatherHandler(ToolHandler):
    BASE_URL = "http://api.weatherapi.com/v1"
    TIMEOUT_SECUNDE = 5
    CACHE_SECUNDE = 600  # 10 min

    def __init__(self):
        self.cache_date = None
        self.cache_timp = 0.0

    def proceseaza(self, text):
        este_ploaie = any(cuvant in text for cuvant in CUVINTE_VREME_URATA)
        este_frumos = any(cuvant in text for cuvant in CUVINTE_VREME_GENERAL)

        if not este_ploaie and not este_frumos:
            return None

        date = self.ia_date_vreme()
        if date is None:
            return (
                "I couldn't reach the weather service. "
                "Please check the connection and try again."
            )

        pentru_maine = "tomorrow" in text
        if pentru_maine and len(date["forecast"]["forecastday"]) < 2:
            pentru_maine = False

        if este_ploaie:
            return self.mesaj_ploaie(date, pentru_maine)
        return self.mesaj_general(date, pentru_maine)

    # Retea
    def ia_date_vreme(self):
        # Returneaza dict-ul JSON de la WeatherAPI sau None la eroare de retea.
        # Un singur apel (forecast.json) aduce si current, si forecast pe 2 zile.
        acum = time.time()
        if self.cache_date is not None and acum - self.cache_timp < self.CACHE_SECUNDE:
            return self.cache_date

        if not API_KEY:
            print("X Lipseste API-ul pentru WeatherApi")
            return None

        oras = urllib.parse.quote(LOCATIE)
        url = (
            f"{self.BASE_URL}/forecast.json"
            f"?key={API_KEY}&q={oras}&days=2&aqi=no&alerts=no"
        )

        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=self.TIMEOUT_SECUNDE) as resp:
                date = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print(f"Eroare WeatherAPI: {e}")
            return None
        self.cache_date = date
        self.cache_timp = acum
        return date

    # Construire raspunsuri
    def mesaj_general(self, date, pentru_maine) -> str:
        if pentru_maine:
            zi = date["forecast"]["forecastday"][1]["day"]
            conditie = zi["condition"]["text"]
            temp_max = round(zi["maxtemp_c"])
            temp_min = round(zi["mintemp_c"])
            mesaj = (
                f"Forecast tomorrow in {LOCATIE}. {conditie}. "
                f"The lowest temperature will be {temp_min} and the highest {temp_max} degrees."
            )
            mesaj + self.fraza_vant(zi["maxwind_kph"])
            mesaj += self.fraza_precipitatii(zi)
            return mesaj

        curent = date["current"]
        zi_azi = date["forecast"]["forecastday"][0]["day"]
        conditie = curent["condition"]["text"]
        temp = round(curent["temp_c"])
        resimtit = round(curent["feelslike_c"])

        mesaj = f"It is currently {temp} degrees in {LOCATIE}. {conditie}"
        if abs(resimtit - temp) >= 3:
            mesaj += f" It feels more like {resimtit} degrees."
        mesaj += self.fraza_vant(curent["wind_kph"])
        mesaj += self.fraza_precipitatii(zi_azi)
        return mesaj

    def mesaj_ploaie(self, date, pentru_maine) -> str:
        index = 1 if pentru_maine else 0
        zi = date["forecast"]["forecastday"][index]["day"]
        sansa_ploaie = int(zi.get("daily_chance_of_rain", 0))
        sansa_ninsoare = int(zi.get("daily_chance_of_snow", 0))
        cand = "tomorrow" if pentru_maine else "today"
        vant = self.fraza_vant(zi["maxwind_kph"])

        if sansa_ninsoare >= 50:
            return f"There's a {sansa_ninsoare} percent chance of snow {cand}. You might want to wear thick clothes.{vant}"
        if sansa_ploaie >= 50:
            return f"There's a {sansa_ploaie} percent chance of rain {cand}, so better use an umbrella.{vant}"
        if sansa_ploaie >= 20:
            return f"There's a {sansa_ploaie} percent chance of rain {cand}.{vant}"
        return f"No rain expected {cand}.{vant}"

    def fraza_vant(self, kph) -> str:
        return f" Winds around {round(kph)} kilometers per hour."

    def fraza_precipitatii(self, zi) -> str:
        sansa_ploaie = int(zi.get("daily_chance_of_rain", 0))
        sansa_ninsoare = int(zi.get("daily_chance_of_snow", 0))
        if sansa_ninsoare >= 50:
            return " Snow is expected."
        if sansa_ploaie >= 50:
            return " Rain is expected."
        return ""
