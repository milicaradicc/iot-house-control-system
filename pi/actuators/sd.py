import time
import threading

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None


class SegmentDisplay:
    """
    4-digit 7-segment display driven directly via GPIO pins.
    Each digit is multiplexed — one digit active at a time.
    
    Segment layout (common cathode):
         _
        |_|
        |_|
        
    Segments: A B C D E F G (7 segments)
    Digits:   D1 D2 D3 D4 (4 digit select pins)
    """

    # Segment encoding for digits 0-9
    # Segments: A  B  C  D  E  F  G
    DIGITS = {
        '0': [1, 1, 1, 1, 1, 1, 0],
        '1': [0, 1, 1, 0, 0, 0, 0],
        '2': [1, 1, 0, 1, 1, 0, 1],
        '3': [1, 1, 1, 1, 0, 0, 1],
        '4': [0, 1, 1, 0, 0, 1, 1],
        '5': [1, 0, 1, 1, 0, 1, 1],
        '6': [1, 0, 1, 1, 1, 1, 1],
        '7': [1, 1, 1, 0, 0, 0, 0],
        '8': [1, 1, 1, 1, 1, 1, 1],
        '9': [1, 1, 1, 1, 0, 1, 1],
        ' ': [0, 0, 0, 0, 0, 0, 0],
    }

    def __init__(self, segment_pins, digit_pins):
        """
        segment_pins: list of 7 GPIO pins [A, B, C, D, E, F, G]
        digit_pins:   list of 4 GPIO pins [D1, D2, D3, D4]
        """
        self.segment_pins = segment_pins
        self.digit_pins = digit_pins
        self._current_text = "    "
        self._running = False
        self._thread = None

        for pin in self.segment_pins + self.digit_pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)

    def _display_digit(self, position, char):
        """Activate one digit position and set segments."""
        # Turn off all digits first
        for pin in self.digit_pins:
            GPIO.output(pin, GPIO.LOW)

        segments = self.DIGITS.get(char, self.DIGITS[' '])
        for pin, val in zip(self.segment_pins, segments):
            GPIO.output(pin, val)

        # Activate the selected digit
        GPIO.output(self.digit_pins[position], GPIO.HIGH)

    def display(self, text):
        """Set text to display (max 4 chars, padded with spaces)."""
        self._current_text = text[:4].ljust(4)

    def _multiplex_loop(self):
        """Continuously multiplex through 4 digits."""
        while self._running:
            for i, char in enumerate(self._current_text):
                self._display_digit(i, char)
                time.sleep(0.005)  # 5ms per digit = 200Hz refresh

    def start(self):
        """Start multiplexing in background thread."""
        self._running = True
        self._thread = threading.Thread(target=self._multiplex_loop)
        self._thread.daemon = True
        self._thread.start()

    def stop(self):
        """Stop multiplexing and clear display."""
        self._running = False
        for pin in self.segment_pins + self.digit_pins:
            GPIO.output(pin, GPIO.LOW)

    def cleanup(self):
        self.stop()
        GPIO.cleanup(self.segment_pins + self.digit_pins)