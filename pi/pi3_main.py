import threading
import time
import signal
import sys

from settings.settings import load_settings

from components.dht1 import run_bedroom_dht
from components.dht2 import run_master_bedroom_dht
from components.ir import run_bedroom_ir
from components.dpir3 import run_living_room_dpir
from components.brgb import run_bedroom_rgb
from components.lcd import run_living_room_lcd

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
    dht1_settings = settings.get('PI3', {})['components']['DHT1']
    run_bedroom_dht(dht1_settings, threads, stop_event)

    # DHT2
    dht2_settings = settings.get('PI3', {})['components']['DHT2']
    run_master_bedroom_dht(dht2_settings, threads, stop_event)

    # ir_settings = settings.get('PI3', {})['components']['IR']
    # run_bedroom_ir(ir_settings, threads, stop_event)

    # dpir3_settings = settings.get('PI3', {})['components']['DPIR3']
    # run_living_room_dpir(dpir3_settings, threads, stop_event)

    brgd_settings = settings.get('PI3', {})['components']['BRGB']
    rgb = run_bedroom_rgb(brgd_settings, True)

    lcd_settings = settings.get('PI3', {})['components']['LCD']
    lcd = run_living_room_lcd(lcd_settings, True)

    from components.lcd import start_lcd_listener
    start_lcd_listener(lcd_settings, lcd)
    
    # MAIN LOOP – kontrola aktuatora
    try:
        while True:
            cmd = input("> ").strip().lower()

            if cmd == "exit":
                shutdown()

            elif cmd == "white":
                rgb.white()

            elif cmd == "red":
                rgb.red()

            elif cmd == "green":
                rgb.green()

            elif cmd == "blue":
                rgb.blue()

            elif cmd == "yellow":
                rgb.yellow()

            elif cmd == "light blue":
                rgb.lightBlue()

            elif cmd == "purple":
                rgb.purple()

            elif cmd == "turn off":
                rgb.turnOff()


               

            else:
                print("Unknown command. Available: turno ff, red, green, blue, purple, yellow, light blue, white,  exit")

    except KeyboardInterrupt:
        shutdown()