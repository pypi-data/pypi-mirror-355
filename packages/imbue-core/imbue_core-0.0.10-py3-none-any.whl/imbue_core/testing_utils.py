import asyncio
import inspect
import os
import shutil
from contextlib import asynccontextmanager
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from typing import AsyncGenerator
from typing import Callable
from typing import ContextManager
from typing import Coroutine
from typing import Generator
from typing import Iterable
from typing import Optional
from typing import Protocol
from typing import Sequence
from typing import TYPE_CHECKING
from typing import TypeVar
from typing import Union
from uuid import uuid4

import anyio
import pytest
import pytest_asyncio
from _pytest.fixtures import Config
from _pytest.python import Function

from imbue_core.common import TEMP_DIR

if TYPE_CHECKING:
    # noinspection PyProtectedMember
    from _pytest.fixtures import _ScopeName

T = TypeVar("T")

_TestFunc = Union[Callable[..., None], Callable[..., Coroutine[Any, Any, None]]]


def fixture(
    fixture_function: Optional[Any] = None,
    *,
    scope: "Union[_ScopeName, Callable[[str, Config], _ScopeName]]" = "function",
    params: Optional[Iterable[object]] = None,
    autouse: bool = False,
    ids: Optional[Union[Sequence[Optional[object]], Callable[[Any], Optional[object]]]] = None,
) -> Any:
    def decorator(function: Any) -> Any:
        true_name = function.__name__[:-1]
        if inspect.iscoroutinefunction(function):
            return pytest_asyncio.fixture(
                function, name=true_name, scope=scope, params=params, autouse=autouse, ids=ids  # type: ignore
            )
        else:
            return pytest.fixture(function, name=true_name, scope=scope, params=params, autouse=autouse, ids=ids)

    if fixture_function is not None and callable(fixture_function):
        return decorator(fixture_function)

    return decorator


def use(*args: Callable[..., Any]) -> Any:
    true_names = [x.__name__[:-1] for x in args]
    return pytest.mark.usefixtures(*true_names)


def integration_test(function: _TestFunc) -> Any:
    return pytest.mark.integration_test(function)


def slow_integration_test(function: _TestFunc) -> Any:
    return pytest.mark.slow_integration_test(function)


class RequestFixture(Protocol[T]):
    """Yes, there is a class called FixtureRequest, but the types are quite bad for it"""

    node: Function
    param: T


@fixture
def temp_file_path_() -> Generator[Path, None, None]:
    with create_temp_file_path() as output:
        yield output


@fixture
def temp_path_() -> Generator[Path, None, None]:
    with temp_dir(TEMP_DIR) as output:
        yield output


def create_temp_file_path(cleanup: bool = True) -> ContextManager[Path]:
    @contextmanager
    def context() -> Generator[Path, None, None]:
        random_id = uuid4()
        output_path = os.path.join(TEMP_DIR, str(random_id))
        try:
            yield Path(output_path)
        finally:
            if cleanup and os.path.exists(output_path):
                if os.path.isfile(output_path):
                    os.remove(output_path)
                else:
                    shutil.rmtree(output_path)

    # noinspection PyTypeChecker
    return context()


def temp_dir(base_dir: str, is_uuid_concatenated: bool = False) -> ContextManager[Path]:
    @contextmanager
    def context() -> Generator[Path, None, None]:
        random_id = uuid4()
        if is_uuid_concatenated:
            output_path = Path(base_dir.rstrip("/") + "_" + str(random_id))
        else:
            output_path = Path(base_dir) / str(random_id)
        output_path.mkdir(parents=True, exist_ok=True)
        try:
            yield output_path
        finally:
            if output_path.exists():
                try:
                    shutil.rmtree(str(output_path))
                except OSError:
                    os.unlink(str(output_path))

    # noinspection PyTypeChecker
    return context()


@asynccontextmanager
async def async_temp_dir(base_dir: str, is_uuid_concatenated: bool = False) -> AsyncGenerator[Path, None]:
    random_id = uuid4()
    if is_uuid_concatenated:
        output_path = anyio.Path(base_dir.rstrip("/") + "_" + str(random_id))
    else:
        output_path = anyio.Path(base_dir) / str(random_id)
    await output_path.mkdir(parents=True, exist_ok=True)
    try:
        yield Path(output_path)
    finally:
        if await output_path.exists():
            try:
                await asyncio.to_thread(shutil.rmtree, str(output_path))
            except OSError:
                await output_path.unlink()
