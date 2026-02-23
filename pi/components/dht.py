import threading
import time
import json
import paho.mqtt.publish as publish
from settings.broker_settings import HOSTNAME, PORT

dht_batch = []
publish_data_counter = 0
publish_data_limit = 6  # 3 DHT × 2 poruke (temp + humidity)
counter_lock = threading.Lock()


def publisher_task(event):
    global publish_data_counter, dht_batch
    while True:
        event.wait()
        with counter_lock:
            local_dht_batch = dht_batch.copy()
            publish_data_counter = 0
            dht_batch.clear()
        if local_dht_batch:
            try:
                publish.multiple(local_dht_batch, hostname=HOSTNAME, port=PORT)
                print(f"📤 Published {len(local_dht_batch)} DHT values")
            except Exception as e:
                print(f"❌ Publish error: {e}")
        event.clear()


publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event,))
publisher_thread.daemon = True
publisher_thread.start()


def dht_callback(humidity, temperature, publish_event, dht_settings, code="DHT1", verbose=False):
    global publish_data_counter, dht_batch

    if verbose:
        t = time.localtime()
        print("=" * 20)
        print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
        print(f"Code: {code}")
        print(f"Humidity: {humidity}%")
        print(f"Temperature: {temperature} °C")

    topic = dht_settings['topic']  # npr. "pi3/dht1"

    temperature_payload = {
        "measurement": topic + "/temp",
        "simulated": dht_settings['simulated'],
        "runs_on": dht_settings["runs_on"],
        "name": dht_settings["name"],
        "value": temperature
    }

    humidity_payload = {
        "measurement": topic + "/humidity",
        "simulated": dht_settings['simulated'],
        "runs_on": dht_settings["runs_on"],
        "name": dht_settings["name"],
        "value": humidity
    }

    with counter_lock:
        dht_batch.append((topic + "/temp",     json.dumps(temperature_payload), 0, True))
        publish_data_counter += 1
        dht_batch.append((topic + "/humidity", json.dumps(humidity_payload),    0, True))
        publish_data_counter += 1
        should_publish = publish_data_counter >= publish_data_limit

    if should_publish:
        publish_event.set()


def run_dht(settings, threads, stop_event, code):
    if settings['simulated']:
        from simulators.dht import run_dht_simulator
        print(f"Starting {code} simulator...")
        dht_thread = threading.Thread(
            target=run_dht_simulator,
            args=(2, dht_callback, stop_event, publish_event, settings)
        )
        dht_thread.start()
        threads.append(dht_thread)
        print(f"✅ {code} simulator started")
    else:
        from sensors.dht import run_dht_loop, DHT
        print(f"Starting {code} loop...")
        dht = DHT(settings['pin'])
        dht_thread = threading.Thread(
            target=run_dht_loop,
            args=(dht, 2, dht_callback, stop_event, code, publish_event, settings)
        )
        dht_thread.start()
        threads.append(dht_thread)
        print(f"✅ {code} loop started")