from ..simulators.dl import DLSimulator
from simulation.broker_settings import HOSTNAME, PORT

import paho.mqtt.publish as publish
import threading
import json
import time

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
except ImportError:
    GPIO = None

dl_batch = []
publish_data_counter = 0
publish_data_limit = 2
counter_lock = threading.Lock()

def publisher_task(event, dl_batch):
    global publish_data_counter, publish_data_limit
    while True:
        event.wait()
        with counter_lock:
            local_dl_batch = dl_batch.copy()
            publish_data_counter = 0
            dl_batch.clear()
        publish.multiple(local_dl_batch, hostname=HOSTNAME, port=PORT)
        print(f'published {publish_data_limit} LED values')
        event.clear()


publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, dl_batch))
publisher_thread.daemon = True
publisher_thread.start()

def dl_callback(value, publish_event, dl_settings, code="DL"):
    global publish_data_counter, publish_data_limit

    numeric_value = 1 if value == "ON" else 0

    distance_payload = {
        "measurement": "LED",
        "simulated": dl_settings['simulated'],
        "runs_on": dl_settings["runs_on"],
        "name": dl_settings["name"],
        "value": numeric_value  
    }

    with counter_lock:
        dl_batch.append(('LED', json.dumps(distance_payload), 0, True))
        publish_data_counter += 1
        print(f"[DL] Prepared to publish: {distance_payload}")

    if publish_data_counter >= publish_data_limit:
        publish_event.set()

def run_door_led(settings, state=True):
    if settings.get("simulated", True) or GPIO is None:
        simulator = DLSimulator()
        return simulator
    else:
        pin = settings.get("pin")
        if pin is not None:
            GPIO.output(pin, GPIO.HIGH if state else GPIO.LOW)