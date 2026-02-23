class LCDSimulator:
    def __init__(self, callback):
        self.text = ""
        self.callback = callback

    def _update(self):
        self.callback(self.text)
        print(f"[LCD] Displaying:\n{self.text}")

    def display(self, text):
        self.text = text
        self._update()

    def clear(self):
        self.text = ""
        self._update()