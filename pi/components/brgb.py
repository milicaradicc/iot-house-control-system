from simulators.brgb import RGBLedSimulator
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
        print(f'published {len(local_rgb_batch)} RGB values')
        event.clear()


publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, rgb_batch))
publisher_thread.daemon = True
publisher_thread.start()


def rgb_callback(color, publish_event, rgb_settings, code="RGB"):
    global publish_data_counter, publish_data_limit

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


def start_rgb_listener(settings, rgb_instance):
    def on_message(client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            color = payload.get("color")

            if color == "red":
                rgb_instance.red()
            elif color == "green":
                rgb_instance.green()
            elif color == "blue":
                rgb_instance.blue()
            elif color == "white":
                rgb_instance.white()
            elif color == "light blue":
                rgb_instance.lightBlue()
            elif color == "purple":
                rgb_instance.purple()
            elif color == "yellow":
                rgb_instance.yellow()
            elif color == "off":
                rgb_instance.turnOff()
            else:
                print(f"[RGB] Unknown color: {color}")
        except Exception as e:
            print(f"[RGB] Error handling message: {e}")

    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.on_message = on_message
    client.connect(HOSTNAME, PORT, 60)
    client.subscribe("commands/PI3/BRGB")
    client.loop_start()


def run_bedroom_rgb(settings, state=True):
    if settings.get("simulated", True) or GPIO is None:
        def callback_wrapper(value):
            rgb_callback(value, publish_event, settings)

        simulator = RGBLedSimulator(callback_wrapper)
        return simulator
    else:
        from actuators.brgb import RGBLed

        def callback_wrapper(value):
            rgb_callback(value, publish_event, settings)

        rgb = RGBLed(
            r_pin=settings.get("red_pin"),
            g_pin=settings.get("green_pin"),
            b_pin=settings.get("blue_pin"),
            callback=callback_wrapper
        )
        return rgb