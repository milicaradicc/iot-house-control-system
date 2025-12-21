import threading
import time
import random

def dpir1_callback(motion_detected, code="DPIR1"):
    t = time.localtime()
    print("="*20)
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
    print(f"Code: {code}")
    print(f"Motion detected: {'YES' if motion_detected else 'NO'}")

def generate_motion_values():
    while True:
        yield random.choice([True, False])

def run_motion_sensor(settings, threads, stop_event):
    if settings.get('simulated', True):
        print("Starting DPIR1 simulator")

        def sensor_loop():
            for state in generate_motion_values():
                if stop_event.is_set():
                    break
                dpir1_callback(state, code="DPIR1")
                time.sleep(settings.get('delay', 2)) 

        t = threading.Thread(target=sensor_loop)
        t.start()
        threads.append(t)

        print("DPIR1 simulator started")

    else:
        from sensors.dpir1 import DPIR1Sensor, run_dpir1_loop
        sensor = DPIR1Sensor(settings['pin'])
        t = threading.Thread(target=run_dpir1_loop, args=(sensor, settings.get('delay', 2), dpir1_callback, stop_event))
        t.start()
        threads.append(t)
        print("DPIR1 hardware loop started")
