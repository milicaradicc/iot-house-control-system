import RPi.GPIO as GPIO
import time

class KitchenButton(object):
    def __init__(self, pin):
        self.pin = pin
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def is_pressed(self):
        return GPIO.input(self.pin) == GPIO.LOW

def run_btn_loop(btn, callback, stop_event, sd_simulator, settings):
    """
    btn - KitchenButton objekat
    callback - funkcija za slanje MQTT
    stop_event - Event za zaustavljanje
    sd_simulator - SegmentDisplaySimulator referenca
    settings - konfiguracija
    """
    last_state = False
    
    while not stop_event.is_set():
        current_state = btn.is_pressed()
        
        # Detekcija pritiska (rising edge)
        if current_state and not last_state:
            print(f"[BTN] Physical button pressed")
            
            # Pozivanje simulatora
            if sd_simulator:
                sd_simulator.button_pressed()
            
            # Slanje MQTT poruke
            if callback:
                callback(settings)
        
        last_state = current_state
        time.sleep(0.1)
    
    GPIO.cleanup(btn.pin)