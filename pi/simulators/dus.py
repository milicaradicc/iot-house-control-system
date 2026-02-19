import time
import random


def generate_ultrasonic_distance(phase):
    if phase == 'idle':
        return random.uniform(200, 500)
    elif phase == 'approach':
        return random.uniform(60, 200)
    elif phase == 'close':
        return random.uniform(10, 40)
    elif phase == 'leaving':
        return random.uniform(60, 200)


def run_ultrasonic_door_sensor_simulator(delay, callback, stop_event, publish_event, settings):
    while not stop_event.is_set():
        phases = [
            ('idle',     random.randint(8, 15)),   # isto kao DPIR idle
            ('approach', random.randint(2, 3)),
            ('close',    random.randint(4, 6)),     # duže da poklopi DPIR
            ('leaving',  random.randint(2, 3)),
        ]

        for phase, count in phases:
            print(f"[DUS SIM] Phase: {phase} ({count} readings)")
            for _ in range(count):
                if stop_event.is_set():
                    return
                distance = generate_ultrasonic_distance(phase)
                callback(distance, publish_event, settings)
                time.sleep(delay)