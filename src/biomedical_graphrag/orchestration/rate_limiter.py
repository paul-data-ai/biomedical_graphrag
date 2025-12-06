"""Advanced rate limiter with exponential backoff and circuit breaker pattern."""

import asyncio
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable

from biomedical_graphrag.utils.logger_util import setup_logging

logger = setup_logging()


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""

    requests_per_second: float = 3.0
    requests_per_minute: int = 100
    burst_size: int = 10
    retry_attempts: int = 5
    base_delay: float = 1.0
    max_delay: float = 60.0
    circuit_failure_threshold: int = 5
    circuit_timeout: float = 300.0  # 5 minutes


class AdaptiveRateLimiter:
    """
    Adaptive rate limiter with circuit breaker pattern.

    Handles:
    - Token bucket for burst support
    - Sliding window for per-minute limits
    - Exponential backoff with jitter
    - Circuit breaker for persistent failures
    """

    def __init__(self, config: RateLimitConfig | None = None) -> None:
        """
        Initialize the rate limiter.

        Args:
            config: Rate limit configuration
        """
        self.config = config or RateLimitConfig()

        # Token bucket for per-second rate limiting
        self.tokens = self.config.burst_size
        self.last_update = time.time()
        self.lock = asyncio.Lock()

        # Sliding window for per-minute tracking
        self.request_times: deque[float] = deque(maxlen=self.config.requests_per_minute)

        # Circuit breaker
        self.circuit_state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: float | None = None
        self.success_count_in_half_open = 0

    async def acquire(self) -> None:
        """Acquire permission to make a request."""
        async with self.lock:
            # Check circuit breaker
            await self._check_circuit()

            if self.circuit_state == CircuitState.OPEN:
                raise RuntimeError("Circuit breaker is OPEN - too many failures")

            # Refill tokens based on elapsed time
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(
                self.config.burst_size,
                self.tokens + elapsed * self.config.requests_per_second,
            )
            self.last_update = now

            # Check per-minute limit
            self._clean_old_requests(now)
            if len(self.request_times) >= self.config.requests_per_minute:
                oldest = self.request_times[0]
                wait_time = 60.0 - (now - oldest)
                if wait_time > 0:
                    logger.warning(
                        f"Per-minute limit reached, waiting {wait_time:.2f}s"
                    )
                    await asyncio.sleep(wait_time)
                    self._clean_old_requests(time.time())

            # Wait for token availability
            while self.tokens < 1:
                wait_time = (1 - self.tokens) / self.config.requests_per_second
                logger.debug(f"Rate limit: waiting {wait_time:.2f}s for token")
                await asyncio.sleep(wait_time)

                # Refill after waiting
                now = time.time()
                elapsed = now - self.last_update
                self.tokens = min(
                    self.config.burst_size,
                    self.tokens + elapsed * self.config.requests_per_second,
                )
                self.last_update = now

            # Consume token
            self.tokens -= 1
            self.request_times.append(time.time())

    def _clean_old_requests(self, now: float) -> None:
        """Remove request times older than 1 minute."""
        cutoff = now - 60.0
        while self.request_times and self.request_times[0] < cutoff:
            self.request_times.popleft()

    async def _check_circuit(self) -> None:
        """Check and update circuit breaker state."""
        now = time.time()

        if self.circuit_state == CircuitState.OPEN:
            # Check if timeout has passed
            if (
                self.last_failure_time
                and now - self.last_failure_time >= self.config.circuit_timeout
            ):
                logger.info("Circuit breaker entering HALF_OPEN state")
                self.circuit_state = CircuitState.HALF_OPEN
                self.success_count_in_half_open = 0

    async def record_success(self) -> None:
        """Record a successful request."""
        async with self.lock:
            if self.circuit_state == CircuitState.HALF_OPEN:
                self.success_count_in_half_open += 1
                # After 3 successes, close the circuit
                if self.success_count_in_half_open >= 3:
                    logger.info("Circuit breaker closing - service recovered")
                    self.circuit_state = CircuitState.CLOSED
                    self.failure_count = 0
            elif self.circuit_state == CircuitState.CLOSED:
                # Reset failure count on success
                self.failure_count = 0

    async def record_failure(self, exception: Exception) -> None:
        """Record a failed request."""
        async with self.lock:
            self.failure_count += 1
            self.last_failure_time = time.time()

            logger.warning(
                f"Request failed ({self.failure_count}/"
                f"{self.config.circuit_failure_threshold}): {exception}"
            )

            if self.circuit_state == CircuitState.HALF_OPEN:
                # Any failure in half-open immediately opens circuit
                logger.error("Circuit breaker opening - failure in HALF_OPEN state")
                self.circuit_state = CircuitState.OPEN
            elif self.failure_count >= self.config.circuit_failure_threshold:
                logger.error(
                    f"Circuit breaker opening - {self.failure_count} consecutive failures"
                )
                self.circuit_state = CircuitState.OPEN

    async def execute_with_retry(
        self, func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> Any:
        """
        Execute a function with rate limiting and exponential backoff retry.

        Args:
            func: Async function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result from func

        Raises:
            Exception: If all retries exhausted
        """
        last_exception = None

        for attempt in range(self.config.retry_attempts):
            try:
                # Acquire rate limit permission
                await self.acquire()

                # Execute function
                result = await func(*args, **kwargs)

                # Record success
                await self.record_success()

                return result

            except Exception as e:
                last_exception = e
                await self.record_failure(e)

                # Check if we should retry
                if attempt < self.config.retry_attempts - 1:
                    # Calculate exponential backoff with jitter
                    delay = min(
                        self.config.base_delay * (2**attempt),
                        self.config.max_delay,
                    )
                    # Add jitter (±20%)
                    import random

                    jitter = delay * 0.2 * (2 * random.random() - 1)
                    delay_with_jitter = delay + jitter

                    logger.warning(
                        f"Attempt {attempt + 1}/{self.config.retry_attempts} "
                        f"failed: {e}. Retrying in {delay_with_jitter:.2f}s"
                    )
                    await asyncio.sleep(delay_with_jitter)
                else:
                    logger.error(
                        f"All {self.config.retry_attempts} retry attempts exhausted"
                    )

        raise last_exception  # type: ignore

    def get_stats(self) -> dict[str, Any]:
        """Get current rate limiter statistics."""
        return {
            "tokens_available": self.tokens,
            "requests_in_last_minute": len(self.request_times),
            "circuit_state": self.circuit_state.value,
            "failure_count": self.failure_count,
            "config": {
                "requests_per_second": self.config.requests_per_second,
                "requests_per_minute": self.config.requests_per_minute,
                "burst_size": self.config.burst_size,
            },
        }
