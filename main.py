import threading
from settings import load_settings
from simulation.components.ds import run_door_sensor
from simulation.components.dus import run_ultrasonic_door_sensor
import time

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
except:
    pass

if __name__ == "__main__":

    print("Starting app.....")
    settings = load_settings()
    threads = []
    stop_event = threading.Event()
    try:
        ds1_settings = settings['DS1']
        run_door_sensor(ds1_settings, threads, stop_event)

        dus1_settings = settings['DUS1']
        run_ultrasonic_door_sensor(dus1_settings, threads, stop_event)
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("Stopping app")
        for thread in threads:
            stop_event.set()