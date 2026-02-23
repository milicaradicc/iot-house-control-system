import time
import random
import math

def run_gyroscope_simulator(delay, callback, stop_event, publish_event, settings, verbose=False):
    while not stop_event.is_set():
        idle_count = random.randint(15, 25)
        print(f"[GSG SIM] Phase: idle ({idle_count} readings)")
        for _ in range(idle_count):
            if stop_event.is_set():
                return
            magnitude = 1.0 + random.uniform(-0.05, 0.05)
            callback(False, magnitude, publish_event, settings, verbose=verbose) 
            time.sleep(delay)

        move_count = random.randint(3, 6)
        print(f"[GSG SIM] Phase: movement ({move_count} readings)")
        for _ in range(move_count):
            if stop_event.is_set():
                return
            magnitude = 1.0 + random.uniform(0.6, 2.0)
            callback(True, magnitude, publish_event, settings, verbose=verbose)  
            time.sleep(delay)