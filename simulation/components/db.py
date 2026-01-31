from ..simulators.db import DBSimulator
try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
except ImportError:
    GPIO = None

def run_door_buzzer(settings, state=True):
    global buzzer_state
    buzzer_state = state
    if settings.get("simulated", True) or GPIO is None:
        simulator = DBSimulator()
        return simulator
    else:
        pin = settings.get("pin")
        if pin is not None:
            GPIO.output(pin, GPIO.HIGH if state else GPIO.LOW)
