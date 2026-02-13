import threading
import time
import signal
import sys

from settings import load_settings

from components.dht1 import run_bedroom_dht
from components.dht2 import run_master_bedroom_dht
from components.ir import run_bedroom_ir
from components.dpir3 import run_living_room_dpir

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

    # # DHT1 
    # dht1_settings = settings.get('DHT1', {})
    # run_bedroom_dht(dht1_settings, threads, stop_event)

    # # DHT2
    # dht2_settings = settings.get('DHT2', {})
    # run_master_bedroom_dht(dht1_settings, threads, stop_event)

    # ir_settings = settings.get('IR', {})
    # run_bedroom_ir(ir_settings, threads, stop_event)

    dpir3_settings = settings.get('DPIR3', {})
    run_living_room_dpir(dpir3_settings, threads, stop_event)

    # brgd_settings = settings.get('BRGB', {})
    # run_bedroom_rgb(brgd_settings, threads, stop_event)

    # lcd_settings = settings.get('LCD', {})
    # run_living_room_lcd(lcd_settings, threads, stop_event)


    
    # MAIN LOOP – kontrola aktuatora
    try:
        while True:
            cmd = input("> ").strip().lower()

            if cmd == "exit":
                shutdown()

            # elif cmd == "rgb off":
            #     rgb.off()

            # elif cmd == "led off":
            #     dl.off()

            # elif cmd == "buzzer on":
            #     db.on()

            # elif cmd == "buzzer off":
            #     db.off()
               

            else:
                print("Unknown command. Available:  exit")

    except KeyboardInterrupt:
        shutdown()