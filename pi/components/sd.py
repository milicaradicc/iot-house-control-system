import threading
import time
import paho.mqtt.client as mqtt
from settings.broker_settings import HOSTNAME, PORT
import json

sd_batch = []
publish_data_counter = 0
publish_data_limit = 2
counter_lock = threading.Lock()

def publisher_task(event, sd_batch):
    global publish_data_counter, publish_data_limit
    while True:
        event.wait()
        with counter_lock:
            local_sd_batch = sd_batch.copy()
            publish_data_counter = 0
            sd_batch.clear()
        
        if local_sd_batch:
            import paho.mqtt.publish as publish
            publish.multiple(local_sd_batch, hostname=HOSTNAME, port=PORT)
            print(f'published {len(local_sd_batch)} SD values')
        
        event.clear()

publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, sd_batch))
publisher_thread.daemon = True
publisher_thread.start()

def sd_callback(value, publish_event, sd_settings, verbose = False):
    global publish_data_counter
    
    payload = {
        "measurement": sd_settings['topic'],
        "simulated": sd_settings['simulated'],
        "runs_on": sd_settings["runs_on"],
        "name": sd_settings["name"],
        "value": value
    }

    if verbose:
        t = time.localtime()
        print("="*20)
        print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
        print(f"Time: {value}")
    
    with counter_lock:
        sd_batch.append((sd_settings['topic'], json.dumps(payload), 0, True))
        publish_data_counter += 1
    
    if publish_data_counter >= publish_data_limit:
        publish_event.set()

def run_segment_display(settings, state=True, verbose=False):
    try:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        is_gpio_available = True
    except ImportError:
        GPIO = None
        is_gpio_available = False

    if settings.get("simulated", True) or not is_gpio_available:
        from simulators.sd import SegmentDisplaySimulator

        def callback_wrapper(value):
            sd_callback(value, publish_event, settings, verbose)

        simulator = SegmentDisplaySimulator(callback_wrapper)

        simulator_thread = threading.Thread(target=simulator.run)
        simulator_thread.daemon = True
        simulator_thread.start()

        return simulator

    else:
        from actuators.sd import SegmentDisplay

        segment_pins = settings.get("segment_pins")  # [A, B, C, D, E, F, G]
        digit_pins = settings.get("digit_pins")      # [D1, D2, D3, D4]

        if not segment_pins or not digit_pins:
            raise ValueError("[SD] Missing segment_pins or digit_pins in settings")

        sd = SegmentDisplay(segment_pins, digit_pins)
        sd.start()

        print(f"[SD] Hardware segment display started on pins: {segment_pins}, {digit_pins}")
        return sd