import threading
import time
import json
import paho.mqtt.publish as publish
from settings.broker_settings import HOSTNAME, PORT

dht2_batch = []
publish_data_counter = 0
publish_data_limit = 5
counter_lock = threading.Lock()

def publisher_task(event, dht2_batch):
    global publish_data_counter, publish_data_limit
    while True:
        event.wait()
        with counter_lock:
            local_dht2_batch = dht2_batch.copy()
            publish_data_counter = 0
            dht2_batch.clear()
        publish.multiple(local_dht2_batch, hostname=HOSTNAME, port=PORT)
        print(f'published {publish_data_limit} dht2 values')
        event.clear()

publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, dht2_batch,))
publisher_thread.daemon = True
publisher_thread.start()

def dht2_callback(humidity, temperature, publish_event, dht2_settings, code = "DHT2", verbose = False):
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
        "simulated": dht2_settings['simulated'],
        "runs_on": dht2_settings["runs_on"],
        "name": dht2_settings["name"],
        "value": humidity  
    }

    temperature_payload = {
        "measurement": "Temperature",          # a temperature?
        "simulated": dht2_settings['simulated'],
        "runs_on": dht2_settings["runs_on"],
        "name": dht2_settings["name"],
        "value": temperature  
    }

    with counter_lock:
        dht2_batch.append(('Humidity', json.dumps(humidity_payload), 0, True))
        publish_data_counter += 1

        dht2_batch.append(('Temperature', json.dumps(temperature_payload), 0, True))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()

def run_master_bedroom_dht(settings, threads, stop_event):
        
        code = "DHT2"

        if settings['simulated']:
            print("Starting dht2 sumilator")
            from simulators.dht2 import run_master_bedroom_dht_simulator
            print("Starting dht2 simulator...")
            dht2_thread = threading.Thread(target = run_master_bedroom_dht_simulator, args=(2, dht2_callback, stop_event, publish_event, settings))
            dht2_thread.start()
            threads.append(dht2_thread)
            print("dht2 sumilator started")
        else:
            from sensors.dht import run_dht_loop, DHT
            print("Starting dht2 loop")
            dht = DHT(settings['pin'])
            dht2_thread = threading.Thread(target=run_dht_loop, args=(dht, 2, dht2_callback, stop_event, code))
            dht2_thread.start()
            threads.append(dht2_thread)
            print("dht2 loop started")
