import threading
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
        self._start_listener()
    
    def on(self):
        if not self.is_on:
            self.is_on = True
            GPIO.output(self.pin, GPIO.HIGH)
            self.callback(True)
            print("[DB] BUZZER is: ON")
    
    def off(self):
        if self.is_on:
            self.is_on = False
            GPIO.output(self.pin, GPIO.LOW)
            self.callback(False)
            print("[DB] BUZZER is: OFF")
    
    def _start_listener(self):
        GPIO.add_event_detect(
            self.pin,
            GPIO.BOTH,
            callback=self._gpio_callback,
            bouncetime=200
        )
    
    def _gpio_callback(self, channel):
        state = GPIO.input(self.pin)
        if state == GPIO.HIGH:
            self.on()
        else:
            self.off()
    
    def cleanup(self):
        GPIO.remove_event_detect(self.pin)
        GPIO.cleanup(self.pin)
        print("[DB] GPIO cleaned up")