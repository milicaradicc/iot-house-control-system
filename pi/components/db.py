from actuators.db import DoorBuzzer
from simulators.db import DBSimulator
from settings.broker_settings import HOSTNAME, PORT

import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt
import threading
import json
import uuid

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
except ImportError:
    GPIO = None

db_batch = []
publish_data_counter = 0
publish_data_limit = 2
counter_lock = threading.Lock()
publish_event = threading.Event()


def publisher_task(event):
    global publish_data_counter
    while True:
        event.wait()
        with counter_lock:
            local_db_batch = db_batch.copy()
            publish_data_counter = 0
            db_batch.clear()
        if local_db_batch:
            try:
                publish.multiple(local_db_batch, hostname=HOSTNAME, port=PORT)
                print(f"📤 Published {len(local_db_batch)} DB values")
            except Exception as e:
                print(f"❌ DB Publish error: {e}")
        event.clear()


publisher_thread = threading.Thread(target=publisher_task, args=(publish_event,))
publisher_thread.daemon = True
publisher_thread.start()


def db_callback(value, publish_event, db_settings, code="DB"):
    global publish_data_counter

    numeric_value = 1 if value else 0

    payload = {
        "measurement": db_settings['topic'],
        "simulated":   db_settings['simulated'],
        "runs_on":     db_settings["runs_on"],
        "name":        db_settings["name"],
        "value":       numeric_value
    }

    with counter_lock:
        db_batch.append((db_settings['topic'], json.dumps(payload), 0, True))
        publish_data_counter += 1
        should_publish = publish_data_counter >= publish_data_limit
        print(f"[DB] Prepared: value={numeric_value}")

    if should_publish:
        publish_event.set()


def start_db_listener(db_settings, db_instance):
    def on_connect(client, userdata, flags, rc):
        print(f"[DB Listener] Connected rc={rc}")
        if rc == 0:
            client.subscribe("commands/PI1/DB")
            print("✅ DB listener subscribed to commands/PI1/DB")
        else:
            print(f"❌ DB listener connection failed: rc={rc}")

    def on_message(client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            value = payload.get("value", False)
            print(f"[DB] 📩 Command received: value={value}")
            if value:
                print("[DB] 🔊 Turning buzzer ON")
                db_instance.on()
            else:
                print("[DB] 🔇 Turning buzzer OFF")
                db_instance.off()
        except Exception as e:
            print(f"❌ DB on_message error: {e}")

    client = mqtt.Client(client_id=f"db_listener_{uuid.uuid4()}")
    client.on_connect = on_connect
    client.on_message = on_message
    print(f"[DB Listener] Connecting to {HOSTNAME}:{PORT}...")
    client.connect(HOSTNAME, PORT, 60)
    client.loop_start()
    return client


def run_door_buzzer(settings, threads, stop_event):
    def callback_wrapper(value):
        db_callback(value, publish_event, settings)

    if settings.get("simulated", True) or GPIO is None:
        print("Starting DB simulator...")
        db_instance = DBSimulator(callback_wrapper)
    else:
        pin = settings.get("pin")
        print(f"Starting DB on pin {pin}...")
        db_instance = DoorBuzzer(pin, callback_wrapper)

    listener_client = start_db_listener(settings, db_instance)

    print("✅ DB started")
    return db_instance, listener_client