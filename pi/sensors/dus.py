import RPi.GPIO as GPIO
import time

class DoorUltrasonicSensor(object):
    
    def __init__(self, trigger_pin, echo_pin):
        self.trigger_pin = trigger_pin
        self.echo_pin = echo_pin
        GPIO.setup(self.trigger_pin, GPIO.OUT)
        GPIO.setup(self.echo_pin, GPIO.IN)

    def get_distance(self):
        GPIO.output(self.trigger_pin, False)
        time.sleep(0.2)
        GPIO.output(self.trigger_pin, True)
        time.sleep(0.00001)
        GPIO.output(self.trigger_pin, False)

        pulse_start_time = time.time()
        pulse_end_time = time.time()

        max_iter = 100

        iter = 0
        while GPIO.input(self.echo_pin) == 0:
            if iter > max_iter:
                return None
            pulse_start_time = time.time()
            iter += 1

        iter = 0
        while GPIO.input(self.echo_pin) == 1:
            if iter > max_iter:
                return None
            pulse_end_time = time.time()
            iter += 1

        pulse_duration = pulse_end_time - pulse_start_time
        distance = (pulse_duration * 34300) / 2
        return distance


def run_dus_loop(dus, delay, callback, stop_event, code, publish_event, settings):
    while not stop_event.is_set():
        distance = dus.get_distance()
        if distance is not None:
            callback(distance, publish_event, settings, code, verbose=True)
        else:
            print(f"[{code}] ⚠️ Sensor vratio None — preskačem")
        time.sleep(delay)