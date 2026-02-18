
import time
import random
from threading import Event


import random

def generate_values(initial_command="POWER"):
    commands = ["POWER", "red", "green", "blue", "yellow", "purple", "light blue", "white"]
    power_on = False
    initial = initial_command if initial_command in commands else "POWER"

    while True:
        if not power_on:
            yield "POWER"
            power_on = True
        else:
            cmd = random.choice(commands[1:])
            yield cmd

        if random.random() < 0.05:
            yield "POWER"
            power_on = not power_on


def run_bedroom_ir_simulator(delay, callback, stop_event, publish_event, settings):
    for command in generate_values():
        print(command)
        time.sleep(delay)
        callback(command, publish_event, settings)
        if stop_event.is_set():
            break

