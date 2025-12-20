import threading
import time

def dus_callback(distance, code):
    t = time.localtime()
    print("="*20)
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
    print(f"Code: {code}")
    print(f"Distance: {distance}")

def run_ultrasonic_door_sensor(settings, threads, stop_event):
    code = "DUS1"
    if settings['simulated']:
        from ..simulators.dus import run_ultrasonic_door_sensor_simulator
        print("Starting dus1 simulator...")
        dus1_thread = threading.Thread(target= run_ultrasonic_door_sensor_simulator, args=(dus_callback, stop_event, code))
        dus1_thread.start()
        threads.append(dus1_thread)
        print("DUS1 simulator started!")
    else:
        from ..sensors.dus import run_dus_loop, DoorUltrasonicSensor
        print("Starting dus1 loop...")
        dus = DoorUltrasonicSensor(settings['trigger_pin'], settings['echo_pin'])
        dus1_thread = threading.Thread(target= run_dus_loop, args=(dus, 2, dus_callback, stop_event, code))
        dus1_thread.start()
        threads.append(dus1_thread)
        print("DUS1 loop started!")