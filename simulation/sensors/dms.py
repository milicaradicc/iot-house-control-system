import RPi.GPIO as GPIO
import time

class DoorMembraneSwitch(object):

    def __init__(self, r1_pin, r2_pin, r3_pin, r4_pin, c1_pin, c2_pin, c3_pin, c4_pin):
        self.r1_pin = r1_pin
        self.r2_pin = r2_pin
        self.r3_pin = r3_pin
        self.r4_pin = r4_pin

        self.c1_pin = c1_pin
        self.c2_pin = c2_pin
        self.c3_pin = c3_pin
        self.c4_pin = c4_pin
        
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(self.r1_pin, GPIO.OUT)
        GPIO.setup(self.r2_pin, GPIO.OUT)
        GPIO.setup(self.r3_pin, GPIO.OUT)
        GPIO.setup(self.r4_pin, GPIO.OUT)

        GPIO.setup(self.c1_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.c2_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.c3_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.c4_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)



    def read_line(self, line, characters):
        GPIO.output(line, GPIO.HIGH)
        if(GPIO.input(self.c1_pin) == 1):
            print(characters[0])
        if(GPIO.input(self.c2_pin) == 1):
            print(characters[1])
        if(GPIO.input(self.c3_pin) == 1):
            print(characters[2])
        if(GPIO.input(self.c4_pin) == 1):
            print(characters[3])
        GPIO.output(line, GPIO.LOW)


def run_dms_loop(dms, delay, callback, stop_event, code):
    while not stop_event.is_set():
        if key:
            callback(key, code)

        key = dms.read_line(dms.r2_pin, ["4","5","6","B"])
        if key:
            callback(key, code)

        key = dms.read_line(dms.r3_pin, ["7","8","9","C"])
        if key:
            callback(key, code)

        key = dms.read_line(dms.r4_pin, ["*","0","#","D"])
        if key:
            callback(key, code)

        time.sleep(delay)