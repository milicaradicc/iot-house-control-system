import time
import random

def run_motion_sensor_simulator(callback, stop_event, publish_event, settings, delay=1):
    """
    Simulira detekciju pokreta u ciklusima.
    Pokret se detektuje samo u određenim intervalima, ne konstantno.
    """
    while not stop_event.is_set():
        # Faza mirovanja - nema pokreta
        idle_count = random.randint(8, 15)
        for _ in range(idle_count):
            if stop_event.is_set():
                return
            callback(False, publish_event, settings)
            time.sleep(delay)

        # Faza pokreta - osoba prolazi (3-5 sekundi)
        motion_count = random.randint(3, 5)
        print(f"[DPIR SIM] Motion detected for {motion_count} readings")
        for _ in range(motion_count):
            if stop_event.is_set():
                return
            callback(True, publish_event, settings)
            time.sleep(delay)