import RPi.GPIO as GPIO
import time
from threading import Event


class DHT(object):
    DHTLIB_OK = 0
    DHTLIB_ERROR_CHECKSUM = -1
    DHTLIB_ERROR_TIMEOUT = -2
    DHTLIB_INVALID_VALUE = -999

    DHTLIB_DHT11_WAKEUP = 0.020
    DHTLIB_TIMEOUT = 0.0001

    humidity = 0
    temperature = 0

    def __init__(self, pin):
        self.pin = pin
        self.bits = [0, 0, 0, 0, 0]

    def _read_raw(self, pin, wakeupDelay):
        mask = 0x80
        idx = 0
        self.bits = [0, 0, 0, 0, 0]
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)
        time.sleep(wakeupDelay)
        GPIO.output(pin, GPIO.HIGH)
        GPIO.setup(pin, GPIO.IN)

        loopCnt = self.DHTLIB_TIMEOUT
        t = time.time()
        while GPIO.input(pin) == GPIO.LOW:
            if (time.time() - t) > loopCnt:
                return self.DHTLIB_ERROR_TIMEOUT

        t = time.time()
        while GPIO.input(pin) == GPIO.HIGH:
            if (time.time() - t) > loopCnt:
                return self.DHTLIB_ERROR_TIMEOUT

        for i in range(0, 40, 1):
            t = time.time()
            while GPIO.input(pin) == GPIO.LOW:
                if (time.time() - t) > loopCnt:
                    return self.DHTLIB_ERROR_TIMEOUT

            t = time.time()
            while GPIO.input(pin) == GPIO.HIGH:
                if (time.time() - t) > loopCnt:
                    return self.DHTLIB_ERROR_TIMEOUT

            if (time.time() - t) > 0.00005:
                self.bits[idx] |= mask

            mask >>= 1
            if mask == 0:
                mask = 0x80
                idx += 1

        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.HIGH)
        return self.DHTLIB_OK

    def readSensor(self):
        rv = self._read_raw(self.pin, self.DHTLIB_DHT11_WAKEUP)
        if rv is not self.DHTLIB_OK:
            self.humidity = self.DHTLIB_INVALID_VALUE
            self.temperature = self.DHTLIB_INVALID_VALUE
            return rv
        self.humidity = self.bits[0]
        self.temperature = self.bits[2] + self.bits[3] * 0.1
        sumChk = ((self.bits[0] + self.bits[1] + self.bits[2] + self.bits[3]) & 0xFF)
        if self.bits[4] is not sumChk:
            return self.DHTLIB_ERROR_CHECKSUM
        return self.DHTLIB_OK


def parseCheckCode(code):
    if code == 0:
        return "DHTLIB_OK"
    elif code == -1:
        return "DHTLIB_ERROR_CHECKSUM"
    elif code == -2:
        return "DHTLIB_ERROR_TIMEOUT"
    elif code == -999:
        return "DHTLIB_INVALID_VALUE"


def run_dht_loop(dht, delay, callback, stop_event, code, publish_event, dht_settings):
    try:
        last_temperature = None
        last_humidity = None

        while not stop_event.is_set():
            result = dht.readSensor()

            if result == DHT.DHTLIB_OK:
                humidity = dht.humidity
                temperature = dht.temperature

                if temperature != last_temperature or humidity != last_humidity:
                    callback(humidity, temperature, publish_event, dht_settings, code)
                    last_humidity = humidity
                    last_temperature = temperature
            else:
                print(f"[DHT] Read error: {parseCheckCode(result)}")

            time.sleep(delay)

    finally:
        GPIO.cleanup(dht.pin)