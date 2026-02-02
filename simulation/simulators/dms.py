import random

def generate_membrane_key():
    """
    Simulates membrane keypad key press.
    """
    return random.choice([
        "1", "2", "3", "A",
        "4", "5", "6", "B",
        "7", "8", "9", "C",
        "*", "0", "#", "D"
    ])

import time

def run_door_membrane_switch_simulator(callback, stop_event, publish_event,settings, delay=2):
    while not stop_event.is_set():
        clicked_value = generate_membrane_key()
        callback(clicked_value, publish_event, settings)
        time.sleep(delay)
