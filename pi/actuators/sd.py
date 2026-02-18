import RPi.GPIO as GPIO
import time

class FourDigitSevenSegment(object):
    def __init__(self, segment_pins, digit_pins):
        self.segment_pins = segment_pins # [A, B, C, D, E, F, G, DP]
        self.digit_pins = digit_pins     # [D1, D2, D3, D4]
        
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        for pin in self.segment_pins + self.digit_pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)

        # Mapiranje karaktera na segmente (zajednička katoda primer)
        self.num_map = {
            '0': [1,1,1,1,1,1,0], '1': [0,1,1,0,0,0,0], '2': [1,1,0,1,1,0,1],
            '3': [1,1,1,1,0,0,1], '4': [0,1,1,0,0,1,1], '5': [1,0,1,1,0,1,1],
            '6': [1,0,1,1,1,1,1], '7': [1,1,1,0,0,0,0], '8': [1,1,1,1,1,1,1],
            '9': [1,1,1,1,0,1,1], ':': [0,0,0,0,0,0,0], ' ': [0,0,0,0,0,0,0]
        }

    def display_digit(self, digit_idx, char):
        # Isključi sve cifre
        for d in self.digit_pins: GPIO.output(d, GPIO.HIGH)
        
        # Postavi segmente
        segments = self.num_map.get(char, [0]*7)
        for i in range(7):
            GPIO.output(self.segment_pins[i], segments[i])
            
        # Uključi odgovarajuću cifru (Low za zajedničku katodu)
        GPIO.output(self.digit_pins[digit_idx], GPIO.LOW)
        time.sleep(0.002) # Multiplexing delay

def run_sd_loop(sd, get_display_value, stop_event):
    while not stop_event.is_set():
        val = get_display_value() # npr. "12:45"
        clean_val = val.replace(":", "")[:4].zfill(4)
        for i in range(4):
            sd.display_digit(i, clean_val[i])