import RPi.GPIO as GPIO
import time


class DoorMembraneSwitch(object):

    def __init__(self, r1_pin, r2_pin, r3_pin, r4_pin,
                 c1_pin, c2_pin, c3_pin, c4_pin):

        self.rows = [r1_pin, r2_pin, r3_pin, r4_pin]
        self.cols = [c1_pin, c2_pin, c3_pin, c4_pin]

        self.keys = [
            ["1", "2", "3", "A"],
            ["4", "5", "6", "B"],
            ["7", "8", "9", "C"],
            ["*", "0", "#", "D"]
        ]

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        # Rows as output
        for row in self.rows:
            GPIO.setup(row, GPIO.OUT)
            GPIO.output(row, GPIO.LOW)

        # Columns as input
        for col in self.cols:
            GPIO.setup(col, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)


    def read_key(self):
        for i, row in enumerate(self.rows):
            GPIO.output(row, GPIO.HIGH)

            for j, col in enumerate(self.cols):
                if GPIO.input(col) == 1:
                    GPIO.output(row, GPIO.LOW)
                    return self.keys[i][j]

            GPIO.output(row, GPIO.LOW)

        return None


def run_dms_loop(dms, delay, callback, stop_event, code, publish_event, dms_settings):
    last_key = None

    print("DMS loop started!")

    while not stop_event.is_set():

        key = dms.read_key()

        # Ako je pritisnut novi taster
        if key and key != last_key:
            callback(key, publish_event, dms_settings, code)
            last_key = key

        # Ako je pušten taster
        if not key:
            last_key = None

        time.sleep(delay)

    GPIO.cleanup()