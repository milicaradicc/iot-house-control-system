import RPi.GPIO as GPIO
import time
from threading import Event

class DoorSensor(object):
    def __init__(self, pin):
        self.pin = pin
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def readSensor(self):
        return not GPIO.input(self.pin)


def run_ds_loop(ds, delay, callback, stop_event, code, publish_event, settings):
    try:
        last_state = None
        while not stop_event.is_set():
            state = ds.readSensor()
            if state != last_state:
                callback(state, publish_event, settings, code, verbose=True)
                last_state = state
            time.sleep(delay)
    finally:
        GPIO.cleanup(ds.pin)