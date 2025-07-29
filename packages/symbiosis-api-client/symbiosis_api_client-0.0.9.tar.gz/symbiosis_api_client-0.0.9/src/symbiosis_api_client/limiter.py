import threading
import time
from datetime import timedelta

import httpx


class SyncLimiter:
    def __init__(self, max_rate: int, time_period: float):
        self.max_rate = max_rate
        self.time_period = time_period
        self.tokens = max_rate
        self.lock = threading.Lock()
        self.last_refill = time.monotonic()

    def acquire(self):
        with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            if elapsed >= self.time_period:
                self.tokens = self.max_rate
                self.last_refill = now

            if self.tokens == 0:
                sleep_time = self.time_period - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)
                self.tokens = self.max_rate
                self.last_refill = time.monotonic()

            self.tokens -= 1


class SyncRateLimitedTransport(httpx.BaseTransport):
    def __init__(
        self,
        *,
        limiter: SyncLimiter,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._limiter = limiter
        self._transport = transport or httpx.HTTPTransport()

    @classmethod
    def create(cls, rate: int, period: timedelta = timedelta(seconds=1), **kwargs):
        limiter = SyncLimiter(rate, period.total_seconds())
        transport = httpx.HTTPTransport(**kwargs)
        return cls(limiter=limiter, transport=transport)

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self._limiter.acquire()
        return self._transport.handle_request(request)
