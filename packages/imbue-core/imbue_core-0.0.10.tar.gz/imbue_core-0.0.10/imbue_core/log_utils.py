from __future__ import annotations

import asyncio
import typing
from pathlib import Path
from typing import Any
from typing import Callable
from typing import Dict
from typing import Union

import loguru

if typing.TYPE_CHECKING:
    loguru_record = loguru.Record
else:
    loguru_record = Dict[str, Any]
FilterDict = Dict[Union[str, None], Union[str, int, bool]]
FilterFunction = Callable[[loguru_record], bool]
LOCATION_WIDTH = 60
TRACE = "TRACE"

TASK_ID_MESSAGE_WIDTH = 12


def fix_full_location(record: "loguru.Record") -> str:
    """
    One goal of this function is to format the location in an IDE-friendly way,
    so that control-clicking on the logged location opens the correct file
    and puts the cursor at the correct line.

    `record` looks like this:
    ```
    {
        "elapsed": datetime.timedelta(seconds=5, microseconds=152312),
        "exception": None,
        "extra": {
            "machine": "32de5bcafaa8",
            "user": "user",
            "agent_type": None,
            "agent_id": None,
            "parent_id": None,
            "async_task_id": None,
            "formatted_task_id": "",
            "formatted_agent_id": "",
            "sandbox_id": None,
            "formatted_sandbox_id": "",
        },
        "file": (
            name="error_dump_utils.py",
            path="/thad/dropbox/Thad Hughes/src/generally_intelligent/computronium/computronium/common/error_dump_utils.py",
        ),
        "function": "write_exception",
        "level": (name="INFO", no=20, icon="ℹ️"),
        "line": 214,
        "message": "Full traceback for  is available at http://node-004.snake-blues.ts.net:7777/exceptions/thad__notebook_2025_01_28_legolas/1000__2025_01_28_17_47_19_170102__P000_W0000/C0000__user_100.110.58.95_5045/2025_03_06_09_59_10_188008_KeyboardInterrupt_traceback.txt",
        "module": "error_dump_utils",
        "name": "computronium.common.error_dump_utils",
        "process": (id=3099015, name="MainProcess"),
        "thread": (id=140434013706048, name="MainThread"),
        "time": datetime(
            2025, 3, 6, 9, 59, 10, 920101, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=57600), "PST")
        ),
    }
    ```
    """
    log_path = Path(record["file"].path)
    if log_path.is_relative_to(Path.cwd()):
        log_path = log_path.relative_to(Path.cwd())
    location = record["extra"].get("full_location", f'{str(log_path)}:{record["line"]}:{record["function"]}')
    while len(location) > LOCATION_WIDTH and "/" in location:
        location = location[location.find("/") + 1 :]
    return location[-LOCATION_WIDTH:].rjust(LOCATION_WIDTH)


def format_task_id(async_task_id: str) -> str:
    return async_task_id[:TASK_ID_MESSAGE_WIDTH].rjust(TASK_ID_MESSAGE_WIDTH)


def patch_log_context_in_place(record: "loguru.Record", format_task_id: Callable[[str], str] = format_task_id) -> None:
    record["extra"]["full_location"] = fix_full_location(record)

    async_task_id = None
    try:
        # get the task id
        current_task = asyncio.current_task()
        if current_task is not None:
            async_task_id = current_task.get_name()
    except RuntimeError:
        # we're not in an asyncio event loop
        pass

    if async_task_id:
        formatted_task_id = format_task_id(async_task_id)
        record["extra"]["formatted_task_id"] = f" [{formatted_task_id}]"
        record["extra"]["async_task_id"] = async_task_id
