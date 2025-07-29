"""Utilities to work with GitLab repositories."""

import os
from contextlib import contextmanager
from typing import Final
from typing import Generator
from typing import Optional

import gitlab
from gitlab.exceptions import GitlabGetError
from loguru import logger
from pydantic import ConfigDict
from pydantic_settings import BaseSettings

from imbue_core.serialization_types import Serializable

GITLAB_TOKEN_NAME: Final[str] = "GITLAB_TOKEN_FOR_USER_REPOS"


class GitlabTokenMissingError(Exception):
    """Raised when the expected environment variable is not set."""


class GitlabProjectReference(BaseSettings, Serializable):
    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True, extra="allow")
    subgroup: str
    project_name: str

    @property
    def path_with_namespace(self) -> str:
        return f"{self.subgroup}/{self.project_name}"


@contextmanager
def gitlab_client_from_environment() -> Generator[gitlab.Gitlab, None, None]:
    """Create a GitLab client from environment variables and manage it as a context.

    Yields:
        gitlab.Gitlab: The configured GitLab client

    Raises:
        GitlabTokenMissingError: If gitlab_token_name environment variable is not set
        GitlabAuthenticationError: If authentication fails
    """
    # Get GitLab token from environment -- this is not a setting, it's a secret.
    gitlab_token = os.getenv(GITLAB_TOKEN_NAME)
    if not gitlab_token:
        error_msg = f"{GITLAB_TOKEN_NAME} environment variable is not set"
        raise GitlabTokenMissingError(error_msg)

    # Get GitLab URL from environment or use default
    gitlab_url = os.getenv("GITLAB_URL", "https://gitlab.com")
    logger.debug(f"Using GitLab URL: {gitlab_url}")

    # Initialize GitLab client
    with gitlab.Gitlab(gitlab_url, private_token=gitlab_token) as gl:
        logger.debug("GitLab client initialized successfully")
        yield gl


def get_gitlab_remote_url(gitlab_token: str, gitlab_project_reference: GitlabProjectReference) -> str:
    """WARNING: This embeds the token in the URL!  Only use this on the server-side backend."""
    # TODO:(CFTY-1244): Perhaps there is a better way to manage this secret?
    return f"https://oauth2:{gitlab_token}@gitlab.com/{gitlab_project_reference.path_with_namespace}.git"


def ensure_gitlab_project_exists(
    gl: gitlab.Gitlab,
    project_reference: GitlabProjectReference,
    visibility: str = "private",
    description: Optional[str] = None,
) -> None:
    path_with_namespace = project_reference.path_with_namespace
    logger.debug(f"Creating GitLab repository: {path_with_namespace=}")

    try:
        found_project = gl.projects.get(path_with_namespace)
        logger.debug(
            f"Repository already exists: {path_with_namespace} -- we will not create it and ignore the description passed in."
        )
        assert (
            found_project.path_with_namespace == path_with_namespace
        ), f"Repository path mismatch: {found_project.path_with_namespace} != {path_with_namespace}"
        return
    except GitlabGetError:
        logger.info(f"Repository {path_with_namespace} does not exist, so we will proceed with creating it.")

    group = gl.groups.get(project_reference.subgroup)
    logger.debug(f"Found subgroup: {project_reference.subgroup}")

    # Create the repository
    project_data = {
        "name": project_reference.project_name,
        "path": project_reference.project_name,
        "namespace_id": group.id,
        "visibility": visibility,
        "initialize_with_readme": False,
        "description": description or f"Repository for {project_reference.project_name}",
    }
    logger.debug(f"Creating repository with data: {project_data}")

    created_project = gl.projects.create(project_data)
    logger.success(f"Successfully created repository: {created_project.path_with_namespace}")
    assert (
        created_project.path_with_namespace == path_with_namespace
    ), f"Repository path mismatch: {created_project.path_with_namespace} != {path_with_namespace}"


def delete_gitlab_project(
    gl: gitlab.Gitlab,
    project_reference: GitlabProjectReference,
) -> None:
    """Delete a GitLab repository.

    This operation requires "Owner" access to the subgroup.

    Args:
        gl: GitLab client instance
        project_name: Name of the repository to delete
        subgroup: Subgroup path where the repository is located

    Raises:
        GitlabGetError: If repository is not found
        GitlabDeleteError: If repository deletion fails
    """
    path_with_namespace = project_reference.path_with_namespace
    logger.info(f"Deleting GitLab repository: {path_with_namespace}")

    project = gl.projects.get(path_with_namespace)
    logger.debug(f"Found repository: {path_with_namespace}")

    # Delete the project
    project.delete()
    logger.success(f"Successfully deleted repository: {path_with_namespace}")


def is_project_already_existing(gl: gitlab.Gitlab, project_reference: GitlabProjectReference) -> bool:
    try:
        project = gl.projects.get(project_reference.path_with_namespace)
        return not bool(project.marked_for_deletion_at)
    except GitlabGetError:
        return False
    return True
