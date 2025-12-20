import threading
import time

def dms_callback(key, code):
    t = time.localtime()
    print("="*20)
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
    print(f"Code: {code}")
    print(f"Key: {key}")

def run_door_membrane_switch(settings, threads, stop_event):
    code = "DMS"
    if settings['simulated']:
        from ..simulators.dms import run_door_membrane_switch_simulator
        print("Starting dms simulator...")
        dms_thread = threading.Thread(target= run_door_membrane_switch_simulator, args=(dms_callback, stop_event, code))
        dms_thread.start()
        threads.append(dms_thread)
        print("DMS simulator started!")
    else:
        from ..sensors.dms import run_dms_loop, DoorMembraneSwitch
        print("Starting dms loop...")
        dms = DoorMembraneSwitch(
            settings['r1'], 
            settings['r2'],
            settings['r3'],
            settings['r4'],
            settings['c1'],
            settings['c2'],
            settings['c3'],
            settings['c4']
            )
        dms_thread = threading.Thread(target= run_dms_loop, args=(dms, 2, dms_callback, stop_event, code))
        dms_thread.start()
        threads.append(dms_thread)
        print("DMS loop started!")