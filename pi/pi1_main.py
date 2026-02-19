import threading
import time
import signal
import sys

from settings.settings import load_settings
# 12
from components.ds import run_door_sensor
from components.dus import run_ultrasonic_door_sensor
from components.dpir1 import run_motion_sensor
from components.dms import run_door_membrane_switch
from components.dl import run_door_led
from components.db import run_door_buzzer

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
except:
    GPIO = None


def shutdown(signal_received=None, frame=None):
    print("\nShutting down application...")
    stop_event.set()

    for thread in threads:
        thread.join()

    if GPIO:
        try:
            GPIO.cleanup()
        except:
            pass

    print("App stopped cleanly.")
    sys.exit(0)


if __name__ == "__main__":

    print("Starting app...")
    settings = load_settings()

    threads = []
    stop_event = threading.Event()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # DS1 – Door Sensor
    ds1_settings = settings.get('PI1', {})['components']['DS1']
    run_door_sensor(ds1_settings, threads, stop_event)
    
    # DUS1 – Ultrasonic Sensor
    dus1_settings = settings.get('PI1', {})['components']['DUS1']
    run_ultrasonic_door_sensor(dus1_settings, threads, stop_event, "DUS1")

    # DPIR1 – Motion Sensor
    dpir1_settings = settings.get('PI1', {})['components']['DPIR1']
    run_motion_sensor(dpir1_settings, threads, stop_event, "DPIR1")

    # DMS – Door Membrane Switch
    dms_settings = settings.get('PI1', {})['components']['DMS']
    run_door_membrane_switch(dms_settings, threads, stop_event)

    # DL – LED
    dl_settings = settings.get('PI1', {})['components']['DL']
    dl = run_door_led(dl_settings, True)
    from components.dl import start_dl_listener
    start_dl_listener(dl_settings, dl)

    # DB – Buzzer
    db_settings = settings.get('PI1', {})['components']['DB']
    db = run_door_buzzer(db_settings, True)
    from components.db import start_db_listener
    start_db_listener(db_settings, db)

    # MAIN LOOP – kontrola aktuatora
    try:
        while True:
            cmd = input("> ").strip().lower()

            if cmd == "exit":
                shutdown()

            elif cmd == "led on":
                dl.on()

            elif cmd == "led off":
                dl.off()

            elif cmd == "buzzer on":
                db.on()

            elif cmd == "buzzer off":
                db.off()
               

            else:
                print("Unknown command. Available: led on, led off, buzzer on, buzzer off, exit")

    except KeyboardInterrupt:
        shutdown()