import threading
try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None
try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None

class DoorBuzzer:
    def __init__(self, pin, callback):
        self.pin = pin
        self.callback = callback
        self.is_on = False
        
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.LOW)  # inicijalno ugašen

    def on(self):
        if not self.is_on:
            self.is_on = True
            GPIO.output(self.pin, GPIO.HIGH)
            self.callback(True)
            print("[DB] 🔊 BUZZER: ON")

    def off(self):
        if self.is_on:
            self.is_on = False
            GPIO.output(self.pin, GPIO.LOW)
            self.callback(False)
            print("[DB] 🔇 BUZZER: OFF")

    def cleanup(self):
        GPIO.cleanup(self.pin)
        print("[DB] GPIO cleaned up")