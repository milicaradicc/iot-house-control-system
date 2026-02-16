import threading
import time
import paho.mqtt.publish as publish
from settings.broker_settings import HOSTNAME, PORT
import json

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
except ImportError:
    GPIO = None


def run_button(settings, threads, stop_event, sd_simulator=None):
    """
    sd_simulator - referenca na SegmentDisplaySimulator objekat
    """
    # Čuvamo referencu na simulator globalno za pristup iz main.py
    settings['_sd_simulator'] = sd_simulator
    
    if settings.get("simulated", True) or GPIO is None:
        print(f"[BTN] Button {settings['name']} initialized in SIMULATION mode")
        print(f"[BTN] Use 'b' command in console to press the button")
        
        # U simuliranom modu ne pokrećemo thread, 
        # dugme se aktivira ručno preko komande
        
    else:
        pin = settings.get("pin")
        if pin is None:
            print(f"[BTN] Error: No pin defined for {settings['name']}")
            return
        
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        def button_thread():
            last_state = GPIO.HIGH
            
            while not stop_event.is_set():
                current_state = GPIO.input(pin)
                
                # Detekcija pada signala (pritisnuto dugme)
                if last_state == GPIO.HIGH and current_state == GPIO.LOW:
                    print(f"[BTN] Button {settings['name']} pressed")
                    
                    # Pozivanje button_pressed na simulatoru
                    if sd_simulator:
                        sd_simulator.button_pressed()
                    
                    # Slanje MQTT poruke
                    payload = {
                        "measurement": settings['topic'],
                        "simulated": False,
                        "runs_on": settings["runs_on"],
                        "name": settings["name"],
                        "value": 1
                    }
                    
                    publish.single(
                        settings['topic'],
                        json.dumps(payload),
                        hostname=HOSTNAME,
                        port=PORT
                    )
                    
                    time.sleep(0.3)  # Debounce
                
                last_state = current_state
                time.sleep(0.01)
        
        thread = threading.Thread(target=button_thread)
        thread.daemon = True
        thread.start()
        threads.append(thread)
        
        print(f"[BTN] Button {settings['name']} initialized on GPIO {pin}")


def simulate_button_press(settings):
    """
    Funkcija za simuliranje pritiska dugmeta iz konzole
    """
    sd_simulator = settings.get('_sd_simulator')
    
    if sd_simulator:
        sd_simulator.button_pressed()
        
        # Slanje MQTT poruke
        payload = {
            "measurement": settings['topic'],
            "simulated": settings['simulated'],
            "runs_on": settings["runs_on"],
            "name": settings["name"],
            "value": 1
        }
        
        try:
            publish.single(
                settings['topic'],
                json.dumps(payload),
                hostname=HOSTNAME,
                port=PORT
            )
        except Exception as e:
            print(f"[BTN] Error publishing MQTT: {e}")
    else:
        print("[BTN] Error: Simulator not available")