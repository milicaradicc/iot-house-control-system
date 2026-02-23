# simulators/sd.py

import threading
import time
import paho.mqtt.client as mqtt
from settings.broker_settings import HOSTNAME, PORT
import json

class SegmentDisplaySimulator:
    def __init__(self, callback):
        self.remaining_time = 0
        self.n_increment = 10
        self.is_blinking = False
        self.lock = threading.Lock()
        self.callback = callback
        self.running = True
        
        # MQTT klijent za prijem komandi
        self.mqtt_client = mqtt.Client(
            client_id=f"sd_simulator_{id(self)}",
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2
        )
        self.mqtt_client.on_connect = self._on_connect
        self.mqtt_client.on_message = self._on_message
        
        # Povezivanje na MQTT broker
        try:
            self.mqtt_client.connect(HOSTNAME, PORT, 60)
            self.mqtt_client.loop_start()
            print("[Timer] MQTT client connected")
        except Exception as e:
            print(f"[Timer] Failed to connect to MQTT: {e}")
    
    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            client.subscribe("timer/set")
            client.subscribe("timer/increment")
            print("[Timer] Subscribed to timer control topics")
    
    def _on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode("utf-8"))
            
            if msg.topic == "timer/set":
                seconds = data.get("seconds", 0)
                self.set_timer(seconds)
                print(f"[Timer] Received set command: {seconds}s")
            
            elif msg.topic == "timer/increment":
                increment = data.get("increment", 10)
                self.set_n_increment(increment)
                print(f"[Timer] Received increment command: {increment}s")
        
        except Exception as e:
            print(f"[Timer] Error processing MQTT message: {e}")
    
    def set_timer(self, seconds):
        with self.lock:
            self.remaining_time = int(seconds)
            self.is_blinking = False
            print(f"[Timer] Set to: {seconds}s")
    
    def set_n_increment(self, n):
        with self.lock:
            self.n_increment = int(n)
            print(f"[Timer] Button increment set to: {n}s")
    
    def button_pressed(self):
        with self.lock:
            if self.is_blinking:
                self.is_blinking = False
                self.remaining_time = 0
                print("[Timer] Blinking stopped by button press")
            else:
                self.remaining_time += self.n_increment
                print(f"[Timer] Added {self.n_increment}s. Total: {self.remaining_time}s")
    
    def run(self):
        while self.running:
            display_value = ""
            
            with self.lock:
                if self.is_blinking:
                    # Treperenje - naizmenično prikazuje 0000 i prazan displej
                    display_value = "0000" if int(time.time()) % 2 == 0 else "    "
                else:
                    if self.remaining_time > 0:
                        self.remaining_time -= 1
                        
                        # Formatiranje u MMSS (bez dvotačke)
                        mins, secs = divmod(self.remaining_time, 60)
                        display_value = f"{mins:02d}{secs:02d}"
                        
                        if self.remaining_time == 0:
                            self.is_blinking = True
                            print("[Timer] Time expired! Starting blink...")
                    else:
                        display_value = "0000"
            
            # Slanje vrednosti ka MQTT-u
            self.callback(display_value)
            time.sleep(1)
    
    def stop(self):
        self.running = False
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()