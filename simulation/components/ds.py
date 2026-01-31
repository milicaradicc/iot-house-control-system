import threading
import time
import json
import paho.mqtt.publish as publish
from simulation.broker_settings import HOSTNAME, PORT
from simulation.simulators.ds import run_door_sensor_simulator

ds_batch = []
publish_data_counter = 0
publish_data_limit = 5
counter_lock = threading.Lock()

def publisher_task(event, dus_batch):
    global publish_data_counter, publish_data_limit
    while True:
        event.wait()
        with counter_lock:
            local_ds_batch = ds_batch.copy()
            publish_data_counter = 0
            ds_batch.clear()
        publish.multiple(local_ds_batch, hostname=HOSTNAME, port=PORT)
        print(f'published {publish_data_limit} ds values')
        event.clear()


publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, ds_batch,))
publisher_thread.daemon = True
publisher_thread.start()

def ds_callback(state, publish_event, ds_settings, code = "DS1", verbose = False):
    global publish_data_counter, publish_data_limit

    if verbose:
        t = time.localtime()
        print("="*20)
        print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
        print(f"Code: {code}")
        print(f"State: {'CLOSED' if state else 'OPEN'}")
    
    state_payload = {
        "measurement": "State",
        "simulated": ds_settings['simulated'],
        "runs_on": ds_settings["runs_on"],
        "name": ds_settings["name"],
        "value": state
    }

    with counter_lock:
        ds_batch.append(('State', json.dumps(state_payload), 0, True))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()

def run_door_sensor(settings, threads, stop_event):

    code = "DS1"

    if settings['simulated']:
        from ..simulators.ds import run_door_sensor_simulator
        print("Starting ds1 simulator...")
        ds1_thread = threading.Thread(target= run_door_sensor_simulator, args = (2, ds_callback, stop_event, publish_event, settings))
        ds1_thread.start()
        threads.append(ds1_thread)
        print("DS1 simulator started!")
    else:
        from ..sensors.ds import run_ds_loop, DoorSensor
        print("Starting ds1 loop...")
        ds = DoorSensor(settings['pin'])
        ds1_thread = threading.Thread(target= run_ds_loop, args=(ds, 0.1, ds_callback, stop_event, code))
        ds1_thread.start()
        threads.append(ds1_thread)
        print("DS1 loop started!")