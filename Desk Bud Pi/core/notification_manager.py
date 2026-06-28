import time
import queue
import threading


class ManagerNotificari:
    """
    Trimite mesaje vocale (remindere) FARA sa intrerupa o conversatie in curs.
    Daca DeskBud raspunde la un prompt, mesajul asteapta pana la `intarziere`
    secunde de liniste DUPA ce conversatia s-a terminat, apoi e rostit.
    Bucla principala marcheaza conversatia cu conversatie_inceput/sfarsit;
    sursele de remindere (monitor prezenta, hidratare) apeleaza trimite().
    """

    def __init__(self, tts, intarziere=3.0):
        self.tts = tts
        self.intarziere = intarziere
        self.coada = queue.Queue()
        self.conversatie = threading.Event()
        threading.Thread(target=self.bucla, daemon=True).start()

    def conversatie_inceput(self):
        self.conversatie.set()

    def conversatie_sfarsit(self):
        self.conversatie.clear()

    def trimite(self, mesaj):
        self.coada.put(mesaj)

    def bucla(self):
        while True:
            mesaj = self.coada.get()
            while not self.asteapta_liniste(self.intarziere):
                pass
            self.tts.vorbeste(mesaj)

    def asteapta_liniste(self, secunde):
        pas = 0.1
        timp_scurs = 0.0
        while timp_scurs < secunde:
            if self.conversatie.is_set():
                while self.conversatie.is_set():
                    time.sleep(pas)
                return False
            time.sleep(pas)
            secunde += pas
        return True
