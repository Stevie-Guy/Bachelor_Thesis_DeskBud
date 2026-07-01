import cv2
import mediapipe as mp
from datetime import datetime

# Indici landmark MediaPipe Face Mesh (cu refine_landmarks=True -> 478 puncte)
# Iris (cele 5 puncte aditionale per ochi; primul e centrul)
IRIS_STANGA = (474, 475, 476, 477)
IRIS_DREAPTA = (469, 470, 471, 472)

# Colturile ochilor (interior/exterior) pentru raportul orizontal
OCHI_STANGA_EXT = 263  # coltul exterior ochi stang
OCHI_STANGA_INT = 362  # coltul interior ochi stang
OCHI_DREAPTA_EXT = 33  # coltul exterior ochi drept
OCHI_DREAPTA_INT = 133  # coltul interior ochi drept

# Pragul orizontal: cat de departe de centru (0.5) poate fi irisul si tot
# consideram ca privirea e spre monitor. 0.5 = centrat perfect.
# Valori mai mari de PRAG fata de 0.5 = privire in lateral = distras.
# Camera sub monitor: deplasarea orizontala e fiabila, deci pe ea ne bazam.
PRAG_GAZE_ORIZONTAL = 0.18  # tolerance; regleaza testand cu MOD_DEBUG

# Cate verificari consecutive de distragere pana la recomandare
PRAG_DISTRAS_SEC = 3 * 60  # 3 minute (in secunde de timp la birou)

INTERVAL_COOLDOWN = 60 * 60  # dupa o recomandare, asteapta o ora pana la urmatoarea

MOD_DEBUG = True  # printeaza raportul gaze la fiecare cadru ca sa reglezi pragul


class DetectorAtentie:
    """
    Estimeaza daca utilizatorul e atent la monitor, folosind MediaPipe Face Mesh
    pe ACELASI cadru capturat de MonitorPrezenta (nu face captura proprie).
    Face Detection (din MonitorPrezenta) e poarta: Face Mesh ruleaza doar daca
    fata e prezenta. Dupa 3 min de distragere consecutiva -> recomandare vocala,
    apoi repetata cel mult o data pe ora.
    Warning-urile pot fi oprite vocal; oprirea dureaza doar pe ziua curenta.
    """

    def __init__(self, manager_notificari, interval_verificare):
        self.manager = manager_notificari
        self.interval = interval_verificare
        self.timp_distras = 0.0
        self.timp_distras_la_ultim_mesaj = 0.0
        self.recomandare_trimisa = False

        self.fm = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        # Activarea warning-urilor. Oprirea e valabila doar pe ziua curenta:
        # cand se schimba data, revine automat la activ.
        self.activ = True
        self.data_activ = datetime.now().strftime("%Y-%m-%d")

    def inchide(self):
        try:
            self.fm.close()
        except Exception as e:
            print(f"Eroare la inchiderea Face Mesh: {e}")

    def opreste_warnings(self):
        self.verifica_reset_zilnic()
        self.activ = False
        self.data_activ = datetime.now().strftime("%Y-%m-%d")
        self.reset()

    def porneste_warnings(self):
        self.activ = True
        self.data_activ = datetime.now().strftime("%Y-%m-%d")
        self.reset()

    def warnings_active(self) -> bool:
        self.verifica_reset_zilnic()
        return self.activ

    def verifica_reset_zilnic(self):
        # Oprirea dureaza doar pe ziua respectiva -> la zi noua, revine la activ.
        azi = datetime.now().strftime("%Y-%m-%d")
        if self.data_activ != azi:
            self.activ = True
            self.data_activ = azi

    # Bucla
    def tick(self, prezent: bool, cadru):
        self.verifica_reset_zilnic()

        # Daca warning-urile sunt oprite pe ziua asta, nu evaluam deloc atentia.
        if not self.activ:
            return

        # Poarta: daca nu e prezent la birou, atentia nu se evalueaza.
        # Absenta e gestionata de MonitorPrezenta (sedentarism), aici doar resetam.
        if not prezent:
            self.reset()
            return

        atent = self.estimeaza_atentie(cadru)
        if atent is None:
            # Fata prezenta dar Face Mesh n-a putut estima (ochi inchisi, unghi prost).
            # Nu penalizam: tratam ca atent (nu acumulam distragere pe incertitudine).
            return

        if atent:
            self.reset()
        else:
            self.timp_distras += self.interval
            self.verifica_si_trimite()

    def reset(self):
        self.timp_distras = 0.0
        self.recomandare_trimisa = False
        self.timp_distras_la_ultim_mesaj = 0.0

    def verifica_si_trimite(self):
        if self.timp_distras < PRAG_DISTRAS_SEC:
            return
        destul_de_la_ultim = (
            self.timp_distras - self.timp_distras_la_ultim_mesaj >= INTERVAL_COOLDOWN
        )
        if not self.recomandare_trimisa or destul_de_la_ultim:
            self.manager.trimite(
                "You seem distracted. Maybe take a break if you can't focus."
            )
            self.recomandare_trimisa = True
            self.timp_distras_la_ultim_mesaj = self.timp_distras

    def estimeaza_atentie(self, cadru):
        """
        Returneaza True (atent), False (distras) sau None (nedeterminabil).
        Metoda: raportul orizontal al centrului irisului fata de colturile ochiului.
        Daca irisul e centrat (aproape de 0.5) pe ambii ochi -> privire spre monitor.
        """
        try:
            rgb = cv2.cvtColor(cadru, cv2.COLOR_BGR2RGB)
            rez = self.fm.process(rgb)
        except Exception as e:
            print(f"X Eroare Face Mesh: {e}")
            return None

        if not rez.multi_face_landmarks:
            return None

        pct = rez.multi_face_landmarks[0].landmark

        r_stang = self.raport_orizontal(
            pct, IRIS_STANGA[0], OCHI_STANGA_INT, OCHI_STANGA_EXT
        )
        r_drept = self.raport_orizontal(
            pct, IRIS_DREAPTA[0], OCHI_DREAPTA_INT, OCHI_DREAPTA_EXT
        )

        if r_stang is None and r_drept is None:
            return None

        # Media pe ochii disponibili
        rapoarte = [r for r in (r_stang, r_drept) if r is not None]
        raport_mediu = sum(rapoarte) / len(rapoarte)

        # Deviatia fata de centru (0.5)
        deviatie = abs(raport_mediu - 0.5)

        if MOD_DEBUG:
            print(
                f"[ATENTIE] raport={raport_mediu:.3f} deviatie={deviatie:.3f} "
                f"prag={PRAG_GAZE_ORIZONTAL} -> "
                f"{'ATENT' if deviatie <= PRAG_GAZE_ORIZONTAL else 'DISTRAS'} "
                f"| distras_de={int(self.timp_distras)}s"
            )

        return deviatie <= PRAG_GAZE_ORIZONTAL

    def raport_orizontal(self, pct, idx_iris, idx_int, idx_ext):
        """
        Pozitia orizontala a irisului intre coltul interior si exterior al ochiului.
        0.0 = la coltul interior, 1.0 = la coltul exterior, 0.5 = centrat.
        Returneaza None daca ochiul e prea inchis (colturi suprapuse).
        """
        try:
            x_iris = pct[idx_iris].x
            x_int = pct[idx_int].x
            x_ext = pct[idx_ext].x
        except (IndexError, AttributeError):
            return None

        latime = x_ext - x_int
        if abs(latime) < 1e-6:  # colturi suprapuse / ochi inchis
            return None

        return (x_iris - x_int) / latime
