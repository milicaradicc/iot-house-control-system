import threading
import signal
import sys


from settings.settings import load_settings
from components.dht import run_dht
from components.ir import run_bedroom_ir, ir_callback, publish_event
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

    console_ir_map = {
        "off": "0x300ff22dd",
        "red": "0x300ffc23d",
        "green": "0x300ff629d",
        "blue": "0x300ffa857",
        "white": "0x300ff9867",
        "yellow": "0x300ffb04f",
        "purple": "0x300ff02fd",
        "light blue": "0x300ffc23f"
    }

    try:
        while True:
            cmd = input("PI3-CONSOLE> ").strip().lower()

            if cmd == "exit":
                shutdown()
            elif cmd in console_ir_map:
                hex_code = console_ir_map[cmd]
                ir_callback(hex_code, publish_event, ir_settings)
                publish_event.set()
            else:
                print("Dostupno: off, red, green, blue, yellow, light blue, purple, white, exit")

    except KeyboardInterrupt:
        shutdown()
