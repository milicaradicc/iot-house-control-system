import threading
import paho.mqtt.publish as publish
import json

# Globalne varijable
people_count = 0
distance_history = {"DUS1": [], "DUS2": []}
state_lock = threading.Lock()

def update_people_count(delta, sensor_name, hostname, port):
    global people_count
    with state_lock:
        people_count += delta
        # Osiguravamo da broj ne ode ispod nule
        if people_count < 0: people_count = 0
        
        payload = {
            "measurement": "people_count",
            "value": people_count,
            "triggered_by": sensor_name
        }
        publish.single("home/people_count", json.dumps(payload), hostname=hostname, port=port)
        print(f"\n[BROJAČ] Stanje u objektu: {people_count} (Izmena: {delta} od {sensor_name})")