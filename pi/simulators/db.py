class DBSimulator:
    def __init__(self, callback):
        self.is_on = False
        self.callback = callback

    def on(self):
        if not self.is_on:
            self.is_on = True
            self.callback(True)
            print("[DB] BUZZER is: ON")

    def off(self):
        if self.is_on:
            self.is_on = False
            self.callback(False)
            print("[DB] BUZZER is: OFF")
