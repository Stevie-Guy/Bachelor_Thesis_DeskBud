import json
import time
import threading
from datetime import datetime
from pathlib import Path

import cv2
import mediapipe as mp
from picamera2 import Picamera2

SETTINGS_FILE = Path(__file__).parent / "user_settings.json"

INTERVAL_VERIFICARE = 60
PRAG_ABSENT_PAUZA = 4 * INTERVAL_VERIFICARE
INTERVAL_REMINDER = 5 * 60
PRAG_STAT_JOS_DEFAULT_SEC = 60
PRAG_STAT_JOS_MIN_SEC = 30
PRAG_STAT_JOS_MAX_SEC = 180
DIM_CADRU = (256, 192)


class MonitorPrezenta:
    """Monitorizam prezenta la birou cu Face Detect.
    Picamera2 captureaza cadre la intervale fixe, daca fata e prezanta, cronometrul continua.
    Dupa pauza >= 4 min - reset. Peste prag => reminder vocal asincron repetat la 5 min pana la pauza."""

    def __init__(self, manager_notificari):
        self.manager = manager_notificari
        self.timp_la_birou = 0.0
        self.timp_absent = 0.0
        self.reminder_trimis = False
        self.timp_la_birou_la_ultim_reminder = 0.0

        self.prag = PRAG_STAT_JOS_DEFAULT_SEC * 60
        self.data_prag = datetime.now().strftime("%Y-%m-%d")
        self.incarca_setari()

        self.ruleaza = False
        self.cam = None
        self.fd = None

    def porneste(self):
        if self.ruleaza:
            return
        self.ruleaza = True
        threading.Thread(target=self.bucla, daemon=True).start()
        print("Monitor prezenta la birou pornit ---------------")

    def opreste(self):
        self.ruleaza = False

    def seteaza_prag_minute(self, minute: int):
        if PRAG_STAT_JOS_MIN_SEC <= minute <= PRAG_STAT_JOS_MAX_SEC:
            self.prag = minute * 60
            self.data_prag = datetime.now().strftime("%Y-%m-%d")

            # daca noul prag e peste timpul curent, urmatorul reminder e "primul" la
            # noul prag (timer-ul continua pana acolo)
            if self.timp_la_birou < self.prag:
                self.reminder_trimis = False
            self.salveaza_setari()

    def prag_minute(self) -> int:
        return self.prag // 60

    # Bucla camera
    def bucla(self):
        self.porneste_camera()
        try:
            while self.ruleaza:
                fata = self.detecteaza_fata()
                self.tick(fata)
                time.sleep(INTERVAL_VERIFICARE)
        finally:
            self.opreste_camera()

    def porneste_camera(self):
        self.cam = Picamera2()
        cam_config = self.cam.create_preview_configuration(
            main={"size": (640, 480), "format": "RGB888"}
        )
        self.cam.configure(cam_config)
        self.cam.start()
        self.fd = mp.solutions.face_detection.FaceDetection(
            model_selection=0, min_detection_confidence=0.5
        )
        time.sleep(1)

    def opreste_camera(self):
        try:
            if self.cam:
                self.cam.stop()
            if self.fd:
                self.fd.close()
        except Exception as e:
            print(f"Eroare la oprirea camerei: {e}")

    def detecteaza_fata(self) -> bool:
        try:
            cadru = self.cam.capture_array()
            if cadru.shape[2] == 4:  # XBGR/RGBA -> luam doar 3 canale
                cadru = cadru[:, :, :3]
            mic = cv2.resize(cadru, DIM_CADRU)
            rgb = cv2.cvtColor(mic, cv2.COLOR_BGR2RGB)
            rez = self.fd.process(rgb)
            return bool(rez.detections)
        except Exception as e:
            print(f"X Eroare detectie prezenta: {e}")
            return False

    def tick(self, fata_detectata: bool):
        self.verifica_reset_zilnic()
        if fata_detectata:
            self.timp_absent = 0.0
            self.timp_la_birou += INTERVAL_VERIFICARE
            self.verifica_nevoie_reminder()
        else:
            self.timp_absent += INTERVAL_VERIFICARE
            if self.timp_absent >= PRAG_ABSENT_PAUZA:
                self.reset_birou()

    def verifica_nevoie_reminder(self):
        if self.timp_la_birou < self.prag:
            return
        destul_de_la_ultim = (
            self.timp_la_birou - self.timp_la_birou_la_ultim_reminder
            >= INTERVAL_REMINDER
        )

        if not self.reminder_trimis or destul_de_la_ultim:
            self.trimite_reminder()
            self.reminder_trimis = True
            self.timp_la_birou_la_ultim_reminder = self.timp_la_birou

    def reset_birou(self):
        self.timp_la_birou = 0.0
        self.reminder_trimis = False
        self.timp_la_birou_la_ultim_reminder = 0.0

    def trimite_reminder(self):
        minute = int(self.timp_la_birou // 60)
        mesaj = (
            f"You've been sitting at your desk for about {minute} minutes. "
            "For your well-being, stand up and take a short break."
        )
        self.manager.trimite(mesaj)

    def verifica_reset_zilnic(self):
        azi = datetime.now().strftime("%Y-%m-%d")
        if self.data_prag != azi:
            self.prag = PRAG_STAT_JOS_DEFAULT_SEC * 60
            self.data_prag = azi
            self.salveaza_setari()

    # Persistenta setarilor
    def incarca_setari(self):
        if not SETTINGS_FILE.exists():
            return
        try:
            d = json.loads(SETTINGS_FILE.read_text())
        except Exception as e:
            print(f"Eroare la incarcare setari: {e}")
            return
        azi = datetime.now().strftime("%Y-%m-%d")

        if d.get("data_prag") == azi and "prag_sedentarism_min" in d:
            self.prag = int(d["prag_sedentarism_min"]) * 60
            self.data_prag = azi

    def salveaza_setari(self):
        d = {}
        if SETTINGS_FILE.exists():
            try:
                d = json.loads(SETTINGS_FILE.read_text())
            except Exception as e:
                print(f"Eroare la read din user_settings.json: {e}")
                d = {}
        d["prag_sedentarism_min"] = self.prag // 60
        d["data_prag"] = self.data_prag
        try:
            SETTINGS_FILE.write_text(json.dumps(d, indent=2))
        except Exception as e:
            print(f"Eroare la write in user_settings.json: {e}")

    def secunde_pana_la_reminder(self):
        if self.timp_la_birou <= 0:
            return None

        if not self.reminder_trimis:
            ramas = self.prag - self.timp_la_birou
        else:
            urmatorul = self.timp_la_birou_la_ultim_reminder + INTERVAL_REMINDER
            ramas = urmatorul - self.timp_la_birou
        return max(0, ramas)
