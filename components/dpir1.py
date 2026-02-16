import threading
import time
import json
import paho.mqtt.publish as publish
from settings.broker_settings import HOSTNAME, PORT
from simulators.dpir1 import run_motion_sensor_simulator

dpir_batch = []
publish_data_counter = 0
publish_data_limit = 5
counter_lock = threading.Lock()

# LED kontrola
led_timer = None
led_instance = None

def publisher_task(event, dpir_batch):
    global publish_data_counter, publish_data_limit
    while True:
        event.wait()
        with counter_lock:
            local_dpir_batch = dpir_batch.copy()
            publish_data_counter = 0
            dpir_batch.clear()
        publish.multiple(local_dpir_batch, hostname=HOSTNAME, port=PORT)
        print(f'published {publish_data_limit} dpir values')
        event.clear()

publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, dpir_batch,))
publisher_thread.daemon = True
publisher_thread.start()


def turn_off_led_after_delay():
    """Timer funkcija koja gasi LED nakon 10 sekundi"""
    global led_instance
    time.sleep(10)
    if led_instance:
        led_instance.off()
        print("[DPIR1] LED automatically turned OFF after 10 seconds")


def set_led_instance(led):
    """Postavlja LED instancu za kontrolu iz DPIR1 callback-a"""
    global led_instance
    led_instance = led
    print("[DPIR1] LED instance registered for motion control")


def dpir1_callback(motion_detected, publish_event, dpir_settings, code="DPIR1", verbose=False):
    global publish_data_counter, publish_data_limit, led_timer, led_instance

    if verbose:
        t = time.localtime()
        print("="*20)
        print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
        print(f"Code: {code}")
        print(f"Motion detected: {'YES' if motion_detected else 'NO'}")
        print("="*20)

    # Kontrola LED-a kada je detektovan pokret
    if motion_detected and led_instance:
        # Uključi LED
        led_instance.on()
        print("[DPIR1] Motion detected! LED turned ON for 10 seconds")
        
        # Pokreni novi timer za gašenje nakon 10 sekundi
        led_timer = threading.Thread(target=turn_off_led_after_delay, daemon=True)
        led_timer.start()

    motion_payload = {
        "measurement": dpir_settings['topic'],
        "simulated": dpir_settings['simulated'],
        "runs_on": dpir_settings["runs_on"],
        "name": dpir_settings["name"],
        "value": 1 if motion_detected else 0 
    }

    with counter_lock:
        dpir_batch.append((dpir_settings['topic'], json.dumps(motion_payload), 0, True))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()


def run_motion_sensor(settings, threads, stop_event, verbose = False):
    code = "DPIR1"

    if settings.get('simulated', True):
        print("Starting DPIR1 simulator")

        t = threading.Thread(
            target=run_motion_sensor_simulator,
            args=(dpir1_callback, stop_event, publish_event, settings, verbose)    
        )

        t.start()
        threads.append(t)

        print("DPIR1 simulator started")

    else:
        from sensors.dpir1 import DPIR1Sensor, run_dpir1_loop

        sensor = DPIR1Sensor(settings['pin'])

        t = threading.Thread(
            target=run_dpir1_loop,
            args=(sensor, settings.get('delay', 0.5), dpir1_callback, stop_event, code, publish_event, settings)
        )

        t.start()
        threads.append(t)

        print("DPIR1 hardware loop started")