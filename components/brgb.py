from simulators.brgb import RGBLedSimulator
from broker_settings import HOSTNAME, PORT

import paho.mqtt.publish as publish
import threading
import json
import time

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
except ImportError:
    GPIO = None

rgb_batch = []
publish_data_counter = 0
publish_data_limit = 2
counter_lock = threading.Lock()

def publisher_task(event, rgb_batch):
    global publish_data_counter, publish_data_limit
    while True:
        event.wait()
        with counter_lock:
            local_rgb_batch = rgb_batch.copy()
            publish_data_counter = 0
            rgb_batch.clear()
        publish.multiple(local_rgb_batch, hostname=HOSTNAME, port=PORT)
        print(f'published {publish_data_limit} RGB values')
        event.clear()

publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, rgb_batch))
publisher_thread.daemon = True
publisher_thread.start()

def rgb_callback(color, publish_event, rgb_settings, code="RGB"):
    global publish_data_counter, publish_data_limit
    print(color)
    # mapping = {
    #     "off": {"R": 0, "G": 0, "B": 0},
    #     "red": {"R": 1, "G": 0, "B": 0},
    #     "green": {"R": 0, "G": 1, "B": 0},
    #     "blue": {"R": 0, "G": 0, "B": 1},
    #     "white": {"R": 1, "G": 1, "B": 1},
    #     "yellow": {"R": 1, "G": 1, "B": 0},
    #     "purple": {"R": 1, "G": 0, "B": 1},
    #     "lightBlue": {"R": 0, "G": 1, "B": 1},
    # }
    # value = mapping.get(color, {"R": 0, "G": 0, "B": 0})

    color_payload = {
        "measurement": rgb_settings['topic'],
        "simulated": rgb_settings['simulated'],
        "runs_on": rgb_settings["runs_on"],
        "name": rgb_settings["name"],
        "value": color
    }

    with counter_lock:
        rgb_batch.append((rgb_settings['topic'], json.dumps(color_payload), 0, True))
        publish_data_counter += 1
        print(f"[RGB] Prepared to publish: {color_payload}")

    if publish_data_counter >= publish_data_limit:
        publish_event.set()


def run_bedroom_rgb(settings, state=True):
    if settings.get("simulated", True) or GPIO is None:
        def callback_wrapper(value):
            rgb_callback(value, publish_event, settings)
        
        simulator = RGBLedSimulator(callback_wrapper)
        return simulator
    else:
        pin = settings.get("pin")
        if pin is not None:
            GPIO.output(pin, GPIO.HIGH if state else GPIO.LOW)

