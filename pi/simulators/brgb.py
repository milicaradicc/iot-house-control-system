class RGBLedSimulator:
    def __init__(self ,callback):
        
        self.color = {"R": 0, "G": 0, "B": 0}
        self.callback = callback

    def _update(self):
        color_state = self.color.copy()
        self.callback(color_state)
        print(f"[RGB] Current state: {color_state}")

    def turnOff(self):
        self.color = {"R": 0, "G": 0, "B": 0}
        self._update()
        
    def white(self):
        self.color = {"R": 1, "G": 1, "B": 1}
        self._update()
        
    def red(self):
        self.color = {"R": 1, "G": 0, "B": 0}
        self._update()

    def green(self):
        self.color = {"R": 0, "G": 1, "B": 0}
        self._update()
        
    def blue(self):
        self.color = {"R": 0, "G": 0, "B": 1}
        self._update() 

    def yellow(self):
        self.color = {"R": 1, "G": 1, "B": 0}
        self._update()
        
    def purple(self):
        self.color = {"R": 1, "G": 0, "B": 1}
        self._update()
        
    def lightBlue(self):
        self.color = {"R": 0, "G": 1, "B": 1}
        self._update()

