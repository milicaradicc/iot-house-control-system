import RPi.GPIO as GPIO
import time

class DPIR1Sensor(object):
    def __init__(self, pin):
        self.pin = pin
        GPIO.setup(self.pin, GPIO.IN)

    def detect_motion(self):
        return GPIO.input(self.pin) == 1  


def run_dpir1_loop(sensor, delay, callback, stop_event, code, publish_event, dpir_settings):
    while not stop_event.is_set():
        motion_detected = sensor.detect_motion()
        callback(motion_detected, publish_event, dpir_settings, code)
        time.sleep(delay)