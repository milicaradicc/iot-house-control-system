
import time
import random
from threading import Event


import random

def generate_values(initial_command="POWER"):

    commands = ["POWER", "R", "G", "B", "UP", "DOWN"]
    power_on = False
    initial = initial_command if initial_command in commands else "POWER"

    while True:
        if not power_on:
            # prvo uključi POWER
            yield "POWER"
            power_on = True
        else:
            # random komanda osim POWER
            cmd = random.choice(commands[1:])  # ["R","G","B","UP","DOWN"]
            yield cmd

        # simuliši mogućnost da neko pritisne POWER u random trenutku
        if random.random() < 0.05:  # 5% šansa da POWER toggle
            yield "POWER"
            power_on = not power_on



def run_bedroom_ir_simulator(delay, callback, stop_event, publish_event, settings):
    for command in generate_values():
        print(command)
        time.sleep(delay)
        callback(command, publish_event, settings)
        if stop_event.is_set():
            break

