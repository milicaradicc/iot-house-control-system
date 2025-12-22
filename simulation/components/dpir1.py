import threading
import time
import random
from ..simulators.dpir1 import run_motion_sensor_simulator

def dpir1_callback(motion_detected, code="DPIR1"):
    t = time.localtime()
    print("="*20)
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
    print(f"Code: {code}")
    print(f"Motion detected: {'YES' if motion_detected else 'NO'}")
    print("="*20)

def run_motion_sensor(settings, threads, stop_event):
    code = "DPIR1"

    if settings.get('simulated', True):
        print("Starting DPIR1 simulator")

        t = threading.Thread(
            target=run_motion_sensor_simulator,
            args=(dpir1_callback, stop_event, code)
        )

        t.start()
        threads.append(t)

        print("DPIR1 simulator started")

    else:
        from sensors.dpir1 import DPIR1Sensor, run_dpir1_loop

        sensor = DPIR1Sensor(settings['pin'])

        t = threading.Thread(
            target=run_dpir1_loop,
            args=(sensor, settings.get('delay', 2), dpir1_callback, stop_event)
        )

        t.start()
        threads.append(t)

        print("DPIR1 hardware loop started")
