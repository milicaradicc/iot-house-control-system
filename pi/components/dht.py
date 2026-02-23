import threading
import time
import json
import paho.mqtt.publish as publish
from settings.broker_settings import HOSTNAME, PORT

dht_batch = []
publish_data_counter = 0
publish_data_limit = 6 
counter_lock = threading.Lock()

def publisher_task(event):
    global publish_data_counter, dht_batch
    while True:
        # Timeout od 10s sprečava da podaci čekaju zauvek u baferu
        signaled = event.wait(timeout=10.0)
        with counter_lock:
            if dht_batch:
                local_batch = dht_batch.copy()
                dht_batch.clear()
                publish_data_counter = 0
                try:
                    publish.multiple(local_batch, hostname=HOSTNAME, port=PORT)
                    print(f"📤 [MQTT] Published {len(local_batch)} DHT values")
                except Exception as e:
                    print(f"❌ [MQTT] Error: {e}")
        event.clear()

publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event,))
publisher_thread.daemon = True
publisher_thread.start()

def dht_callback(humidity, temperature, publish_event, dht_settings, code="DHT1"):
    global publish_data_counter, dht_batch
    topic = dht_settings['topic']
    
    # Kreiranje unificiranog payload-a
    for m_type, val in [("temp", temperature), ("humidity", humidity)]:
        payload = {
            "measurement": f"{topic}/{m_type}",
            "simulated": dht_settings['simulated'],
            "runs_on": dht_settings["runs_on"],
            "name": dht_settings["name"],
            "value": val
        }
        with counter_lock:
            dht_batch.append((f"{topic}/{m_type}", json.dumps(payload), 0, True))
            publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()

def run_dht(settings, threads, stop_event, code):
    if settings['simulated']:
        from simulators.dht import run_dht_simulator
        print(f"🚀 Starting {code} SIMULATOR")
        t = threading.Thread(target=run_dht_simulator, args=(2, dht_callback, stop_event, publish_event, settings))
    else:
        from sensors.dht import run_dht_loop, DHT
        print(f"🔌 Starting {code} HARDWARE")
        dht = DHT(settings['pin'])
        t = threading.Thread(target=run_dht_loop, args=(dht, 2, dht_callback, stop_event, code, publish_event, settings))
    
    t.start()
    threads.append(t)