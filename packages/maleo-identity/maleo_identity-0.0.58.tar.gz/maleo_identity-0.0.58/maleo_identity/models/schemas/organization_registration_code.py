from pydantic import BaseModel, Field
from uuid import UUID
from maleo_foundation.models.schemas.general import BaseGeneralSchemas
from maleo_foundation.models.schemas.parameter import BaseParameterSchemas
from maleo_identity.enums.organization_registration_code import MaleoIdentityOrganizationRegistrationCodeEnums

class MaleoIdentityOrganizationRegistrationCodeSchemas:
    class IdentifierType(BaseParameterSchemas.IdentifierType):
        identifier:MaleoIdentityOrganizationRegistrationCodeEnums.IdentifierType = Field(..., description="Organization registration code's identifier")

    class Name(BaseGeneralSchemas.Name):
        name:str = Field(..., max_length=50, description="Organization Role's name")

    class Code(BaseModel):
        code:UUID = Field(..., description="Registration code")

    class MaxUses(BaseModel):
        max_uses:int = Field(..., ge=1, description="Max code uses")

    class CurrentUses(BaseModel):
        current_uses:int = Field(..., ge=0, description="Current code uses")