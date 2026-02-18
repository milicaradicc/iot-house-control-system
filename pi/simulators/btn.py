import time
import random

def generate_button_pressed():
    return random.choice([True, False])

def run_button_simulator(delay, callback, stop_event, publish_event, settings):
    while not stop_event.is_set():
        state = generate_button_pressed()
        callback(state, publish_event, settings)
        time.sleep(delay)