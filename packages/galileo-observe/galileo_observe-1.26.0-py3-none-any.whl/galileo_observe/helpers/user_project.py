from pydantic import UUID4

from galileo_core.helpers.user_project import share_project_with_user as core_share_project_with_user
from galileo_core.helpers.user_project import unshare_project_with_user as core_unshare_project_with_user
from galileo_core.schemas.core.collaboration_role import CollaboratorRole
from galileo_core.schemas.core.user_project import UserProjectCollaboratorResponse
from galileo_observe.schema.config import ObserveConfig


def share_project_with_user(
    project_id: UUID4, user_id: UUID4, role: CollaboratorRole = CollaboratorRole.viewer
) -> UserProjectCollaboratorResponse:
    config = ObserveConfig.get()
    return core_share_project_with_user(project_id=project_id, user_id=user_id, role=role, config=config)


def unshare_project_with_user(project_id: UUID4, user_id: UUID4) -> None:
    config = ObserveConfig.get()
    return core_unshare_project_with_user(project_id=project_id, user_id=user_id, config=config)
