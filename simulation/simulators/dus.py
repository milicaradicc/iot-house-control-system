import time
import random

import time

import random

def generate_ultrasonic_distance(min_cm=10, max_cm=500):
    return random.uniform(min_cm, max_cm)

def run_ultrasonic_door_sensor_simulator(delay, callback, stop_event, publish_event, settings):
    while not stop_event.is_set():
        distance = generate_ultrasonic_distance()
        callback(distance, publish_event, settings)
        time.sleep(delay)
