import hashlib
import inspect
import os
import platform
import uuid
from pathlib import Path
from types import FrameType
from typing import Final
from typing import List

import pathspec


def is_on_osx() -> bool:
    return platform.system().lower() == "darwin"


def is_testing() -> bool:
    return "PYTEST_CURRENT_TEST" in os.environ


def _get_filesystem_root() -> str:
    env_value = os.getenv("SCIENCE_FILESYSTEM_ROOT")
    if not env_value:
        if is_on_osx():
            return "/tmp/science"
        else:
            # When on the physical cluster (and possibly other core clusters), this path is mounted to a unique per-container file path.
            # Anything produced at runtime >10mb should likely go here, as well as anything you might want to dig up for later debugging.
            # The hosts clean up the paths from dead containers periodically, but large data processing jobs should still clean up after themselves.
            return "/mnt/private"
    return env_value


FILESYSTEM_ROOT: Final = _get_filesystem_root()
TEMP_DIR = os.path.join(FILESYSTEM_ROOT, "tmp")

if not is_on_osx():
    os.makedirs(TEMP_DIR, exist_ok=True)


def hash_string(string: str) -> str:
    return hashlib.md5(string.encode("utf-8")).hexdigest()


def get_current_function_name() -> str:
    frame = inspect.currentframe()
    if frame is None:
        return "no_frame"
    prev_frame = frame.f_back
    if prev_frame is None or not isinstance(prev_frame, FrameType):
        return "no_previous_frame"
    return prev_frame.f_code.co_name


def filter_excluded_files(files: List[Path], directory: Path, exclude_file_name: str = ".gitignore") -> List[Path]:
    """Remove files from the list that are matched by a .gitignore or similarly-specified exclude file such as
    excluded.txt"""

    # Underneath the root directory, find all the excluders.
    # They can occur in subfolders and if they do they apply only to that subfolder.
    excluders = {path for path in directory.rglob(exclude_file_name) if not path.is_symlink()}

    # Per excluder, make a pathspec.
    for excluder in excluders:
        with excluder.open("r") as exclude_file:
            exclude_spec = pathspec.GitIgnoreSpec.from_lines(exclude_file)

            # Now we have two cases - We keep the file if the excluder doesn't apply because it's in a different
            # folder, or if it applies but doesn't match
            prefix = os.path.dirname(excluder)
            files = [
                file
                for file in files
                if not (file.is_relative_to(prefix) and exclude_spec.match_file(file.relative_to(prefix)))
            ]

    return files


def generate_id() -> str:
    return uuid.uuid4().hex


def generate_id_from_existing_id(existing_id: str, seed: int) -> str:
    return hashlib.md5(f"{existing_id}-{seed}".encode()).hexdigest()


def truncate_string(s: str, max_length: int) -> str:
    if len(s) <= max_length:
        return s
    return s[: max_length - 3] + "..."
