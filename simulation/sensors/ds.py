import RPi.GPIO as GPIO
import time

class DoorSensor(object):
    
    def __init__(self, pin):
        self.pin = pin

        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)  #pull up otpornik - GPIO pin je preko otpornika vezan na 3.3V - napon - logicka jedinica je default stanje - podignut
        #GPIO.add_event_detect(pin, GPIO.FALLING, callback=self._handle_event, bouncetime=100)
        
    def readSensor(self):
        return not GPIO.input(self.pin)     
    
    # def _handle_event(self, channel):
    #     state = not GPIO.input(self.pin)        #pusteno=high=1 -> 0=False     pritisnuto=low=0 -> 1=True
    #     self.callback(state, self.code)

def run_ds_loop(ds, delay, callback, stop_event, code):
    while not stop_event.is_set():
        state = ds.readSensor()
        callback(state, code)
        time.sleep(delay)
