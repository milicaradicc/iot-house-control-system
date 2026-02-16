import threading
import time
import json
import paho.mqtt.publish as publish
from settings.broker_settings import HOSTNAME, PORT
from simulators.dms import run_door_membrane_switch_simulator

dms_batch = []
publish_data_counter = 0
publish_data_limit = 5
counter_lock = threading.Lock()

def publisher_task(event, dms_batch):
    global publish_data_counter, publish_data_limit
    while True:
        event.wait()
        with counter_lock:
            local_dms_batch = dms_batch.copy()
            publish_data_counter = 0
            dms_batch.clear()
        publish.multiple(local_dms_batch, hostname=HOSTNAME, port=PORT)
        print(f'published {publish_data_limit} dms values')
        event.clear()

publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, dms_batch,))
publisher_thread.daemon = True
publisher_thread.start()

def dms_callback(key, publish_event, dms_settings, code = "DMS", verbose = False):

    global publish_data_counter, publish_data_limit

    if verbose:
        t = time.localtime()
        print("="*20)
        print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
        print(f"Code: {code}")
        print(f"Key: {key}")

    key_payload = {
        "measurement": dms_settings['topic'],
        "simulated" : dms_settings['simulated'],
        "runs_on": dms_settings["runs_on"],
        "name": dms_settings["name"],
        "value": key
    }

    with counter_lock:
        dms_batch.append((dms_settings['topic'], json.dumps(key_payload), 0, True )) 
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()

def run_door_membrane_switch(settings, threads, stop_event):
    code = "DMS"
    if settings['simulated']:
        from simulators.dms import run_door_membrane_switch_simulator
        print("Starting dms simulator...")
        dms_thread = threading.Thread(target= run_door_membrane_switch_simulator, args=(dms_callback, stop_event, publish_event, settings))
        dms_thread.start()
        threads.append(dms_thread)
        print("DMS simulator started!")
    else:
        from sensors.dms import run_dms_loop, DoorMembraneSwitch
        print("Starting dms loop...")
        dms = DoorMembraneSwitch(
            settings['r1'], 
            settings['r2'],
            settings['r3'],
            settings['r4'],
            settings['c1'],
            settings['c2'],
            settings['c3'],
            settings['c4']
            )
        # FIXED: Added publish_event and settings parameters
        dms_thread = threading.Thread(target= run_dms_loop, args=(dms, 0.1, dms_callback, stop_event, code, publish_event, settings))
        dms_thread.start()
        threads.append(dms_thread)
        print("DMS loop started!")