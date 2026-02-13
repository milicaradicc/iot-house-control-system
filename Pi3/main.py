import threading
import time
import signal
import sys

from settings import load_settings

from components.dht1 import run_bedroom_dht
from components.dht2 import run_master_bedroom_dht

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

    # DHT1 
    dht1_settings = settings.get('DHT1', {})
    run_bedroom_dht(dht1_settings, threads, stop_event)

    # DHT2
    dht2_settings = settings.get('DHT2', {})
    run_master_bedroom_dht(dht1_settings, threads, stop_event)
    
    # MAIN LOOP – kontrola aktuatora
    try:
        while True:
            cmd = input("> ").strip().lower()

            if cmd == "exit":
                shutdown()

            # elif cmd == "led on":
            #     dl.on()

            # elif cmd == "led off":
            #     dl.off()

            # elif cmd == "buzzer on":
            #     db.on()

            # elif cmd == "buzzer off":
            #     db.off()
               

            else:
                print("Unknown command. Available: led on, led off, buzzer on, buzzer off, exit")

    except KeyboardInterrupt:
        shutdown()