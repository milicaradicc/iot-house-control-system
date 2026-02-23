import threading
import time
import json
import paho.mqtt.publish as publish
from settings.broker_settings import HOSTNAME, PORT

ir_batch = []
publish_data_counter = 0
publish_data_limit = 5
counter_lock = threading.Lock()

def publisher_task(event, ir_batch):
    global publish_data_counter, publish_data_limit
    while True:
        event.wait()
        with counter_lock:
            local_ir_batch = ir_batch.copy()
            publish_data_counter = 0
            ir_batch.clear()
        publish.multiple(local_ir_batch, hostname=HOSTNAME, port=PORT)
        print(f'published {publish_data_limit} ir values')
        event.clear()

publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, ir_batch,))
publisher_thread.daemon = True
publisher_thread.start()

def ir_callback(command, publish_event, ir_settings, code = "IR", verbose = False):
    global publish_data_counter, publish_data_limit

    if verbose:
        t = time.localtime()
        print("="*20)
        print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
        print(f"Code: {code}")
        print(f"Command: {command}%")

    command_payload = {
        "measurement": ir_settings['topic'],          
        "simulated": ir_settings['simulated'],
        "runs_on": ir_settings["runs_on"],
        "name": ir_settings["name"],
        "value": command  
    }

    with counter_lock:
        ir_batch.append((ir_settings['topic'], json.dumps(command_payload), 0, True))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()


def run_bedroom_ir(settings, threads, stop_event):

    code="IR"

    if settings['simulated']:
        print("Starting ir sumilator")
        from simulators.ir import run_bedroom_ir_simulator
        print("Starting ir simulator...")
        ir_thread = threading.Thread(target = run_bedroom_ir_simulator, args=(2, ir_callback, stop_event, publish_event, settings))
        ir_thread.start()
        threads.append(ir_thread)
        print("IR sumilator started")
    else:
        from sensors.ir import run_ir_loop, IR
        print("Starting ir loop")
        ir = IR(settings['pin'])
        ir_thread = threading.Thread(target=run_ir_loop, args=(ir, 2, ir_callback, stop_event, publish_event, settings))
        ir_thread.start()
        threads.append(ir_thread)
        print("IR loop started")
