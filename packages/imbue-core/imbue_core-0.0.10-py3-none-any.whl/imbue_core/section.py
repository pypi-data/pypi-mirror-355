"""
Provides a context manager for logging a potentially time-consuming process, or a "section".

- Prints logs at start and end of a section.

- Prints a Markdown-like heading for nested sections: "#" for top-level sections, "##" for one level down, and so on.

- Emits structured logs for easier query.

The SectionWrapper context manager can be used to time the __enter__ and __exit__ methods of an existing context manager.
"""
import contextlib
import threading
import time
import typing
from asyncio import CancelledError
from types import TracebackType
from typing import Optional
from typing import Type
from typing import Union

from loguru import logger

_monotonic_base = time.monotonic()


def _monotonic_time() -> float:
    """A wrapper around time.monotonic() to make the return values a bit smaller and easier to read by a human."""
    return time.monotonic() - _monotonic_base


class _ThreadLocal(threading.local):
    def __init__(self) -> None:
        self.next_section_level: int = 0


_thread_local = _ThreadLocal()


class Section(contextlib.ContextDecorator):
    def __init__(self, message: str, log_level: Union[int, str] = "INFO") -> None:
        # TODO: loguru doesn't properly display integer log levels like e.g. logging.INFO
        self.message = message
        self.log_level = log_level

    def __enter__(self) -> "Section":
        level = _thread_local.next_section_level
        _thread_local.next_section_level += 1
        self.header = "#" * (level + 1)
        self.start_monotonic_time = _monotonic_time()
        start_clock_time = time.time()
        self.section = {
            "name": self.message,
            "level": level,
            "start_monotonic_time": self.start_monotonic_time,
            "start_clock_time": start_clock_time,
        }
        logger.log(
            self.log_level,
            f"{self.header} Start: {self.message}",
            section=self.section,
        )
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        _thread_local.next_section_level -= 1
        finish_monotonic_time = _monotonic_time()
        finish_clock_time = time.time()
        duration_seconds = finish_monotonic_time - self.start_monotonic_time
        section = self.section | {
            "finish_monotonic_time": finish_monotonic_time,
            "finish_clock_time": finish_clock_time,
            "duration_seconds": duration_seconds,
        }
        self.elapsed = duration_seconds

        if exc_val is None:
            logger.log(
                self.log_level,
                f"{self.header} Done: {self.message} (took {duration_seconds:.2f} seconds)",
                section=section | {"result": "success"},
            )
        else:
            if isinstance(exc_val, CancelledError):
                logger.log(
                    self.log_level,
                    f"{self.header} Cancelled: {self.message} (took {duration_seconds:.2f} seconds)",
                    section=section | {"result": "cancelled"},
                )
            else:
                logger.log(
                    self.log_level,
                    f"{self.header} Failed: {self.message} (within {duration_seconds:.2f} seconds)",
                    section=section | {"result": "failed"},
                )


T = typing.TypeVar("T")


class SectionWrapper(contextlib.AbstractContextManager[T]):
    def __init__(self, cm: contextlib.AbstractContextManager[T], enter_message: str, exit_message: str) -> None:
        self._cm = cm
        self._enter_message = enter_message
        self._exit_message = exit_message

    def __enter__(self) -> T:
        with Section(self._enter_message) as cm:
            return self._cm.__enter__()

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        with Section(self._exit_message):
            self._cm.__exit__(exc_type, exc_val, exc_tb)
