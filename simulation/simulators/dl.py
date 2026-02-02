class DLSimulator:
    def __init__(self, callback):
        self.is_on = False
        self.callback = callback

    def on(self):
        if not self.is_on:
            self.is_on = True
            self.callback(True)
            print("[DL] LED is: ON")

    def off(self):
        if self.is_on:
            self.is_on = False
            self.callback(False)
            print("[DL] LED is: OFF")
