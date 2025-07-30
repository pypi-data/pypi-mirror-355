from pydantic import BaseModel, Field
from typing import List
from maleo_foundation.models.schemas.general import BaseGeneralSchemas
from maleo_metadata.models.expanded_schemas.system_role import MaleoMetadataSystemRoleExpandedSchemas
from maleo_identity.models.schemas.general import MaleoIdentityGeneralSchemas

class UserSystemRoleTransfers(
    MaleoMetadataSystemRoleExpandedSchemas.OptionalExpandedSystemRole,
    MaleoMetadataSystemRoleExpandedSchemas.SimpleSystemRole,
    MaleoIdentityGeneralSchemas.UserId,
    BaseGeneralSchemas.Status,
    BaseGeneralSchemas.Timestamps,
    BaseGeneralSchemas.Identifiers
): pass

class ListOfExpandedUserSystemRole(BaseModel):
    system_roles:List[UserSystemRoleTransfers] = Field([], description="List of user's system roles")