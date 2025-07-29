import contextlib
from typing import Iterable
from typing import Sequence
from typing import TypeVar

from imbue_core.errors import ImbueError

T = TypeVar("T")


class ImbueItertoolsValueError(ImbueError, ValueError):
    """This value error is thrown when the assumptions of the itertools module are violated."""


def only(x: Iterable[T]) -> T:
    try:
        (value,) = x
    except ValueError as e:
        message = "Expected exactly one value"
        if isinstance(x, Sequence):
            with contextlib.suppress():
                message += f" but got {len(x)} {x[:3]=}"
        raise ImbueItertoolsValueError(message) from e

    return value
