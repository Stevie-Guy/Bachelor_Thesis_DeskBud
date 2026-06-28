import os
import json
import time
import urllib.parse
import urllib.request
import urllib.error

from pathlib import Path
from flask import request, jsonify

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
REDIRECT_URI = "http://localhost"
SCOPES = "https://www.googleapis.com/auth/calendar.events"
CALE_TOKEN = Path(__file__).parent / "calendar_token.json"


class CalendarAuth:
    """
    Mecanismul de auth pentru Google Calendar.
    Conectarea efectiva e orchestrata de aplicatia Android: butonul de pe tabul
    Calculator cheama /calendar/start, deschide URL-ul OAuth in Chrome Custom
    Tab, userul lipeste in app codul din pagina de eroare, app-ul il trimite la
    /calendar/connect.
    Pi-ul ofera doar API-ul: /calendar/status, /calendar/start,
    /calendar/connect, /calendar/disconnect.
    """

    def __init__(self):
        self.client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
        self.client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")
        self.access_token = None
        self.expira_la = 0.0
        self._refresh_token = self.incarca_refresh_token()

    # Stare
    def este_configurat(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def este_conectat(self) -> bool:
        return self._refresh_token is not None

    # Flask
    def inregistreaza_rute(self, app):
        @app.route("/calendar/status", methods=["GET"])
        def status_calendar():
            return jsonify(
                configured=self.este_configurat(),
                connected=self.este_conectat(),
            )

        @app.route("/calendar/start", methods=["POST"])
        def start_calendar():
            if not self.este_configurat():
                return jsonify(error="not_configured"), 400
            return jsonify(auth_url=self.url_accept())

        @app.route("/calendar/connect", methods=["POST"])
        def conecteaza_calendar():
            json_body = request.get_json(silent=True) or {}
            cod = request.form.get("cod", "") or json_body.get("cod", "")
            if self.conecteaza_cu_cod(cod):
                return jsonify(ok=True)
            return jsonify(ok=False), 400

        @app.route("/calendar/disconnect", methods=["POST"])
        def deconecteaza_calendar():
            self.deconecteaza()
            return jsonify(ok=True)

    # OAuth
    def url_accept(self) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": REDIRECT_URI,
            "response_type": "code",
            "scope": SCOPES,
            "access_type": "offline",
            "prompt": "consent",
        }
        return f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    def conecteaza_cu_cod(self, cod: str) -> bool:
        cod = self.extrage_cod(cod)
        if not cod:
            return False

        date = urllib.parse.urlencode(
            {
                "code": cod,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": REDIRECT_URI,
                "grant_type": "authorization_code",
            }
        ).encode("utf-8")

        try:
            raspuns = self.post(TOKEN_URL, date)
        except urllib.error.HTTPError as e:
            print(f"X Eroare schimb cod: {e.read().decode('utf-8', 'ignore')}")
            return False

        refresh = raspuns.get("refresh_token")
        if not refresh:
            print(
                "X Nu am primit refresh token. Revoca accesul DeskBud din "
                "contul Google si reincearca."
            )
            return False

        self._refresh_token = refresh
        self.salveaza_refresh(refresh)
        self.access_token = raspuns.get("access_token")
        self.expira_la = time.time() + raspuns.get("expires_in", 3600) - 60
        return True

    def returneaza_access_token(self):
        """Returneaza access_token valid sau None daca nu este conectat."""
        if not self._refresh_token:
            return None
        if self.access_token and time.time() < self.expira_la:
            return self.access_token
        return self.refresh_access_token()

    def refresh_access_token(self):
        date = urllib.parse.urlencode(
            {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self._refresh_token,
                "grant_type": "refresh_token",
            }
        ).encode("utf-8")

        try:
            raspuns = self.post(TOKEN_URL, date)
        except urllib.error.HTTPError as e:
            corp = e.read().decode("utf-8", "ignore")
            print(f"X Refresh esuat: {corp}")
            if "invalid_grant" in corp:
                self.deconecteaza()
            return None

        self.access_token = raspuns.get("access_token")
        self.expira_la = time.time() + raspuns.get("expires_in", 3600) - 60
        return self.access_token

    def deconecteaza(self):
        self._refresh_token = None
        self.access_token = None
        self.expira_la = 0.0
        if CALE_TOKEN.exists():
            CALE_TOKEN.unlink()

    # Refresh token persistent
    def incarca_refresh_token(self):
        if CALE_TOKEN.exists():
            try:
                return json.loads(CALE_TOKEN.read_text()).get("refresh_token")
            except Exception as e:
                print(f"Eroare la reincarcarea refresh token: {e}")
                return None
        return None

    def salveaza_refresh(self, refresh: str):
        CALE_TOKEN.write_text(json.dumps({"refresh_token": refresh}))

    # Helperi
    def post(self, url: str, date: bytes) -> dict:
        req = urllib.request.Request(
            url,
            data=date,
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode("utf-8"))

    def extrage_cod(self, text: str) -> str:
        text = text.strip()
        if "code=" in text:
            interogare = urllib.parse.urlparse(text).query or text.split("?", 1)[-1]
            return urllib.parse.parse_qs(interogare).get("code", [""])[0]
        return text
