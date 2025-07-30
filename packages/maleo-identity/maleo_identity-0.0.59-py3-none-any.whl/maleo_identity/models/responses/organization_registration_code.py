from pydantic import Field
from maleo_foundation.models.responses import BaseResponses
from maleo_identity.enums.organization_registration_code import MaleoIdentityOrganizationRegistrationCodeEnums
from maleo_identity.models.transfers.general.organization_registration_code import OrganizationRegistrationCodeTransfers

class MaleoIdentityOrganizationRegistrationCodeResponses:
    class InvalidIdentifierType(BaseResponses.BadRequest):
        code:str = "IDT-ORC-001"
        message:str = "Invalid identifier type"
        description:str = "Invalid identifier type is given in the request"
        other: str = f"Valid identifier types: {[f'{e.name} ({e.value})' for e in MaleoIdentityOrganizationRegistrationCodeEnums.IdentifierType]}"

    class InvalidValueType(BaseResponses.BadRequest):
        code:str = "IDT-ORC-002"
        message:str = "Invalid value type"
        description:str = "Invalid value type is given in the request"

    class GetSingle(BaseResponses.SingleData):
        code:str = "IDT-ORC-003"
        message:str = "Organization registration code found"
        description:str = "Requested organization registration code found in database"
        data:OrganizationRegistrationCodeTransfers = Field(..., description="Organization registration code")

    class GetMultiple(BaseResponses.PaginatedMultipleData):
        code:str = "IDT-ORC-004"
        message:str = "Organization registration codes found"
        description:str = "Requested organization registration codes found in database"
        data:list[OrganizationRegistrationCodeTransfers] = Field(..., description="Organization registration codes")

    class CreateFailed(BaseResponses.BadRequest):
        code:str = "IDT-ORC-005"
        message:str = "Failed creating new organization registration code"

    class CreateSuccess(BaseResponses.SingleData):
        code:str = "IDT-ORC-006"
        message:str = "Successfully created new organization registration code"
        data:OrganizationRegistrationCodeTransfers = Field(..., description="Organization registration code")

    class UpdateFailed(BaseResponses.BadRequest):
        code:str = "IDT-ORC-007"
        message:str = "Failed updating organization registration code's data"

    class UpdateSuccess(BaseResponses.SingleData):
        code:str = "IDT-ORC-008"
        message:str = "Successfully updated organization registration code's data"
        data:OrganizationRegistrationCodeTransfers = Field(..., description="Organization registration code")