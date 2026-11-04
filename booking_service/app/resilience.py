import asyncio
import logging
import time
from collections import deque

import grpc

from app.config import (
    CB_FAILURE_THRESHOLD,
    CB_OPEN_SECONDS,
    CB_WINDOW_SIZE,
    RETRY_BASE_DELAY_MS,
    RETRY_MAX_ATTEMPTS,
)

log = logging.getLogger("booking.resilience")

RETRYABLE_CODES = {grpc.StatusCode.UNAVAILABLE, grpc.StatusCode.DEADLINE_EXCEEDED}
FAILURE_CODES = {
    grpc.StatusCode.UNAVAILABLE,
    grpc.StatusCode.DEADLINE_EXCEEDED,
    grpc.StatusCode.INTERNAL,
    grpc.StatusCode.UNKNOWN,
}

CLOSED = "CLOSED"
OPEN = "OPEN"
HALF_OPEN = "HALF_OPEN"


class CircuitOpenError(Exception):
    pass


class RetryInterceptor(grpc.aio.UnaryUnaryClientInterceptor):
    async def intercept_unary_unary(self, continuation, client_call_details, request):
        delay = RETRY_BASE_DELAY_MS / 1000
        attempt = 1
        while True:
            call = await continuation(client_call_details, request)
            code = await call.code()
            if code not in RETRYABLE_CODES or attempt >= RETRY_MAX_ATTEMPTS:
                return call
            method = client_call_details.method
            if isinstance(method, bytes):
                method = method.decode()
            log.warning("retry method=%s attempt=%s code=%s delay=%.3fs", method, attempt, code.name, delay)
            await asyncio.sleep(delay)
            delay *= 2
            attempt += 1


class CircuitBreakerInterceptor(grpc.aio.UnaryUnaryClientInterceptor):
    def __init__(self):
        self.state = CLOSED
        self.results = deque(maxlen=CB_WINDOW_SIZE)
        self.opened_at = 0.0
        self.probe_in_flight = False

    def switch(self, new_state: str) -> None:
        if new_state == self.state:
            return
        log.warning("circuit breaker %s -> %s", self.state, new_state)
        self.state = new_state

    def open(self) -> None:
        self.opened_at = time.monotonic()
        self.results.clear()
        self.probe_in_flight = False
        self.switch(OPEN)

    def before_call(self) -> None:
        if self.state == OPEN:
            if time.monotonic() - self.opened_at < CB_OPEN_SECONDS:
                raise CircuitOpenError("circuit breaker is open")
            self.switch(HALF_OPEN)
        if self.state == HALF_OPEN:
            if self.probe_in_flight:
                raise CircuitOpenError("circuit breaker is half open")
            self.probe_in_flight = True

    def record(self, failed: bool) -> None:
        if self.state == OPEN:
            return
        if self.state == HALF_OPEN:
            self.probe_in_flight = False
            if failed:
                self.open()
            else:
                self.results.clear()
                self.switch(CLOSED)
            return
        self.results.append(failed)
        if sum(self.results) >= CB_FAILURE_THRESHOLD:
            self.open()

    async def intercept_unary_unary(self, continuation, client_call_details, request):
        self.before_call()
        try:
            call = await continuation(client_call_details, request)
            code = await call.code()
        except BaseException:
            self.probe_in_flight = False
            raise
        self.record(code in FAILURE_CODES)
        return call
