import threading
import time
import signal
import sys

from settings.settings import load_settings
from components.dht import run_dht
from components.ir import run_bedroom_ir
from components.dpir1 import run_motion_sensor
from components.brgb import run_bedroom_rgb, start_rgb_listener
from components.lcd import run_living_room_lcd, start_lcd_listener

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
    print("Starting Smart Home App (PI3)...")
    settings = load_settings()
    threads = []
    stop_event = threading.Event()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # DHT1 - Bedroom
    dht1_settings = settings.get('PI3', {})['components']['DHT1']
    run_dht(dht1_settings, threads, stop_event, "DHT1")

    # DHT2 - Master Bedroom
    dht2_settings = settings.get('PI3', {})['components']['DHT2']
    run_dht(dht2_settings, threads, stop_event, "DHT2")

    # IR
    ir_settings = settings.get('PI3', {})['components']['IR']
    run_bedroom_ir(ir_settings, threads, stop_event)

    # DPIR3
    dpir3_settings = settings.get('PI3', {})['components']['DPIR3']
    run_motion_sensor(dpir3_settings, threads, stop_event, "DPIR3")

    # BRGB
    brgb_settings = settings.get('PI3', {})['components']['BRGB']
    rgb = run_bedroom_rgb(brgb_settings, True)
    start_rgb_listener(brgb_settings, rgb)

    # LCD
    lcd_settings = settings.get('PI3', {})['components']['LCD']
    lcd = run_living_room_lcd(lcd_settings, True)
    start_lcd_listener(lcd_settings, lcd)

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
                print("Unknown command. Available: turn off, red, green, blue, purple, yellow, light blue, white, exit")

    except KeyboardInterrupt:
        shutdown()
