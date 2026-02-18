import paho.mqtt.publish as publish
import threading
import json
import time
from settings.broker_settings import HOSTNAME, PORT
from simulators.lcd import LCDSimulator

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
except ImportError:
    GPIO = None

lcd_batch = []
publish_data_counter = 0
publish_data_limit = 2
counter_lock = threading.Lock()


def publisher_task(event, batch):
    global publish_data_counter
    while True:
        event.wait()
        with counter_lock:
            local_batch = batch.copy()
            publish_data_counter = 0
            batch.clear()
        publish.multiple(local_batch, hostname=HOSTNAME, port=PORT)
        print(f'Published {len(local_batch)} LCD status values')
        event.clear()


publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, lcd_batch))
publisher_thread.daemon = True
publisher_thread.start()


def lcd_callback(text, settings):
    global publish_data_counter

    payload = {
        "measurement": settings['topic'],
        "simulated": settings.get('simulated', False),
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": text
    }

    with counter_lock:
        lcd_batch.append((settings['topic'], json.dumps(payload), 0, True))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()


def run_living_room_lcd(settings, dht_data_provider):

    if settings.get("simulated", True) or GPIO is None:
        print(f"Using Simulator for {settings['name']}")

        def callback_wrapper(value):
            lcd_callback(value, publish_event, settings)

        simulator = LCDSimulator(callback_wrapper)
        return simulator
        # def simulator_loop():
        #     while True:
        #         for i in range(1, 4):
        #             temp = 20 + i
        #             hum = 50 + i
        #             text = f"DHT{i}: {temp}C\nHum: {hum}%"
        #
        #             print(f"LCD Simulator: {text}")
        #             lcd_callback(text, settings)
        #             time.sleep(5)  # Menja prikaz svakih 5 sekundi

        # thread = threading.Thread(target=simulator_loop)
        # thread.daemon = True
        # thread.start()
    else:
        from actuators.lcd import LCD
        lcd_hw = LCD()

        return lcd_hw
        # from actuators.lcd import LCD
        # lcd_hw = LCD()
        #
        # def hardware_loop():
        #     while True:
        #
        #         for i in range(1, 4):
        #
        #             text = f"DHT{i} Active..."
        #             lcd_hw.display(text)
        #             lcd_callback(text, settings)
        #             time.sleep(5)
        #
        # thread = threading.Thread(target=hardware_loop)
        # thread.daemon = True
        # thread.start()