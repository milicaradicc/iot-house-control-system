
import time
import random
from threading import Event


import random

def generate_values(initial_command="0x300ff22dd"):
    commands = ["0x300ff22dd", "0x300ffc23d", "0x300ff629d", "0x300ffa857", "0x300ffb04f", "0x300ff02fd", "0x300ffc23f", "0x300ff9867"]
    power_on = False
    initial = initial_command if initial_command in commands else "0x300ff22dd"

    while True:
        if not power_on:
            yield "0x300ff22dd"
            power_on = True
        else:
            cmd = random.choice(commands[1:])
            yield cmd

        if random.random() < 0.05:
            yield "0x300ff22dd"
            power_on = not power_on


def run_bedroom_ir_simulator(delay, callback, stop_event, publish_event, settings):
    for command in generate_values():
        print(command)
        time.sleep(delay)
        callback(command, publish_event, settings)
        if stop_event.is_set():
            break

