from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

import pytest

from imbue_core.common import TEMP_DIR
from imbue_core.computing_environment.computing_environment import get_untracked_files
from imbue_core.computing_environment.computing_environment import git_add
from imbue_core.computing_environment.computing_environment import is_repo_dirty
from imbue_core.computing_environment.computing_environment import make_commit
from imbue_core.conftest import mock_repo_
from imbue_core.git import LocalGitRepo
from imbue_core.git import WritableLocalGitRepo
from imbue_core.git import copy_files_from_one_repo_to_another
from imbue_core.git_snapshot import checkout_repo_from_snapshot
from imbue_core.git_snapshot import get_local_repo_snapshot
from imbue_core.testing_utils import async_temp_dir
from imbue_core.testing_utils import use


@asynccontextmanager
async def temp_writable_local_git_repo(existing_repo: LocalGitRepo) -> AsyncIterator[WritableLocalGitRepo]:
    """Context manager to create a writable version of an existing git repo.

    Under the hood this will create a copy of the existing repo in a temporary directory in the fastest way possible.
    """
    async with async_temp_dir(TEMP_DIR) as writable_repo_path:
        repo_snapshot = await get_local_repo_snapshot(existing_repo)

        cloned_repo = await checkout_repo_from_snapshot(
            repo_snapshot=repo_snapshot,
            destination_path=writable_repo_path,
        )

        # copy any untracked files into new writable repo
        if repo_snapshot.git_untracked_files is not None:
            await copy_files_from_one_repo_to_another(
                src_repo_path=existing_repo.base_path,
                dst_repo_path=writable_repo_path,
                relative_file_paths=repo_snapshot.git_untracked_files,
            )

        yield await WritableLocalGitRepo.build_from_repo(cloned_repo)


@pytest.mark.asyncio
@use(mock_repo_)
async def test_temp_writable_local_git_repo_clean(mock_repo: LocalGitRepo) -> None:
    await mock_repo.assert_clean()

    async with temp_writable_local_git_repo(mock_repo) as writable_repo:
        assert mock_repo.base_path != writable_repo.base_path
        main_repo_hash = await mock_repo.head_hash()
        writable_repo_hash = await writable_repo.head_hash()
        assert main_repo_hash == writable_repo_hash
        assert writable_repo_hash == writable_repo.initial_git_hash

        main_file_relative_path = Path("mock_repo/main.py")
        main_module_contents = await writable_repo.safely_read_file_from_repo(main_file_relative_path)

        new_code = "\n".join(
            [
                "",
                "",
                "def a_new_function(arg_1: int) -> str:",
                "    return str(arg_1)",
                "",
            ]
        )
        main_module_contents += new_code

        await writable_repo.apply_change_to_file(main_file_relative_path, main_module_contents)
        assert await is_repo_dirty(writable_repo)
        await mock_repo.assert_clean()
        new_writable_repo_hash = await make_commit(writable_repo, "making change")
        new_main_repo_hash = await mock_repo.head_hash()
        assert new_main_repo_hash == main_repo_hash
        assert new_writable_repo_hash != writable_repo_hash


@pytest.mark.asyncio
@use(mock_repo_)
async def test_temp_writable_local_git_repo_unstaged_uncommited(mock_repo: LocalGitRepo) -> None:
    # test when there is unstaged uncommited changes in main repo
    await mock_repo.assert_clean()

    mock_main_file_path = mock_repo.base_path / Path("mock_repo/main.py")
    mock_main_module_contents = await mock_repo.safely_read_file_from_repo(mock_main_file_path)

    new_code = "\n".join(
        [
            "",
            "",
            "def a_new_function(arg_1: int) -> str:",
            "    return str(arg_1)",
            "",
        ]
    )
    mock_main_module_contents += new_code
    mock_main_file_path.write_text(mock_main_module_contents)
    assert await is_repo_dirty(mock_repo)

    async with temp_writable_local_git_repo(mock_repo) as writable_repo:
        assert mock_repo.base_path != writable_repo.base_path
        await writable_repo.assert_clean()
        main_repo_hash = await mock_repo.head_hash()
        writable_repo_hash = await writable_repo.head_hash()
        # expect these to be different, since writable repo creates a new commit to manage uncommited changes
        assert main_repo_hash != writable_repo_hash
        assert main_repo_hash == writable_repo.initial_git_hash
        assert writable_repo_hash == writable_repo.stash_git_hash

        writable_main_relative_path = Path("mock_repo/main.py")
        writable_main_module_contents = await writable_repo.safely_read_file_from_repo(writable_main_relative_path)
        assert writable_main_module_contents == mock_main_module_contents


