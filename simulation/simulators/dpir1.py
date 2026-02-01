import time
import random

import random

def generate_motion_state():
    """
    Simulates motion sensor state.
    True  -> motion detected
    False -> no motion
    """
    return random.choice([True, False])

import time

def run_motion_sensor_simulator(callback, stop_event, publish_event, settings, delay=2):
    while not stop_event.is_set():
        motion_detected = generate_motion_state()
        callback(motion_detected, publish_event, settings)
        time.sleep(delay)
