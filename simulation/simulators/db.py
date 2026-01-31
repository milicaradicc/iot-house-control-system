class DBSimulator:
    def __init__(self):
        self.is_on = False

    def on(self):
        if not self.is_on:
            self.is_on = True
            print("[DB] BUZZER is: ON")

    def off(self):
        if self.is_on:
            self.is_on = False
            print("[DB] BUZZER is: OFF")
