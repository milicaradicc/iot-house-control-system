import time
import random

# def generate_values(inital_state = True):
#     state = inital_state
#     while True:
#         state = random.choice([True, False])
#         yield state


def run_door_sensor_simulator(callback, stop_evant, code):
    while not stop_evant.is_set():
        state = random.choice([True, False])
        callback(state, code)
        time.sleep(2)
    