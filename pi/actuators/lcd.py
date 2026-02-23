from pcf8574 import PCF8574_GPIO
from adafruit_lcd import Adafruit_CharLCD

class LCD:
    def __init__(self, address=0x27, alternate_address=0x3F):
        self.address = address
        self.alternate_address = alternate_address
        self.mcp = self._init_mcp()
        self.lcd = Adafruit_CharLCD(pin_rs=0, pin_e=2, pins_db=[4,5,6,7], GPIO=self.mcp)
        self.mcp.output(3, 1)
        self.lcd.begin(16, 2)

    def _init_mcp(self):
        try:
            return PCF8574_GPIO(self.address)
        except:
            try:
                return PCF8574_GPIO(self.alternate_address)
            except:
                print('I2C Address Error!')
                raise Exception("Could not find LCD I2C address.")

    def display(self, text):
        self.lcd.clear()
        self.lcd.setCursor(0, 0)
        self.lcd.message(text)

    def clear(self):
        self.lcd.clear()