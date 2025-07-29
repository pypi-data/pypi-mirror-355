import asyncio
import functools
import hashlib
from pathlib import Path
from typing import Mapping
from typing import Tuple

import anyio
import attr

from imbue_core.cattrs_serialization import serialize_to_json
from imbue_core.computing_environment.computing_environment import apply_patch_via_git
from imbue_core.computing_environment.computing_environment import make_commit
from imbue_core.frozen_utils import empty_mapping
from imbue_core.git import LocalGitRepo
from imbue_core.secrets_utils import get_secret


@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class GitRepo:
    git_user_name: str
    git_user_email: str


@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class GitRepoSnapshot(GitRepo):
    git_hash: str
    git_branch: str
    git_diff: str | None

    @functools.cached_property
    def reference_hash(self) -> str:
        hash_fn = hashlib.md5()
        hash_fn.update(serialize_to_json(self).encode("UTF-8"))
        return hash_fn.hexdigest()


@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class RemoteGitRepoSnapshot(GitRepoSnapshot):
    git_repo_url: str


@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class LocalGitRepoSnapshot(GitRepoSnapshot):
    git_repo_path: str
    # the relative paths of any untracked files in the repo
    git_untracked_files: Tuple[str, ...] | None


@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class GitCommitSnapshot:
    contents_by_path: Mapping[str, str]
    commit_message: str
    # ex: "2023-05-15T14:30:00"
    # used for GIT_AUTHOR_DATE and GIT_COMMITTER_DATE
    commit_time: str


@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class FullLocalGitRepo(GitRepo):
    main_history: Tuple[GitCommitSnapshot, ...]
    # the relative paths of any currently untracked files in the repo, and their content
    untracked_file_content_by_path: Mapping[str, str] = attr.ib(factory=empty_mapping)
    git_branch: str = "main"
    git_diff: str | None = None


async def create_repo_from_snapshot(
    full_repo: FullLocalGitRepo,
    destination_path: Path,
) -> LocalGitRepo:
    """Creates an entire repo history locally from scratch. Much faster and more reliable than checking from remote."""
    anyio_path = anyio.Path(destination_path)
    if not await anyio_path.exists():
        destination_path.mkdir(parents=True)
    assert (
        await anyio_path.is_dir()
    ), f"Destination for repo checkout must be a directory. {destination_path} is not a directory."

    async for _ in anyio_path.iterdir():
        raise Exception(f"Destination for repo creation must be an empty directory. {destination_path} is not empty.")

    # create the empty repo
    new_repo = LocalGitRepo(destination_path)
    await new_repo.run_git(("init",))
    await new_repo.run_git(("checkout", "-b", "main"))
    if full_repo.git_branch != "main":
        await new_repo.run_git(("branch", "-m", "main", full_repo.git_branch))
    await new_repo.run_git(("config", "user.name", f"'{full_repo.git_user_name}'"))
    await new_repo.run_git(("config", "user.email", f"'{full_repo.git_user_email}'"))

    # put the history in
    for commit in full_repo.main_history:
        await _write_files_in_parallel(new_repo, commit.contents_by_path)
        await make_commit(new_repo, commit.commit_message, commit_time=commit.commit_time)

    if full_repo.git_diff:
        # apply any diffs from between git_hash and repo snapshot state of repo being checked out
        await apply_patch_via_git(new_repo, full_repo.git_diff, is_error_logged=True)

    if full_repo.untracked_file_content_by_path:
        # make sure the untracked file contents are there
        await _write_files_in_parallel(new_repo, full_repo.untracked_file_content_by_path)

    return new_repo


