from actuators.dl import DoorLight
from simulators.dl import DLSimulator
from settings.broker_settings import HOSTNAME, PORT

import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt
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



def start_dl_listener(dl_settings, dl_instance):
    def on_message(client, userdata, msg):
        payload = json.loads(msg.payload.decode("utf-8"))
        value = payload.get("value")
        
        if value is True:
            dl_instance.on()
        elif value is False:
            dl_instance.off()
        else:
            # Nema eksplicitne vrijednosti → toggle
            dl_instance.toggle()

    client = mqtt.Client()
    client.on_message = on_message
    client.connect(HOSTNAME, PORT, 60)
    client.subscribe("commands/PI1/DL")
    client.loop_start()


publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, dl_batch))
publisher_thread.daemon = True
publisher_thread.start()

def dl_callback(value, publish_event, dl_settings, code="DL"):
    global publish_data_counter, publish_data_limit

    if value:
        numeric_value = 1 
    else:
        numeric_value = 0

    print(numeric_value)

    distance_payload = {
        "measurement": dl_settings['topic'],
        "simulated": dl_settings['simulated'],
        "runs_on": dl_settings["runs_on"],
        "name": dl_settings["name"],
        "value": numeric_value  
    }

    with counter_lock:
        dl_batch.append((dl_settings['topic'], json.dumps(distance_payload), 0, True))
        publish_data_counter += 1
        print(f"[DL] Prepared to publish: {distance_payload}")

    if publish_data_counter >= publish_data_limit:
        publish_event.set()



def run_door_led(settings, state=True):
    def callback_wrapper(value):
        dl_callback(value, publish_event, settings)

    if settings.get("simulated", True) or GPIO is None:
        simulator = DLSimulator(callback_wrapper)
        return simulator
    else:
        pin = settings.get("pin")
        if pin is None:
            raise ValueError("DL hardware mode zahtijeva 'pin' u settings")
        hardware = DoorLight(pin, callback_wrapper)
        # Postavi inicijalno stanje
        if state:
            hardware.on()
        return hardware