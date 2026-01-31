from ..simulators.dl import DLSimulator

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
except ImportError:
    GPIO = None

def run_door_led(settings, state=True):
    if settings.get("simulated", True) or GPIO is None:
        simulator = DLSimulator()
        return simulator
    else:
        pin = settings.get("pin")
        if pin is not None:
            GPIO.output(pin, GPIO.HIGH if state else GPIO.LOW)
