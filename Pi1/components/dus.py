# from simulators.dus import run_ultrasonic_door_sensor_simulator
import threading
import time
import json
import paho.mqtt.publish as publish
from broker_settings import HOSTNAME, PORT


dus_batch = []
publish_data_counter = 0
publish_data_limit = 5
counter_lock = threading.Lock()

def publisher_task(event, dus_batch):
    global publish_data_counter, publish_data_limit
    while True:
        event.wait()
        with counter_lock:
            local_dus_batch = dus_batch.copy()
            publish_data_counter = 0
            dus_batch.clear()
        publish.multiple(local_dus_batch, hostname=HOSTNAME, port=PORT)
        print(f'published {publish_data_limit} dus values')
        event.clear()


publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, dus_batch))
publisher_thread.daemon = True
publisher_thread.start()

def dus_callback(distance, publish_event, dus_settings, code = "DUS1", verbose = False):
    global publish_data_counter, publish_data_limit

    if verbose:
        t = time.localtime()
        print("="*20)
        print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
        print(f"Code: {code}")
        print(f"Distance: {distance}")

    distance_payload = {
        "measurement": "Distance",
        "simulated": dus_settings['simulated'],
        "runs_on": dus_settings["runs_on"],
        "name": dus_settings["name"],
        "value": distance
    }

    with counter_lock:
        dus_batch.append(('Distance', json.dumps(distance_payload), 0, True))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()

def run_ultrasonic_door_sensor(settings, threads, stop_event):
    if settings['simulated']:
        from simulators.dus import run_ultrasonic_door_sensor_simulator
        print("Starting dus1 simulator...")
        dus1_thread = threading.Thread(target= run_ultrasonic_door_sensor_simulator, args=(2, dus_callback, stop_event, publish_event, settings))
        dus1_thread.start()
        threads.append(dus1_thread)
        print("DUS1 simulator started!")
    else:
        from sensors.dus import run_dus_loop, DoorUltrasonicSensor
        print("Starting dus1 loop...")
        dus = DoorUltrasonicSensor(settings['trigger_pin'], settings['echo_pin'])
        dus1_thread = threading.Thread(target= run_dus_loop, args=(dus, 2, dus_callback, stop_event, publish_event, settings))
        dus1_thread.start()
        threads.append(dus1_thread)
        print("DUS1 loop started!")