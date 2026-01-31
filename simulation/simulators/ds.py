import time
import random

import random

def generate_door_state():
    """
    Simulates door sensor state.
    True  -> door open
    False -> door closed
    """
    return random.choice([True, False])

def run_door_sensor_simulator(callback, stop_event, code, delay=2):
    while not stop_event.is_set():
        state = generate_door_state()
        callback(state, code)
        time.sleep(delay)