import RPi.GPIO as GPIO


class RGBLed:
    def __init__(self, r_pin, g_pin, b_pin, callback):
        self.r_pin = r_pin
        self.g_pin = g_pin
        self.b_pin = b_pin
        self.callback = callback

        GPIO.setup(self.r_pin, GPIO.OUT)
        GPIO.setup(self.g_pin, GPIO.OUT)
        GPIO.setup(self.b_pin, GPIO.OUT)

    def turnOff(self):
        GPIO.output(self.r_pin, GPIO.LOW)
        GPIO.output(self.g_pin, GPIO.LOW)
        GPIO.output(self.b_pin, GPIO.LOW)
        self.callback("off")

    def white(self):
        GPIO.output(self.r_pin, GPIO.HIGH)
        GPIO.output(self.g_pin, GPIO.HIGH)
        GPIO.output(self.b_pin, GPIO.HIGH)
        self.callback("white")

    def red(self):
        GPIO.output(self.r_pin, GPIO.HIGH)
        GPIO.output(self.g_pin, GPIO.LOW)
        GPIO.output(self.b_pin, GPIO.LOW)
        self.callback("red")

    def green(self):
        GPIO.output(self.r_pin, GPIO.LOW)
        GPIO.output(self.g_pin, GPIO.HIGH)
        GPIO.output(self.b_pin, GPIO.LOW)
        self.callback("green")

    def blue(self):
        GPIO.output(self.r_pin, GPIO.LOW)
        GPIO.output(self.g_pin, GPIO.LOW)
        GPIO.output(self.b_pin, GPIO.HIGH)
        self.callback("blue")

    def yellow(self):
        GPIO.output(self.r_pin, GPIO.HIGH)
        GPIO.output(self.g_pin, GPIO.HIGH)
        GPIO.output(self.b_pin, GPIO.LOW)
        self.callback("yellow")

    def purple(self):
        GPIO.output(self.r_pin, GPIO.HIGH)
        GPIO.output(self.g_pin, GPIO.LOW)
        GPIO.output(self.b_pin, GPIO.HIGH)
        self.callback("purple")

    def lightBlue(self):
        GPIO.output(self.r_pin, GPIO.LOW)
        GPIO.output(self.g_pin, GPIO.HIGH)
        GPIO.output(self.b_pin, GPIO.HIGH)
        self.callback("light blue")

    def cleanup(self):
        GPIO.cleanup([self.r_pin, self.g_pin, self.b_pin])