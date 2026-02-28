"""
Deterministic Timing Wrappers.

Provides timing utilities for budget enforcement while maintaining
determinism for reproducibility.
"""

import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class TimingResult:
    """Result of a timed operation.

    Attributes:
        elapsed_ms: Elapsed time in milliseconds
        start_time: Start timestamp
        end_time: End timestamp
    """

    elapsed_ms: int
    start_time: float
    end_time: float


class DeterministicTimer:
    """Timer that provides both real timing and deterministic values.

    For determinism tier D0, we use simulated timing that produces
    consistent values across runs.
    """

    def __init__(self, deterministic: bool = True, base_time: float = 1000000.0):
        """Initialize the timer.

        Args:
            deterministic: Whether to use deterministic timing
            base_time: Base time for deterministic mode
        """
        self._deterministic = deterministic
        self._base_time = base_time
        self._elapsed = 0.0
        self._start_time: Optional[float] = None
        self._last_tick = base_time

    def start(self) -> float:
        """Start the timer.

        Returns:
            Start timestamp
        """
        self._start_time = self._get_time()
        return self._start_time

    def stop(self) -> TimingResult:
        """Stop the timer and return the result.

        Returns:
            Timing result with elapsed time
        """
        if self._start_time is None:
            raise ValueError("Timer not started")

        end_time = self._get_time()
        elapsed = end_time - self._start_time

        result = TimingResult(
            elapsed_ms=int(elapsed),
            start_time=self._start_time,
            end_time=end_time,
        )

        self._start_time = None
        return result

    def tick(self, ms: int = 0) -> int:
        """Simulate a time tick for deterministic mode.

        Args:
            ms: Milliseconds to advance (0 for auto-increment)

        Returns:
            Current simulated time in ms
        """
        if ms > 0:
            self._last_tick += ms
        else:
            self._last_tick += 1  # Minimal increment
        self._elapsed = self._last_tick - self._base_time
        return int(self._elapsed)

    def elapsed_ms(self) -> int:
        """Get elapsed time in milliseconds.

        Returns:
            Elapsed time in ms
        """
        if self._start_time is not None:
            current = self._get_time()
            return int(current - self._start_time)
        return int(self._elapsed)

    def _get_time(self) -> float:
        """Get current time based on mode.

        Returns:
            Current timestamp
        """
        if self._deterministic:
            return self._last_tick
        return time.perf_counter() * 1000  # Convert to ms


def format_duration(ms: int) -> str:
    """Format duration in milliseconds to human-readable string.

    Args:
        ms: Duration in milliseconds

    Returns:
        Formatted duration string
    """
    if ms < 1000:
        return f"{ms}ms"
    elif ms < 60000:
        seconds = ms / 1000
        return f"{seconds:.2f}s"
    else:
        minutes = ms / 60000
        return f"{minutes:.2f}m"
