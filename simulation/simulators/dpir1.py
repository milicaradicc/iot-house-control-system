import time
import random

def run_motion_sensor_simulator(callback, stop_event, code):
    while not stop_event.is_set():
        motion_detected = random.choice([True, False])
        callback(motion_detected, code)
        time.sleep(2)  # simulira interval ocitavanja
