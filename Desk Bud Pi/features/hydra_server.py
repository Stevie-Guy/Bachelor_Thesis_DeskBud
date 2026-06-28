from flask import Flask, request, jsonify
from datetime import datetime
import schedule
import threading
import time
import json
from pathlib import Path

from core.tts import TextToSpeech
from core.audio_io import AudioIO


CONFIG_FILE = Path(__file__).parent / "hydration_config.json"


class HydraServer:
    def __init__(
        self, audio_io: AudioIO, tts: TextToSpeech, manager_notificari, asistent=None
    ):
        self.audio_io = audio_io
        self.tts = tts
        self.app = Flask(__name__)
        self.manager_notificari = manager_notificari

        self.status_curent = {
            "ml_bauti": 0,
            "goal": 2000,
            "procent": 0,
            "data": "",
            "ultima_actualizare": "",
        }

        self.config = {
            "numar_remindere": 3,
            "ora_start": 12,
            "ora_final": 22,
        }

        self._inregistreaza_rute()

    # ── config persistence ─────────────────────────────────────────────────

    def incarca_config(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r") as f:
                    self.config = json.load(f)
                print(f"Config incarcat: {self.config}")
            except Exception as e:
                print(f"Eroare la incarcare config: {e}")

    def salveaza_config(self):
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Eroare la salvare config: {e}")

    # ── logica remindere ───────────────────────────────────────────────────

    def calculeaza_ore_reminder(self, numar):
        ora_start = self.config["ora_start"]
        ora_final = self.config["ora_final"]
        durata_total = (ora_final - ora_start) * 60
        interval_minute = durata_total / numar

        ore = []
        for i in range(1, numar + 1):
            minute_dupa_start = int(interval_minute * i)
            ora = ora_start + (minute_dupa_start // 60)
            minut = minute_dupa_start % 60
            ore.append((i, f"{ora:02d}:{minut:02d}"))

        return ore

    def verifica_nevoie_reminder(self, numar_reminder, total_remindere):
        azi = datetime.now().strftime("%Y-%m-%d")

        if (
            not self.status_curent["ultima_actualizare"]
            or self.status_curent["data"] != azi
        ):
            mesaj = "Hey, it's time to drink some water."
            self.manager_notificari.trimite(mesaj)
            return

        ml_bauti = self.status_curent["ml_bauti"]
        goal = self.status_curent["goal"]

        prag_asteptat = (numar_reminder / total_remindere) * goal

        print(
            f"\nReminder: {numar_reminder}/{total_remindere} "
            f"\nVerificare: {ml_bauti}ml / {prag_asteptat:.0f}ml"
        )

        if ml_bauti >= prag_asteptat:
            print("Hidratare ok, skip reminder")
            return

        procent = int((ml_bauti / goal) * 100)

        if procent >= int((numar_reminder / total_remindere) * 100) - 50:
            mesaj = f"Hey, you are currently at {procent} percent of your daily water goal. You may consider drinking some water."
        else:
            mesaj = f"Hey, you are only at {procent} percent of your daily water goal. You should drink some water soon."

        print(f"Reminder vocal: {mesaj}")
        self.manager_notificari.trimite(mesaj)

    def programeaza_remindere(self):
        schedule.clear()
        numar = self.config["numar_remindere"]
        ore = self.calculeaza_ore_reminder(numar)

        print("\nRemindere: ")
        for index, ora in ore:
            print(f"  Reminder {index}/{numar} la ora {ora}")
            schedule.every().day.at(ora).do(
                self.verifica_nevoie_reminder,
                numar_reminder=index,
                total_remindere=numar,
            )

    def _ruleaza_scheduler(self):
        while True:
            schedule.run_pending()
            time.sleep(60)

    # ── rute API ───────────────────────────────────────────────────────────

    def _inregistreaza_rute(self):
        @self.app.route("/api/hydration/status", methods=["POST"])
        def primeste_status():
            try:
                date = request.get_json()
                if not date:
                    return jsonify({"eroare": "Nu s-au trimis date json"}), 400

                camp_obligatoriu = ["ml_bauti", "goal", "procent", "data"]
                for camp in camp_obligatoriu:
                    if camp not in date:
                        return jsonify({"eroare": f"Lipseste campul {camp}"}), 400

                self.status_curent["ml_bauti"] = date["ml_bauti"]
                self.status_curent["goal"] = date["goal"]
                self.status_curent["procent"] = date["procent"]
                self.status_curent["data"] = date["data"]
                self.status_curent["ultima_actualizare"] = datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

                print(
                    f"[{self.status_curent['ultima_actualizare']}] Status primit: "
                    f"{date['ml_bauti']}/{date['goal']} ml ({date['procent']}%)"
                )

                return jsonify(
                    {
                        "succes": True,
                        "mesaj": "Status actualizat",
                        "status": self.status_curent,
                    }
                ), 200

            except Exception as e:
                print(f"Eroare: {e}")
                return jsonify({"eroare": str(e)}), 500

        @self.app.route("/api/hydration/status", methods=["GET"])
        def returneaza_status():
            return jsonify(self.status_curent), 200

        @self.app.route("/api/ping", methods=["GET"])
        def ping():
            return jsonify({"raspuns": "pong", "timp": datetime.now().isoformat()}), 200

        @self.app.route("/api/config/reminders", methods=["GET"])
        def get_numar_remindere():
            return jsonify(
                {
                    "numar_remindere": self.config["numar_remindere"],
                    "ora_start": self.config["ora_start"],
                    "ora_final": self.config["ora_final"],
                    "ore": self.calculeaza_ore_reminder(self.config["numar_remindere"]),
                }
            ), 200

        @self.app.route("/api/config/reminders", methods=["POST"])
        def set_numar_remindere():
            try:
                date = request.get_json()
                if (
                    not date
                    or "ora_start" not in date
                    or "ora_final" not in date
                    or "numar_remindere" not in date
                ):
                    return jsonify(
                        {
                            "eroare": "Campurile 'ora_start', 'ora_final' si 'numar_remindere' lipsesc"
                        }
                    ), 400

                ora_start = int(date["ora_start"])
                ora_final = int(date["ora_final"])
                numar = int(date["numar_remindere"])

                self.config["ora_start"] = ora_start
                self.config["ora_final"] = ora_final
                self.config["numar_remindere"] = numar
                self.salveaza_config()
                self.programeaza_remindere()

                return jsonify(
                    {
                        "succes": True,
                        "ora_start": ora_start,
                        "ora_final": ora_final,
                        "numar_remindere": numar,
                        "ore": self.calculeaza_ore_reminder(numar),
                    }
                ), 200
            except (ValueError, TypeError) as e:
                return jsonify({"eroare": f"Valoare invalida: {e}"}), 400

    # ── lifecycle

    def porneste(self):
        """Apelat din assistant.py — incarca config, programeaza, porneste Flask in thread."""
        self.incarca_config()
        self.programeaza_remindere()

        thread_scheduler = threading.Thread(target=self._ruleaza_scheduler, daemon=True)
        thread_scheduler.start()
        print("✓ Hydra scheduler pornit in background")

        thread_flask = threading.Thread(target=self._porneste_flask, daemon=True)
        thread_flask.start()
        print("✓ Hydra Flask server pornit pe portul 5000")

    def _porneste_flask(self):
        self.app.run(
            host="0.0.0.0", port=5000, debug=False, use_reloader=False, threaded=True
        )
