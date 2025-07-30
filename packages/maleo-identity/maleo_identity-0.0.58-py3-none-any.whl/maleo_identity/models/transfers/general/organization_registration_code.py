from pydantic import BaseModel, Field
from typing import Optional
from maleo_foundation.models.schemas.general import BaseGeneralSchemas
from maleo_identity.models.schemas.general import MaleoIdentityGeneralSchemas
from maleo_identity.models.schemas.organization_registration_code import MaleoIdentityOrganizationRegistrationCodeSchemas

class OrganizationRegistrationCodeTransfers(
    MaleoIdentityOrganizationRegistrationCodeSchemas.CurrentUses,
    MaleoIdentityOrganizationRegistrationCodeSchemas.MaxUses,
    MaleoIdentityOrganizationRegistrationCodeSchemas.Code,
    MaleoIdentityGeneralSchemas.OrganizationId,
    BaseGeneralSchemas.Status,
    BaseGeneralSchemas.Timestamps,
    BaseGeneralSchemas.Identifiers
):
    pass

class OptionalOrganizationRegistrationCodeTransfers(BaseModel):
    registration_code:Optional[OrganizationRegistrationCodeTransfers] = Field(..., description="Registration codes")