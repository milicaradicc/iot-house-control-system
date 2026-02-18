import threading
import time
import json
import paho.mqtt.publish as publish
from settings.broker_settings import HOSTNAME, PORT

dht1_batch = []
publish_data_counter = 0
publish_data_limit = 5
counter_lock = threading.Lock()

def publisher_task(event, dht1_batch):
    global publish_data_counter, publish_data_limit
    while True:
        event.wait()
        with counter_lock:
            local_dht1_batch = dht1_batch.copy()
            publish_data_counter = 0
            dht1_batch.clear()
        publish.multiple(local_dht1_batch, hostname=HOSTNAME, port=PORT)
        print(f'published {publish_data_limit} dht1 values')
        event.clear()

publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, dht1_batch,))
publisher_thread.daemon = True
publisher_thread.start()

def dht1_callback(humidity, temperature, publish_event, dht1_settings, code = "DHT1", verbose = False):
    global publish_data_counter, publish_data_limit

    if verbose:
        t = time.localtime()
        print("="*20)
        print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
        print(f"Code: {code}")
        print(f"Humidity: {humidity}%")
        print(f"Temperature: {temperature} °C")

    humidity_payload = {
        "measurement": "Humidity",
        "simulated": dht1_settings['simulated'],
        "runs_on": dht1_settings["runs_on"],
        "name": dht1_settings["name"],
        "value": humidity  
    }

    temperature_payload = {
        "measurement": "Temperature",          # a temperature?
        "simulated": dht1_settings['simulated'],
        "runs_on": dht1_settings["runs_on"],
        "name": dht1_settings["name"],
        "value": temperature  
    }

    with counter_lock:
        dht1_batch.append((dht1_settings['topic'], json.dumps(humidity_payload), 0, True))
        publish_data_counter += 1

        dht1_batch.append((dht1_settings['topic'], json.dumps(temperature_payload), 0, True))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()

def run_bedroom_dht(settings, threads, stop_event):
        
        code = "DHT1"
        if settings['simulated']:
            print("Starting dht1 sumilator")
            from simulators.dht1 import run_bedroom_dht_simulator
            print("Starting dht1 simulator...")
            dht1_thread = threading.Thread(target = run_bedroom_dht_simulator, args=(2, dht1_callback, stop_event, publish_event, settings))
            dht1_thread.start()
            threads.append(dht1_thread)
            print("DHT1 sumilator started")
        else:
            from sensors.dht import run_dht_loop, DHT
            print("Starting dht1 loop")
            dht = DHT(settings['pin'])
            dht1_thread = threading.Thread(target=run_dht_loop, args=(dht, 2, dht1_callback, stop_event, code))
            dht1_thread.start()
            threads.append(dht1_thread)
            print("Dht1 loop started")
