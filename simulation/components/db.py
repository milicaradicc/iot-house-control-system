import time
try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
except ImportError:
    GPIO = None

def buzzer_control(settings, state=True):
    global buzzer_state
    buzzer_state = state
    if settings.get("simulated", True) or GPIO is None:
        print("="*20)
        print(f"[DB] BUZZER is {'ON' if state else 'OFF'} (simulated)")
        print("="*20)
    else:
        pin = settings.get("pin")
        if pin is not None:
            GPIO.output(pin, GPIO.HIGH if state else GPIO.LOW)
