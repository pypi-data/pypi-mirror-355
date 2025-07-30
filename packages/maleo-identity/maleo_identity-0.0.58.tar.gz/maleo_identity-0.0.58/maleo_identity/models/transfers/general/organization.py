from pydantic import BaseModel, Field
from typing import List, Optional
from maleo_foundation.models.schemas.general import BaseGeneralSchemas
from maleo_metadata.models.expanded_schemas.organization_type import MaleoMetadataOrganizationTypeExpandedSchemas
from maleo_identity.models.schemas.organization import MaleoIdentityOrganizationSchemas
from .organization_registration_code import OptionalOrganizationRegistrationCodeTransfers

class OrganizationTransfers(
    OptionalOrganizationRegistrationCodeTransfers,
    MaleoIdentityOrganizationSchemas.Name,
    MaleoIdentityOrganizationSchemas.Key,
    MaleoIdentityOrganizationSchemas.OptionalParentId,
    MaleoMetadataOrganizationTypeExpandedSchemas.OptionalExpandedOrganizationType,
    MaleoMetadataOrganizationTypeExpandedSchemas.SimpleOrganizationType,
    BaseGeneralSchemas.Status,
    BaseGeneralSchemas.Timestamps,
    BaseGeneralSchemas.Identifiers
):
    pass

class ExpandedOrganization(BaseModel):
    organization:OrganizationTransfers = Field(..., description="Organization's details")

class OptionalExpandedOrganization(BaseModel):
    organization:Optional[OrganizationTransfers] = Field(None, description="Organization's details")

class StructuredOrganizationTransfers(OrganizationTransfers):
    children:List["StructuredOrganizationTransfers"] = Field(..., description="Organization children")

# this is required for forward reference resolution
StructuredOrganizationTransfers.model_rebuild()