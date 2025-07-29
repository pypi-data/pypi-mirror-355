import asyncio
import contextlib
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile
from tempfile import TemporaryDirectory
from typing import Generator

from imbue_core.common import TEMP_DIR
from imbue_core.git import LocalGitRepo
from imbue_core.git import get_git_repo_root
from imbue_core.testing_utils import fixture


@contextlib.contextmanager
def create_temp_file(contents: str, suffix: str, root_dir: Path) -> Generator[Path, None, None]:
    with NamedTemporaryFile(mode="w", suffix=suffix, dir=root_dir, delete=False) as temp_file:
        temp_file.write(contents)
        temp_file.flush()
        yield Path(temp_file.name)
        temp_file.close()
        Path(temp_file.name).unlink()


@contextlib.contextmanager
def create_temp_dir(root_dir: Path) -> Generator[Path, None, None]:
    with TemporaryDirectory(dir=root_dir) as temp_dir:
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)


async def _configure_temp_mock_repo(mock_repo: LocalGitRepo, temp_dir: Path) -> LocalGitRepo:
    temp_repo = await mock_repo.copy_repo(temp_dir)
    await temp_repo.configure_git(
        git_user_name="AGI (Automated Software Inspector)",
        git_user_email="the_true_AGI@running.pytest.com",
    )
    return temp_repo


@fixture
def mock_repo_() -> Generator[LocalGitRepo, None, None]:
    mock_repo_path = get_git_repo_root() / "imbue/imbue/test_data/mock_repo"
    mock_repo = LocalGitRepo(base_path=mock_repo_path)
    with create_temp_dir(root_dir=Path(TEMP_DIR)) as temp_dir:
        temp_repo = asyncio.run(_configure_temp_mock_repo(mock_repo, temp_dir))
        yield temp_repo
