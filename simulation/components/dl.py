try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
except ImportError:
    GPIO = None

def led_on(settings, state=True):
    if settings.get("simulated", True) or GPIO is None:
        print("="*20)
        print(f"[DL] LED is {'ON' if state else 'OFF'} (simulated)")
        print("="*20)
    else:
        pin = settings.get("pin")
        if pin is not None:
            GPIO.output(pin, GPIO.HIGH if state else GPIO.LOW)
