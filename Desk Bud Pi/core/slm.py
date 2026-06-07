import json
import urllib.request
import urllib.error


class MotorSLM:
    OLLAMA_URL = "http://localhost:11434"

    def __init__(self, model: str, sys_prompt: str = ""):
        self.model = model
        self.sys_prompt = sys_prompt
        self.istoric = []  # list of {"role": "user"|"assistant", "content": str}

    def este_disponibil(self) -> bool:
        """Verificam daca Ollama ruleaza si modelul este instalat"""
        try:
            req = urllib.request.Request(f"{self.OLLAMA_URL}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            modele = [m["name"] for m in data.get("models", [])]
            return any(self.model.split(":")[0] in m for m in modele)
        except Exception:
            return False

    def incarcare_model_in_ram(self):
        """Trimitem un scurt prompt pentru a incarca modelele in ram"""
        try:
            for m in self.trimite_cerere_si_primeste_tokeni("Hi", num_tokens=3):
                pass
        except Exception as e:
            print(f"Modelul {self.model} nu a putut fi incarcat. Eroare: {e}")

    def chat(self, mesaj_utilizator: str, num_tokens: int = 200, memoreaza=True):
        """
        Streaming pentru raspuns. Yield-uieste tokeni (str) pe masura ce vin.
        Salveaza conversatia in istoric pentru context.
        """
        raspuns_complet = ""
        try:
            for token in self.trimite_cerere_si_primeste_tokeni(
                mesaj_utilizator, num_tokens=num_tokens
            ):
                raspuns_complet += token
                yield token
        finally:
            if raspuns_complet and memoreaza:
                self.istoric.append({"role": "user", "content": mesaj_utilizator})
                self.istoric.append({"role": "assistant", "content": raspuns_complet})

    def reseteaza_istoric(self):
        self.istoric.clear()

    def construieste_mesaje(self, mesaj_utilizator: str):
        mesaje = []
        if self.sys_prompt:
            mesaje.append({"role": "system", "content": self.sys_prompt})
        mesaje.extend(self.istoric)
        mesaje.append({"role": "user", "content": mesaj_utilizator})
        return mesaje

    def trimite_cerere_si_primeste_tokeni(self, mesaj_utilizator: str, num_tokens: int):
        payload = {
            "model": self.model,
            "messages": self.construieste_mesaje(mesaj_utilizator),
            "stream": True,
            "options": {
                "num_predict": num_tokens,
                "temperature": 0.7,
                "top_p": 0.9,  # filtrare, alege doar cele mai logice raspunsuri (pana ajunge la 90%)
            },
        }

        date = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.OLLAMA_URL}/api/chat",
            data=date,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as raspuns:
            for raw_line in raspuns:
                line = raw_line.decode("utf-8").strip()
                if not line:
                    continue
                bucata_json = json.loads(line)
                msg = bucata_json.get("message", {})
                token = msg.get("content", "")

                if token:
                    yield token
                if bucata_json.get("done"):
                    break
