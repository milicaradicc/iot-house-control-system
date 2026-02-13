import RPi.GPIO as GPIO
import time
from datetime import datetime
from threading import Event

class IR:

    def __init__(self, pin):
        self.pin = pin

        self.buttons = [
            0x300ff22dd,  # POWER
            0x300ffc23d,  # R
            0x300ff629d,  # G
            0x300ffa857,  # B
            0x300ff9867,  # UP
            0x300ffb04f   # DOWN
        ]

        self.button_names = ["POWER", "R", "G", "B", "UP", "DOWN"]

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN)

    def get_binary(self):
        num1s = 0
        binary = 1
        command = []

        previous_value = 0
        value = GPIO.input(self.pin)

        # čekaj da linija padne na LOW (start signal)
        while value:
            time.sleep(0.0001)
            value = GPIO.input(self.pin)

        start_time = datetime.now()

        while True:
            if previous_value != value:
                now = datetime.now()
                pulse_time = now - start_time
                start_time = now
                command.append((previous_value, pulse_time.microseconds))

            if value:
                num1s += 1
            else:
                num1s = 0

            if num1s > 10000:
                break

            previous_value = value
            value = GPIO.input(self.pin)

        # konverzija pulse width u binarni broj
        for typ, tme in command:
            if typ == 1:
                if tme > 1000:
                    binary = binary * 10 + 1
                else:
                    binary *= 10

        if len(str(binary)) > 34:
            binary = int(str(binary)[:34])

        return binary

    def convert_hex(self, binary_value):
        return hex(int(str(binary_value), 2))

    def read_button(self):
        binary = self.get_binary()
        hex_value = self.convert_hex(binary)

        for i, btn in enumerate(self.buttons):
            if hex(btn) == hex_value:
                return self.button_names[i]

        return None

def run_ir_loop(ir, delay, callback, stop_event: Event, code):
    try:
        last_command = None
        
        
        while not stop_event.is_set():
            command = ir.read_button()
            
            if command != last_command :
                callback(command)
                last_command = command

            time.sleep(delay)

    finally:
        GPIO.cleanup(ir.pin)