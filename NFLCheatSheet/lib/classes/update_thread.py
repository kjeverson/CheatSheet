import threading
import time


class UpdateThread(threading.Thread):
    def __init__(self, ID):
        self.ID = ID
        self.progress = 0
        self.total = 0
        self.state = ""
        super().__init__()
