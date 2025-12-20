import threading
import time


def ds_callback(state, code):
    t = time.localtime()
    print("="*20)
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
    print(f"Code: {code}")
    print(f"State: {'CLOSED' if state else 'OPEN'}")

def run_door_sensor(settings, threads, stop_event):

    code = "DS1"

    if settings['simulated']:
        from ..simulators.door_sensor import run_door_sensor_simulator
        print("Starting ds1 simulator...")
        ds1_thread = threading.Thread(target= run_door_sensor_simulator, args=(ds_callback, stop_event, code))
        ds1_thread.start()
        threads.append(ds1_thread)
        print("DS1 simulator started!")
    else:
        from ..sensors.door_sensor import run_ds_loop, DoorSensor
        print("Starting ds1 loop...")
        ds = DoorSensor(settings['pin'])
        ds1_thread = threading.Thread(target= run_ds_loop, args=(ds, 0.1, ds_callback, stop_event, code))
        ds1_thread.start()
        threads.append(ds1_thread)
        print("DS1 loop started!")