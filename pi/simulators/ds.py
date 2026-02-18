import time
import random

def generate_door_state():
    """
    Simulates door sensor state.
    True  -> door open
    False -> door closed
    """
    return random.choice([True, False, True, True])

def run_door_sensor_simulator(delay, callback, stop_event, publish_event, settings):
    while not stop_event.is_set():
        state = generate_door_state()
        callback(state, publish_event, settings)
        time.sleep(delay)