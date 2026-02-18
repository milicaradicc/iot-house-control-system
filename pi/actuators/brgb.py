import RPi.GPIO as GPIO
from time import sleep


class RGBLed:
    def __init__(self,r_pin, g_pin, b_pin, callback):
        self.r_pin = r_pin
        self.g_pin = g_pin
        self.b_pin = b_pin

        self.callback = callback

        #set pins as outputs
        GPIO.setup(self.r_pin, GPIO.OUT)
        GPIO.setup(self.g_pin, GPIO.OUT)
        GPIO.setup(self.b_pin, GPIO.OUT)

    def turnOff(self):
        GPIO.output(self.r_pin, GPIO.LOW)
        GPIO.output(self.g_pin, GPIO.LOW)
        GPIO.output(self.b_pin, GPIO.LOW)
        
    def white(self):
        GPIO.output(self.r_pin, GPIO.HIGH)
        GPIO.output(self.g_pin, GPIO.HIGH)
        GPIO.output(self.b_pin, GPIO.HIGH)
        
    def red(self):
        GPIO.output(self.r_pin, GPIO.HIGH)
        GPIO.output(self.g_pin, GPIO.LOW)
        GPIO.output(self.b_pin, GPIO.LOW)

    def green(self):
        GPIO.output(self.r_pin, GPIO.LOW)
        GPIO.output(self.g_pin, GPIO.HIGH)
        GPIO.output(self.b_pin, GPIO.LOW)
        
    def blue(self):
        GPIO.output(self.r_pin, GPIO.LOW)
        GPIO.output(self.g_pin, GPIO.LOW)
        GPIO.output(self.b_pin, GPIO.HIGH)
        
    def yellow(self):
        GPIO.output(self.r_pin, GPIO.HIGH)
        GPIO.output(self.g_pin, GPIO.HIGH)
        GPIO.output(self.b_pin, GPIO.LOW)
        
    def purple(self):
        GPIO.output(self.r_pin, GPIO.HIGH)
        GPIO.output(self.g_pin, GPIO.LOW)
        GPIO.output(self.b_pin, GPIO.HIGH)
        
    def lightBlue(self):
        GPIO.output(self.r_pin, GPIO.LOW)
        GPIO.output(self.g_pin, GPIO.HIGH)
        GPIO.output(self.b_pin, GPIO.HIGH)