async def checkout_repo_from_snapshot(
    repo_snapshot: LocalGitRepoSnapshot | RemoteGitRepoSnapshot,
    destination_path: Path,
) -> LocalGitRepo:
    """Checks out an existing repo into a directory in the fastest way possible.

    Uses a snapshot of the existing repo to checkout a specific commit and branch, and apply any uncommited changes.
    Will checkout from a remote or local repo depending on the type of snapshot.

    Note, checking out from a remote repo requires that the necessary git permissions, etc are configured.

    See here: https://stackoverflow.com/questions/31278902/how-to-shallow-clone-a-specific-commit-with-depth-1
    """
    anyio_path = anyio.Path(destination_path)
    assert (
        await anyio_path.is_dir()
    ), f"Destination for repo checkout must be a directory. {destination_path} is not a directory."
    if not await anyio_path.exists():
        destination_path.mkdir(parents=True)
    async for _ in anyio_path.iterdir():
        raise Exception(f"Destination for repo checkout must be an empty directory. {destination_path} is not empty.")

    remote_address: str | None = None
    if isinstance(repo_snapshot, RemoteGitRepoSnapshot):
        token = get_secret("GIT_TOKEN")
        assert token is not None, "Must set GIT_TOKEN environment variable to clone git repos"
        env = {"GIT_TOKEN": token}

        repo_url = repo_snapshot.git_repo_url
        assert repo_url.startswith("https://"), "Only https git urls are supported"
        if repo_url.startswith("https://oauth2"):
            raise Exception("Wait no, that doesn't make sense--that will hardcode the oauth token into the DB")
        remote_address = repo_url.replace("https://", f"https://oauth2:{token}@", 1)
    elif isinstance(repo_snapshot, LocalGitRepoSnapshot):
        remote_address = repo_snapshot.git_repo_path
        env = None
    assert remote_address is not None, "Remote address not found"

    new_repo = LocalGitRepo(destination_path)
    await new_repo.run_git(("init",))
    await new_repo.run_git(("config", "user.name", f"'{repo_snapshot.git_user_name}'"))
    await new_repo.run_git(("config", "user.email", f"'{repo_snapshot.git_user_email}'"))
    await new_repo.run_git(("remote", "add", "origin", str(remote_address)))
    await new_repo.run_command(("git", "fetch", "--depth", "1", "origin", repo_snapshot.git_hash), secrets=env)
    await new_repo.run_git(("checkout", "FETCH_HEAD"))

    if repo_snapshot.git_diff:
        # apply any diffs from between git_hash and repo snapshot state of repo being checked out
        await apply_patch_via_git(new_repo, repo_snapshot.git_diff, is_error_logged=True)

    return new_repo


async def _write_files_in_parallel(repo: LocalGitRepo, content: Mapping[str, str]) -> None:
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(repo.write_file(file_path, content)) for file_path, content in content.items()]
        await asyncio.gather(*tasks)


async def get_snapshot_info(repo: LocalGitRepo) -> GitRepoSnapshot:
    """Get general snapshot of the current state of the git repo."""
    async with asyncio.TaskGroup() as tg:
        git_branch_task = tg.create_task(repo.run_git(("rev-parse", "--abbrev-ref", "HEAD")))
        git_hash_task = tg.create_task(repo.run_git(("rev-parse", "HEAD")))
        git_unstaged_diff_task = tg.create_task(repo.run_git(("diff", "--full-index", "--binary"), is_stripped=False))
        git_staged_diff_task = tg.create_task(
            repo.run_git(("diff", "--full-index", "--binary", "--staged"), is_stripped=False)
        )
        git_user_name_task = tg.create_task(repo.run_git(("config", "user.name")))
        git_user_email_task = tg.create_task(repo.run_git(("config", "user.email")))
        await asyncio.gather(
            *[
                git_branch_task,
                git_hash_task,
                git_unstaged_diff_task,
                git_staged_diff_task,
                git_user_name_task,
                git_user_email_task,
            ]
        )
        git_branch = git_branch_task.result()
        current_git_hash = git_hash_task.result()
        # get the current diff (changes the user has made)
        git_staged_diff = git_staged_diff_task.result()
        git_diff = git_staged_diff
        git_unstaged_diff = git_unstaged_diff_task.result()
        if git_unstaged_diff.strip() != "":
            git_diff += git_unstaged_diff

        git_user_email = git_user_email_task.result()
        git_user_name = git_user_name_task.result()

        return GitRepoSnapshot(
            git_hash=current_git_hash,
            git_diff=git_diff,
            git_branch=git_branch,
            git_user_name=git_user_name,
            git_user_email=git_user_email,
        )


async def get_local_repo_snapshot(repo: LocalGitRepo) -> LocalGitRepoSnapshot:
    """Get a snapshot of the current state of the git repo locally."""
    # run a bunch of commands in parallel to generate the necessary information
    async with asyncio.TaskGroup() as tg:
        general_snapshot_task = tg.create_task(get_snapshot_info(repo))
        git_untracked_files_task = tg.create_task(repo.run_git(("ls-files", "--others", "--exclude-standard")))
        await asyncio.gather(
            *[
                general_snapshot_task,
                git_untracked_files_task,
            ]
        )
        # relative path to any untracked files in repo (that are not in excluded files, etc)
        untracked_files_result = git_untracked_files_task.result()
        if untracked_files_result not in (None, ""):
            untracked_files = tuple(untracked_files_result.splitlines())
        else:
            untracked_files = None

        general_snapshot = general_snapshot_task.result()
    return LocalGitRepoSnapshot(
        git_repo_path=str(repo.base_path),
        git_hash=general_snapshot.git_hash,
        git_diff=general_snapshot.git_diff,
        git_branch=general_snapshot.git_branch,
        git_untracked_files=untracked_files,
        git_user_email=general_snapshot.git_user_email,
        git_user_name=general_snapshot.git_user_name,
    )


async def get_repo_snapshot_for_cwd() -> GitRepoSnapshot:
    return await get_local_repo_snapshot(LocalGitRepo.build_from_cwd())
