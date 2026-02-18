import threading
import time
import json
import paho.mqtt.publish as publish
from settings.broker_settings import HOSTNAME, PORT

gsg_batch = []
publish_data_counter = 0
publish_data_limit = 5
counter_lock = threading.Lock()

def publisher_task(event, gsg_batch):
    global publish_data_counter, publish_data_limit
    while True:
        event.wait()
        with counter_lock:
            local_gsg_batch = gsg_batch.copy()
            publish_data_counter = 0
            gsg_batch.clear()
        publish.multiple(local_gsg_batch, hostname=HOSTNAME, port=PORT)
        print(f'published {publish_data_limit} gsg values')
        event.clear()


publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, gsg_batch))
publisher_thread.daemon = True
publisher_thread.start()

def gsg_callback(temp, publish_event, gsg_settings, code = "GSG", verbose = False):
    global publish_data_counter, publish_data_limit

    if verbose:
        t = time.localtime()
        print("="*20)
        print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
        print(f"Code: {code}")
        print(f"Temp: {temp}")

    temp_payload = {
        "measurement": gsg_settings['topic'],
        "simulated": gsg_settings['simulated'],
        "runs_on": gsg_settings["runs_on"],
        "name": gsg_settings["name"],
        "value": temp
    }

    with counter_lock:
        gsg_batch.append((gsg_settings['topic'], json.dumps(temp_payload), 0, True))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()

def run_gyroscope(settings, threads, stop_event):
    if settings['simulated']:
        from simulators.gsg import run_gyroscope_simulator
        print("Starting gsg simulator...")
        gsg_thread = threading.Thread(target= run_gyroscope_simulator, args=(2, gsg_callback, stop_event, publish_event, settings))
        gsg_thread.start()
        threads.append(gsg_thread)
        print("GSG simulator started!")
    else:
        pass