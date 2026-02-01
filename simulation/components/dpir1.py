import threading
import time
import json
import paho.mqtt.publish as publish
from broker_settings import HOSTNAME, PORT
from simulators.dpir1 import run_motion_sensor_simulator

dpir_batch = []
publish_data_counter = 0
publish_data_limit = 5
counter_lock = threading.Lock()

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


def dpir1_callback(motion_detected, publish_event, dpir_settings, code="DPIR1", verbose = False):
    global publish_data_counter, publish_data_limit


    if verbose:
        t = time.localtime()
        print("="*20)
        print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
        print(f"Code: {code}")
        print(f"Motion detected: {'YES' if motion_detected else 'NO'}")
        print("="*20)

    state_payload = {
        "measurement": "Motion detected",
        "simulated" : dpir_settings['simulated'],
        "value": motion_detected
    }

    with counter_lock:
        dpir_batch.append(('Motion', json.dumps(state_payload), 0, True ))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()


def run_motion_sensor(settings, threads, stop_event):
    code = "DPIR1"

    if settings.get('simulated', True):
        print("Starting DPIR1 simulator")

        t = threading.Thread(
            target=run_motion_sensor_simulator,
            args=(dpir1_callback, stop_event, publish_event, settings)    #missing argument?
        )

        t.start()
        threads.append(t)

        print("DPIR1 simulator started")

    else:
        from sensors.dpir1 import DPIR1Sensor, run_dpir1_loop

        sensor = DPIR1Sensor(settings['pin'])

        t = threading.Thread(
            target=run_dpir1_loop,
            args=(sensor, settings.get('delay', 2), dpir1_callback, stop_event)
        )

        t.start()
        threads.append(t)

        print("DPIR1 hardware loop started")
