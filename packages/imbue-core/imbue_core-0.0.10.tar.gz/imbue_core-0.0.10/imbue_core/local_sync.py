"""
Data types and other utils shared by the local sync server (backend) and client (frontend).

"""
import datetime
from enum import StrEnum
from typing import Any
from typing import Optional
from typing import Tuple
from typing import Union

import attr

from imbue_core.common import generate_id
from imbue_core.repo_state import CleanRepoOperation
from imbue_core.repo_state import ConflictedRepoOperation
from imbue_core.serialization_types import Serializable
from imbue_core.time_utils import get_current_time


def _convert_to_repo_operation(v: Any) -> Union[CleanRepoOperation, ConflictedRepoOperation]:
    """Convert a dict to a repo operation."""
    if isinstance(v, (CleanRepoOperation, ConflictedRepoOperation)):
        return v
    if not isinstance(v, dict):
        raise ValueError("repo_operation must be a dict")
    for operation_class_type in (CleanRepoOperation, ConflictedRepoOperation):
        try:
            return operation_class_type(**v)
        except Exception:
            pass
    raise ValueError("repo_operation must be a CleanRepoOperation or ConflictedRepoOperation")


def _convert_to_utc_datetime(v: Any) -> datetime.datetime:
    if isinstance(v, str):
        return datetime.datetime.fromisoformat(v)
    if isinstance(v, dict):
        if "time" in v:
            # Got something like {"time": 1741999454.609277, "tzaware": true}
            return datetime.datetime.fromtimestamp(v["time"], datetime.timezone.utc)
        raise ValueError("created_at must be a string or a dict with a 'time' key")
    return v


@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class Project(Serializable):
    backend_repo_url: str
    name: str
    id: str


@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class LocalSyncClientInfo(Serializable):
    """Information about the client sent to the backend."""

    ip_address: str


@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class LocalSyncMessage(Serializable):
    """Base class for all local sync messages."""

    created_at: datetime.datetime = attr.ib(factory=get_current_time, converter=_convert_to_utc_datetime)
    message_id: str = attr.ib(factory=generate_id)


@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class LocalSyncClientMessage(LocalSyncMessage):
    """Message from the client to send to the backend."""

    client_id: str
    client_info: LocalSyncClientInfo


@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class CreateProjectMessage(LocalSyncClientMessage):
    project_name: str


@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class UploadLogsMessage(LocalSyncClientMessage):
    log_entries: Tuple[str, ...]


@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class SyncBranchMessage(LocalSyncClientMessage):
    project_id: str
    branch_name: str
    target_branch_name: str
    commit_hash: str
    repo_operation: Union[CleanRepoOperation, ConflictedRepoOperation] = attr.ib(converter=_convert_to_repo_operation)
    user_choice: Optional[str] = None


@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class NewLocalRepoStateMessage(LocalSyncClientMessage):
    """Serialized message from the backend to send to the client."""

    project_id: str
    branch_name: str
    version: int
    commit_hash: str
    repo_operation: Union[CleanRepoOperation, ConflictedRepoOperation] = attr.ib(converter=_convert_to_repo_operation)


@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class NewSecretsMessage(LocalSyncClientMessage):
    encrypted_secrets_file_contents: bytes


@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class NewSecretKeyMessage(LocalSyncClientMessage):
    key: bytes


@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class LocalSyncServerMessage(LocalSyncMessage):
    """Message from the backend to send to the client."""


@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class NewProjectMessage(LocalSyncServerMessage):
    project_name: str
    project_actor_id: str


@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class GetProjectMessage(LocalSyncServerMessage):
    project: Optional[Project]


@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class SyncBranchResponseMessage(LocalSyncServerMessage):
    pass


@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class SyncBranchSuccessful(SyncBranchResponseMessage):
    pass


@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class SyncBranchFailed(SyncBranchResponseMessage):
    remote_state_description: str


@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class FailedToSaveMessage(LocalSyncServerMessage):
    version: int


@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class AppliedSaveMessage(LocalSyncServerMessage):
    version: int
    is_containing_new_changes: bool


@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class SecretsUpdatedMessage(LocalSyncServerMessage):
    pass


class SecretsUpdateFailureReason(StrEnum):
    NO_SECRET_KEY = "NO_SECRET_KEY"
    INVALID_SECRET_KEY = "INVALID_SECRET_KEY"
    UNKNOWN = "UNKNOWN"


@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class SecretsFailedToUpdateMessage(LocalSyncServerMessage):
    reason: SecretsUpdateFailureReason


@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class NewRemoteRepoStateMessage(LocalSyncServerMessage):
    branch_name: str
    version: int
    commit_hash: str
    repo_operation: Union[CleanRepoOperation, ConflictedRepoOperation] = attr.ib(converter=_convert_to_repo_operation)


@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class SyncedMessage(NewRemoteRepoStateMessage):
    pass
