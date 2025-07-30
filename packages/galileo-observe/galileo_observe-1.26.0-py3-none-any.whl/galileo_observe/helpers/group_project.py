from pydantic import UUID4

from galileo_core.helpers.group_project import share_project_with_group as core_share_project_with_group
from galileo_core.helpers.group_project import unshare_project_with_group as core_unshare_project_with_group
from galileo_core.schemas.core.collaboration_role import CollaboratorRole
from galileo_core.schemas.core.group_project import GroupProjectCollaboratorResponse
from galileo_observe.schema.config import ObserveConfig


def share_project_with_group(
    project_id: UUID4, group_id: UUID4, role: CollaboratorRole = CollaboratorRole.viewer
) -> GroupProjectCollaboratorResponse:
    config = ObserveConfig.get()
    return core_share_project_with_group(project_id=project_id, group_id=group_id, role=role, config=config)


def unshare_project_with_group(project_id: UUID4, group_id: UUID4) -> None:
    config = ObserveConfig.get()
    return core_unshare_project_with_group(project_id=project_id, group_id=group_id, config=config)
