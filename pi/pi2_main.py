import threading
import time
import signal
import sys
from settings.settings import load_settings
from components.ds import run_door_sensor
from components.dus import run_ultrasonic_door_sensor
from components.dpir1 import run_motion_sensor
from components.dht import run_dht
from components.gsg import run_gyroscope
from components.btn import run_button, simulate_button_press
from components.sd import run_segment_display

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
except ImportError:
    GPIO = None

# Globalne reference
sd_simulator = None
btn_settings = None

def shutdown(signal_received=None, frame=None):
    print("\nShutting down application...")
    stop_event.set()
    
    if sd_simulator:
        sd_simulator.stop()
    
    for thread in threads:
        thread.join(timeout=2)
    
    if GPIO:
        try:
            GPIO.cleanup()
        except:
            pass
    
    print("App stopped cleanly.")
    sys.exit(0)

if __name__ == "__main__":
    print("Starting Smart Home App (PI2)...")
    settings = load_settings()
    threads = []
    stop_event = threading.Event()
    
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    
    # --- COMPONENT INITIALIZATION ---
    
    # DS2 – Door Sensor
    ds2_settings = settings.get('PI2', {})['components']['DS2']
    run_door_sensor(ds2_settings, threads, stop_event)
    
    # DUS2 – Ultrasonic Sensor
    dus2_settings = settings.get('PI2', {})['components']['DUS2']
    run_ultrasonic_door_sensor(dus2_settings, threads, stop_event, "DUS2")
    
    # DPIR2 – Motion Sensor
    dpir2_settings = settings.get('PI2', {})['components']['DPIR2']
    run_motion_sensor(dpir2_settings, threads, stop_event)
    
    # 4SD – Segment Display & Timer Logic
    sd_settings = settings.get('PI2', {})['components']['4SD']
    sd_simulator = run_segment_display(sd_settings, True, True)
    
    # BTN - Kitchen Button (mora biti posle SD!)
    btn_settings = settings.get('PI2', {})['components']['BTN']
    run_button(btn_settings, threads, stop_event, sd_simulator)
    
    # DHT3 - Temperature/Humidity Sensor
    dht_settings = settings.get('PI2', {})['components']['DHT3']
    run_dht(dht_settings, threads, stop_event, "DHT3")
    
    # GSG - Gyroscope
    # gsg_settings = settings.get('PI2', {})['components']['GSG']
    # run_gyroscope(gsg_settings, threads, stop_event)
    
    # --- MAIN LOOP – Simulation Input ---
    print("\n" + "="*50)
    print("KITCHEN TIMER - Available Commands:")
    print("="*50)
    print("  't [sec]' - Set timer time (e.g., 't 120' for 2 minutes)")
    print("  'n [sec]' - Set button increment (e.g., 'n 30')")
    print("  'b'       - Press kitchen button (BTN)")
    print("  'exit'    - Shutdown application")
    print("="*50 + "\n")
    
    try:
        while True:
            user_input = input("> ").strip().lower()
            
            if user_input == "exit":
                shutdown()
            
            elif user_input.startswith("t "):
                try:
                    seconds = int(user_input.split()[1])
                    if sd_simulator:
                        sd_simulator.set_timer(seconds)
                        print(f"✓ Timer set to {seconds} seconds")
                    else:
                        print("✗ Simulator not available")
                except (ValueError, IndexError):
                    print("✗ Invalid format. Use: t [seconds]")
            
            elif user_input.startswith("n "):
                try:
                    increment = int(user_input.split()[1])
                    if sd_simulator:
                        sd_simulator.set_n_increment(increment)
                        print(f"✓ Button increment set to {increment} seconds")
                    else:
                        print("✗ Simulator not available")
                except (ValueError, IndexError):
                    print("✗ Invalid format. Use: n [seconds]")
            
            elif user_input == "b":
                # Pozivamo funkciju za simulaciju pritiska dugmeta
                simulate_button_press(btn_settings)
                print("✓ Button pressed")
            
            else:
                print("✗ Unknown command. Use: t, n, b, or exit")
                
    except KeyboardInterrupt:
        shutdown()