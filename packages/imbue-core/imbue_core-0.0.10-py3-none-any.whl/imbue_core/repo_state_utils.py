from pathlib import Path
from typing import Dict
from typing import Optional
from typing import cast

from imbue_core.computing_environment.computing_environment import ComputingEnvironment
from imbue_core.computing_environment.computing_environment import get_git_folder_paths
from imbue_core.computing_environment.computing_environment import get_head_hash
from imbue_core.computing_environment.computing_environment import get_modified_file_contents_by_path
from imbue_core.computing_environment.computing_environment import get_staged_unstaged_and_combined_diffs
from imbue_core.computing_environment.computing_environment import get_unmerged_and_staged_blob_contents_by_hash
from imbue_core.computing_environment.computing_environment import is_repo_conflicted
from imbue_core.frozen_utils import FrozenDict
from imbue_core.repo_state import CleanRepoOperation
from imbue_core.repo_state import ConflictType
from imbue_core.repo_state import ConflictedRepoOperation
from imbue_core.repo_state import GIT_FILE_PATH_NAMES_BY_CONFLICT_TYPE
from imbue_core.repo_state import RepoState


async def get_special_git_file_contents_by_path_for_conflict_type(
    computing_environment: ComputingEnvironment, conflict_type: ConflictType
) -> Dict[str, bytes]:
    filenames = GIT_FILE_PATH_NAMES_BY_CONFLICT_TYPE[conflict_type]
    git_file_contents_by_path: Dict[str, bytes] = {}
    for filename in filenames:
        content = await computing_environment.read_file(f".git/{filename}", mode="rb")
        assert isinstance(content, bytes), f"Expected bytes, got {type(content)}"
        git_file_contents_by_path[filename] = content
    return git_file_contents_by_path


async def get_conflict_type_from_computing_environment(
    computing_environment: ComputingEnvironment,
) -> Optional[ConflictType]:
    if await is_repo_conflicted(computing_environment):
        files = await get_git_folder_paths(computing_environment)
        if "MERGE_HEAD" in files:
            return ConflictType.MERGE
        # elif "REBASE_HEAD" in files:
        #     return ConflictType.REBASE
        # elif "CHERRY_PICK_HEAD" in files:
        #     return ConflictType.CHERRY_PICK
        else:
            return ConflictType.APPLY
    else:
        return None


async def maybe_get_conflict_operation_from_computing_environment(
    computing_environment: ComputingEnvironment,
) -> ConflictedRepoOperation | None:
    conflict_type = await get_conflict_type_from_computing_environment(computing_environment)
    if conflict_type is None:
        return None
    return await get_conflict_operation_from_computing_environment(computing_environment, conflict_type)


async def get_conflict_operation_from_computing_environment(
    computing_environment: ComputingEnvironment, conflict_type: ConflictType
) -> ConflictedRepoOperation:
    index_content = await computing_environment.read_file(Path(".git/index"), mode="rb")
    index_content = cast(bytes, index_content)
    blob_content_by_hash = await get_unmerged_and_staged_blob_contents_by_hash(computing_environment)
    modified_file_contents_by_path = await get_modified_file_contents_by_path(computing_environment)
    special_git_file_contents_by_path = await get_special_git_file_contents_by_path_for_conflict_type(
        computing_environment, conflict_type
    )
    return ConflictedRepoOperation(
        blob_content_by_hash=FrozenDict(blob_content_by_hash),
        index_content=index_content,
        modified_file_contents_by_path=FrozenDict(modified_file_contents_by_path),
        conflict_type=conflict_type,
        special_git_file_contents_by_path=FrozenDict(special_git_file_contents_by_path),
    )


async def get_clean_repo_operation_from_computing_environment(
    computing_environment: ComputingEnvironment,
) -> CleanRepoOperation:
    staged_diff, unstaged_diff, combined_diff = await get_staged_unstaged_and_combined_diffs(computing_environment)
    return CleanRepoOperation(
        combined_diff=combined_diff,
        staged_diff=staged_diff,
        unstaged_diff=unstaged_diff,
    )


async def get_conflicted_repo_state_from_computing_environment(
    computing_environment: ComputingEnvironment,
) -> RepoState:
    conflict_type = await get_conflict_type_from_computing_environment(computing_environment)
    assert conflict_type is not None
    conflict_operation = await get_conflict_operation_from_computing_environment(computing_environment, conflict_type)
    return RepoState(
        git_hash=await get_head_hash(computing_environment),
        repo_operation=conflict_operation,
    )
