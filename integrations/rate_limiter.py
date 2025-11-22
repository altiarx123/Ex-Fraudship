import time
import threading


class RateLimiter:
    def __init__(self, window_seconds: int = 60):
        self.window = window_seconds
        self.lock = threading.Lock()
        self.last = {}

    def allowed(self, key: str) -> bool:
        now = time.time()
        with self.lock:
            last = self.last.get(key)
            if last is None or (now - last) >= self.window:
                self.last[key] = now
                return True
            return False

    def update(self, key: str):
        with self.lock:
            self.last[key] = time.time()
