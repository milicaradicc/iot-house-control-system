import RPi.GPIO as GPIO
import time

class DHT(object):
    def __init__(self, pin):
        self.pin = pin
        self.temperature = 0
        self.humidity = 0

    def read_sensor(self):
        # Inicijalizacija signala
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.LOW)
        time.sleep(0.02) # Start signal
        GPIO.output(self.pin, GPIO.HIGH)
        GPIO.setup(self.pin, GPIO.IN)

        # Čekanje na odziv senzora (80us Low, 80us High)
        t0 = time.time()
        while GPIO.input(self.pin) == GPIO.HIGH:
            if time.time() - t0 > 0.001: return -2 # Timeout

        while GPIO.input(self.pin) == GPIO.LOW: pass
        while GPIO.input(self.pin) == GPIO.HIGH: pass

        bits_time = []
        for i in range(40):
            while GPIO.input(self.pin) == GPIO.LOW: pass
            t_start = time.time()
            while GPIO.input(self.pin) == GPIO.HIGH: pass
            bits_time.append(time.time() - t_start)

        # Rekonstrukcija bajtova
        res = [0] * 5
        for i in range(40):
            if bits_time[i] > 0.000048: # Granica za "1" na 48 mikrosekundi
                res[i // 8] |= (1 << (7 - (i % 8)))

        # Checksum provera
        if res[4] == ((res[0] + res[1] + res[2] + res[3]) & 0xFF):
            self.humidity = res[0]
            self.temperature = res[2] + res[3] * 0.1
            return 0 # Sve OK
        return -1 # Checksum greška

def run_dht_loop(dht, delay, callback, stop_event, code, publish_event, dht_settings):
    total, success = 0, 0
    while not stop_event.is_set():
        res = dht.read_sensor()
        total += 1
        if res == 0:
            success += 1
            callback(dht.humidity, dht.temperature, publish_event, dht_settings, code)
        
        rate = (success / total) * 100
        status = "OK" if res == 0 else ("TIMEOUT" if res == -2 else "CHECKSUM_ERR")
        print(f"[{code}] {status} | T: {dht.temperature}°C | Rate: {rate:.1f}%")
        
        # DHT11/22 zahtevaju bar 2s pauze između čitanja
        stop_event.wait(timeout=max(delay, 2.0))

    GPIO.cleanup(dht.pin)