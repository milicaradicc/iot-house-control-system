import time
import random

def run_ultrasonic_door_sensor_simulator(callback, stop_event, code):
    while not stop_event.is_set():
        distance = random.uniform(10, 500) #cm
        callback(distance, code)
        time.sleep(2)