from simulators.db import DBSimulator
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

db_batch = []
publish_data_counter = 0
publish_data_limit = 2
counter_lock = threading.Lock()

def publisher_task(event, db_batch):
    global publish_data_counter, publish_data_limit
    while True:
        event.wait()
        with counter_lock:
            local_db_batch = db_batch.copy()
            publish_data_counter = 0
            db_batch.clear()
        publish.multiple(local_db_batch, hostname=HOSTNAME, port=PORT)
        print(f'published {publish_data_limit} DB values')
        event.clear()


publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, db_batch))
publisher_thread.daemon = True
publisher_thread.start()

def db_callback(value, publish_event, db_settings, code="DB"):
    global publish_data_counter, publish_data_limit
    
    numeric_value = 0
    if value:
        numeric_value = 1 
    else:
        numeric_value = 0

    distance_payload = {
        "measurement": "Buzzer",
        "simulated": db_settings['simulated'],
        "runs_on": db_settings["runs_on"],
        "name": db_settings["name"],
        "value": numeric_value  
    }

    with counter_lock:
        db_batch.append(('Buzzer', json.dumps(distance_payload), 0, True))
        publish_data_counter += 1
        print(f"[DB] Prepared to publish: {distance_payload}")

    if publish_data_counter >= publish_data_limit:
        publish_event.set()


def run_door_buzzer(settings, state=True):
    if settings.get("simulated", True) or GPIO is None:
        def callback_wrapper(value):
            db_callback(value, publish_event, settings)
        
        simulator = DBSimulator(callback_wrapper)
        return simulator
    else:
        pin = settings.get("pin")
        if pin is not None:
            GPIO.output(pin, GPIO.HIGH if state else GPIO.LOW)
