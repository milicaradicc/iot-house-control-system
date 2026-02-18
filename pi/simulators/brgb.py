class RGBLedSimulator:
    def __init__(self ,callback):
        
        self.color ="off"
        self.callback = callback

    def _update(self):
        color_state = self.color
        self.callback(color_state)
        print(f"[RGB] Current state: {color_state}")

    def turnOff(self):
        self.color = "off"
        self._update()
        
    def white(self):
        self.color = "white"
        self._update()
        
    def red(self):
        self.color = "red"
        self._update()

    def green(self):
        self.color = "green"
        self._update()
        
    def blue(self):
        self.color = "blue"
        self._update() 

    def yellow(self):
        self.color = "yellow"
        self._update()
        
    def purple(self):
        self.color = "purple"
        self._update()
        
    def lightBlue(self):
        self.color = "light blue"
        self._update()

