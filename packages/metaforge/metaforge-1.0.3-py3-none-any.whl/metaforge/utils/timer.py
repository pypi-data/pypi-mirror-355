import time

class Timer:
    def __init__(self):
        self.start_time = time.time()

    def stop(self):
        return time.time() - self.start_time