@pytest.mark.asyncio
@use(mock_repo_)
async def test_temp_writable_local_git_repo_staged_uncommited(mock_repo: LocalGitRepo) -> None:
    # test when there is staged uncommited changes in main repo
    await mock_repo.assert_clean()

    mock_main_file_path = mock_repo.base_path / Path("mock_repo/main.py")
    mock_main_module_contents = await mock_repo.safely_read_file_from_repo(mock_main_file_path)
    new_code = "\n".join(
        [
            "",
            "",
            "def a_new_function(arg_1: int) -> str:",
            "    return str(arg_1)",
            "",
        ]
    )
    mock_main_module_contents += new_code
    mock_main_file_path.write_text(mock_main_module_contents)
    assert await is_repo_dirty(mock_repo)

    before_hash = await mock_repo.head_hash()
    # stage change
    await git_add(mock_repo, str(mock_main_file_path))
    after_hash = await mock_repo.head_hash()
    assert before_hash == after_hash
    assert await is_repo_dirty(mock_repo)

    async with temp_writable_local_git_repo(mock_repo) as writable_repo:
        assert mock_repo.base_path != writable_repo.base_path
        main_repo_hash = await mock_repo.head_hash()
        assert main_repo_hash == after_hash

        await writable_repo.assert_clean()
        writable_repo_hash = await writable_repo.head_hash()
        # expect these to be different, since writable repo creates a new commit to manage uncommited changes
        assert main_repo_hash != writable_repo_hash
        assert main_repo_hash == writable_repo.initial_git_hash
        assert writable_repo_hash == writable_repo.stash_git_hash

        writable_main_relative_path = Path("mock_repo/main.py")
        writable_main_module_contents = await writable_repo.safely_read_file_from_repo(writable_main_relative_path)
        assert writable_main_module_contents == mock_main_module_contents


@pytest.mark.asyncio
@use(mock_repo_)
async def test_temp_writable_local_git_repo_untracked(mock_repo: LocalGitRepo) -> None:
    # test when there is untracked changes in main repo
    await mock_repo.assert_clean()

    new_file_path = mock_repo.base_path / "mock_repo" / "new_file.py"
    new_file_content = "\n".join(
        [
            "",
            "",
            "def hello_world(arg_1: int) -> str:",
            "    return str(arg_1)",
            "",
        ]
    )
    new_file_path.write_text(new_file_content)
    assert await is_repo_dirty(mock_repo)

    async with temp_writable_local_git_repo(mock_repo) as writable_repo:
        assert mock_repo.base_path != writable_repo.base_path
        await writable_repo.assert_clean()
        main_repo_hash = await mock_repo.head_hash()
        writable_repo_hash = await writable_repo.head_hash()
        # expect these to be different, since writable repo creates a new commit to manage uncommited changes
        assert main_repo_hash != writable_repo_hash
        assert main_repo_hash == writable_repo.initial_git_hash
        assert writable_repo_hash == writable_repo.stash_git_hash

        writable_new_relative_path = Path("mock_repo/new_file.py")
        writable_new_file_contents = await writable_repo.safely_read_file_from_repo(writable_new_relative_path)
        assert writable_new_file_contents == new_file_content


@pytest.mark.asyncio
@use(mock_repo_)
async def test_identify_untracked_files(mock_repo: LocalGitRepo) -> None:
    await mock_repo.assert_clean()

    new_file_relative_path = Path("new_file.py")
    new_file_path = mock_repo.base_path / new_file_relative_path
    new_file_content = "\n".join(
        [
            "",
            "",
            "def hello_world(arg_1: int) -> str:",
            "    return str(arg_1)",
            "",
        ]
    )
    new_file_path.write_text(new_file_content)
    untracked_files = await get_untracked_files(mock_repo)
    assert str(new_file_relative_path) in untracked_files
