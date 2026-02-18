import math
import time
import random

def generate_temperature():
      amplitude = 5
      frequency = 0.1
      offset = 20
      timestamp = int(time.time())

      temperature = amplitude * math.sin(frequency * timestamp) + offset
      return temperature

def run_gyroscope_simulator(callback, stop_event, publish_event, settings, delay=2):
    while not stop_event.is_set():
        temperature = generate_temperature()
        callback(temperature, publish_event, settings)
        time.sleep(delay)
