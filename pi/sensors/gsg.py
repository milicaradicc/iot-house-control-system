import time
import math
from threading import Event

try:
    import smbus2 as smbus
except ImportError:
    import smbus

# MPU6050 registri
MPU6050_ADDR = 0x68
PWR_MGMT_1   = 0x6B
ACCEL_XOUT_H = 0x3B
ACCEL_YOUT_H = 0x3D
ACCEL_ZOUT_H = 0x3F
GYRO_XOUT_H  = 0x43
GYRO_YOUT_H  = 0x45
GYRO_ZOUT_H  = 0x47


class GyroscopeSensor:
    def __init__(self, address=MPU6050_ADDR, bus=1):
        self.address = address
        self.bus = smbus.SMBus(bus)
        # Wake up MPU6050
        self.bus.write_byte_data(self.address, PWR_MGMT_1, 0)

    def _read_raw(self, reg):
        high = self.bus.read_byte_data(self.address, reg)
        low  = self.bus.read_byte_data(self.address, reg + 1)
        val  = (high << 8) | low
        if val >= 0x8000:
            val -= 65536
        return val

    def read_accelerometer(self):
        x = self._read_raw(ACCEL_XOUT_H) / 16384.0
        y = self._read_raw(ACCEL_YOUT_H) / 16384.0
        z = self._read_raw(ACCEL_ZOUT_H) / 16384.0
        return x, y, z

    def read_gyroscope(self):
        x = self._read_raw(GYRO_XOUT_H) / 131.0
        y = self._read_raw(GYRO_YOUT_H) / 131.0
        z = self._read_raw(GYRO_ZOUT_H) / 131.0
        return x, y, z

    def read_magnitude(self):
        """Returns total acceleration magnitude."""
        x, y, z = self.read_accelerometer()
        return math.sqrt(x**2 + y**2 + z**2)


def run_gsg_loop(sensor, delay, callback, stop_event, code, publish_event, gsg_settings, threshold=0.5, verbose=False):
    while not stop_event.is_set():
        try:
            magnitude = sensor.read_magnitude()
            deviation = abs(magnitude - 1.0)
            movement_detected = deviation > threshold
            callback(movement_detected, magnitude, publish_event, gsg_settings, code, verbose)  
        except Exception as e:
            print(f"[GSG] Read error: {e}")
        time.sleep(delay)