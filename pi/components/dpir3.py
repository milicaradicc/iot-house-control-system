# import threading
# import time
# import json
# import paho.mqtt.publish as publish
# from settings.broker_settings import HOSTNAME, PORT
# from simulators.dpir3 import run_motion_sensor_simulator

# dpir3_batch = []
# publish_data_counter = 0
# publish_data_limit = 5
# counter_lock = threading.Lock()

# def publisher_task(event, dpir3_batch):
#     global publish_data_counter, publish_data_limit
#     while True:
#         event.wait()
#         with counter_lock:
#             local_dpir3_batch = dpir3_batch.copy()
#             publish_data_counter = 0
#             dpir3_batch.clear()
#         publish.multiple(local_dpir3_batch, hostname=HOSTNAME, port=PORT)
#         print(f'published {publish_data_limit} dpir3 values')
#         event.clear()

# publish_event = threading.Event()
# publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, dpir3_batch,))
# publisher_thread.daemon = True
# publisher_thread.start()


# def dpir3_callback(motion_detected, publish_event, dpir_settings, code="DPIR3", verbose = False):
#     global publish_data_counter, publish_data_limit

#     if verbose:
#         t = time.localtime()
#         print("="*20)
#         print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
#         print(f"Code: {code}")
#         print(f"Motion detected: {'YES' if motion_detected else 'NO'}")
#         print("="*20)

#     motion_payload = {
#         "measurement": dpir_settings['topic'],
#         "simulated" : dpir_settings['simulated'],
#         "runs_on": dpir_settings["runs_on"],
#         "name": dpir_settings["name"],
#         "value": 1 if motion_detected else 0 
#     }

#     with counter_lock:
#         dpir3_batch.append((dpir_settings['topic'], json.dumps(motion_payload), 0, True ))
#         publish_data_counter += 1

#     if publish_data_counter >= publish_data_limit:
#         publish_event.set()


# def run_living_room_dpir(settings, threads, stop_event):
#     code = "DPIR3"

#     if settings.get('simulated', True):
#         print("Starting DPIR3 simulator")

#         t = threading.Thread(
#             target=run_motion_sensor_simulator,
#             args=(dpir3_callback, stop_event, publish_event, settings)    
#         )

#         t.start()
#         threads.append(t)

#         print("DPIR3 simulator started")

#     else:

#         # todo!!!!!!!
#         # refactor first!!!


#         # from sensors.dpir1 import DPIR1Sensor, run_dpir1_loop

#         # sensor = DPIR1Sensor(settings['pin'])

#         # # FIXED: Added publish_event and settings parameters
#         # t = threading.Thread(
#         #     target=run_dpir1_loop,
#         #     args=(sensor, settings.get('delay', 0.5), dpir1_callback, stop_event, code, publish_event, settings)
#         # )

#         # t.start()
#         # threads.append(t)

#         print("DPIR1 hardware loop started")