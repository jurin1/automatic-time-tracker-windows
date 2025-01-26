from datetime import datetime
from pynput import mouse, keyboard


class ActivityMonitor:
    def __init__(self):
        self.last_activity = datetime.now()

    def on_move(self, x, y):
        self.last_activity = datetime.now()

    def on_click(self, x, y, button, pressed):
        self.last_activity = datetime.now()

    def on_press(self, key):
        self.last_activity = datetime.now()

    def start(self):
        mouse_listener = mouse.Listener(
            on_move=self.on_move, on_click=self.on_click)
        keyboard_listener = keyboard.Listener(on_press=self.on_press)
        mouse_listener.start()
        keyboard_listener.start()
        return mouse_listener, keyboard_listener

    def get_last_activity_time(self):
        return self.last_activity
