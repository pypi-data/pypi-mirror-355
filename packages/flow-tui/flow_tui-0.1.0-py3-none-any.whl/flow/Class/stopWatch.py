import time

class Stopwatch:
    def __init__(self):
        self.running = False
        self.start_time = None
        self.elapsed = 0

    def start(self):
        if not self.running:
            if self.start_time is None:
                self.start_time = time.time()
            else:
                self.start_time = time.time() - self.elapsed
            self.running = True

    def stop(self):
        if self.running and self.start_time is not None:
            self.elapsed = time.time() - self.start_time
            self.running = False

    def reset(self):
        self.start_time = None
        self.elapsed = 0
        self.running = False

    def get_elapsed(self):
        if self.start_time is None:
            return self.elapsed
        if self.running:
            return time.time() - self.start_time
        else:
            return self.elapsed

