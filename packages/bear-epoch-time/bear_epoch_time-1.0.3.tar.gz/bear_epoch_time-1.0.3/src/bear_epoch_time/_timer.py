import sys
from collections.abc import Callable, Generator
from contextlib import contextmanager
from functools import wraps

if sys.version_info < (3, 11):
    from bear_epoch_time._time_class_legacy import EpochTimestamp
else:
    from bear_epoch_time._time_class import EpochTimestamp

from .basic_logger.logger import BasicLogger


def create_timer(**defaults) -> Callable:
    """A way to set defaults for a frequently used timer decorator."""

    def timer_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            defaults["name"] = func.__name__
            with timer(**defaults):
                return func(*args, **kwargs)

        return wrapper

    return timer_decorator


@contextmanager
def timer(**kwargs) -> Generator["TimerData", None, None]:
    data: TimerData = kwargs.get("data", None) or TimerData(kwargs=kwargs)
    data.start()
    try:
        yield data
    finally:
        data.stop()


class TimerData:
    def __init__(self, **kwargs) -> None:
        self.name: str = kwargs.get("name", "Default Timer")
        self.start_time: EpochTimestamp = EpochTimestamp(0)
        self.end_time: EpochTimestamp = EpochTimestamp(0)
        self._raw_elapsed_time: EpochTimestamp = EpochTimestamp(0)
        self.console = kwargs.get("console", None) or BasicLogger()
        self.callback: Callable | None = kwargs.get("callback", None)
        self._style: str = kwargs.get("style", "bold green")

    def start(self) -> None:
        self.start_time = EpochTimestamp.now()

    def send_callback(self) -> None:
        if self.callback is not None:
            self.callback(self)

    def stop(self) -> None:
        self.end_time = EpochTimestamp.now()
        self._raw_elapsed_time = EpochTimestamp(self.end_time - self.start_time)
        if self.callback:
            self.send_callback()
        if self.console:
            self.console.print(f"[{self.name}] Elapsed time: {self.elapsed_seconds:.2f} seconds", style=self._style)

    @property
    def elapsed_milliseconds(self) -> int:
        if self._raw_elapsed_time:
            return self._raw_elapsed_time.to_milliseconds
        return -1

    @property
    def elapsed_seconds(self) -> int:
        if self._raw_elapsed_time:
            return self._raw_elapsed_time.to_seconds
        return -1


__all__ = ["TimerData"]
