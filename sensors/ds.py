import RPi.GPIO as GPIO
import time
from threading import Event

class DoorSensor(object):
    def __init__(self, pin):
        self.pin = pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)  

    def readSensor(self):
        return not GPIO.input(self.pin)

def run_ds_loop(ds, delay, callback, stop_event: Event, code):
    """
    Pokreće beskonačnu petlju čitanja senzora sve dok stop_event nije postavljen.
    
    Args:
        ds (DoorSensor): Instanca senzora vrata
        delay (float): Vreme čekanja između čitanja u sekundama
        callback (function): Funkcija koja prima (state, code)
        stop_event (threading.Event): Event za prekid petlje
        code (any): Kod ili identifikator senzora
    """
    try:
        last_state = None
        while not stop_event.is_set():
            state = ds.readSensor()
            
            # Pozivanje callback-a samo ako se stanje promenilo
            if state != last_state:
                callback(state, code)
                last_state = state

            time.sleep(delay)
    finally:
        # Opcionalno čišćenje GPIO pinova kada se petlja prekine
        GPIO.cleanup(ds.pin)
