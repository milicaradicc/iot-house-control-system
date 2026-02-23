try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None

class DoorLight:
    def __init__(self, pin, callback):
        self.pin = pin
        self.is_on = True
        self.callback = callback
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)

    def on(self):
        self.is_on = True
        GPIO.output(self.pin, GPIO.HIGH)
        self.callback(True)
        print(f"[DL] LED pin {self.pin}: ON")

    def off(self):
        self.is_on = False
        GPIO.output(self.pin, GPIO.LOW)
        self.callback(False)
        print(f"[DL] LED pin {self.pin}: OFF")

    def toggle(self):
        if self.is_on:
            self.off()
        else:
            self.on()