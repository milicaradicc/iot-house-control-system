import time
import random

def run_door_membrane_switch_simulator(callback, stop_event, code):
    
    values = ["1","2","3","A","4","5","6","B","7","8","9","C","*","0","#","D"]
    while not stop_event.is_set():
        clicked_value = random.choice(values)
        callback(clicked_value, code)
        time.sleep(2)