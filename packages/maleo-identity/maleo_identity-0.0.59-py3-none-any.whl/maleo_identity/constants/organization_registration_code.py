from typing import Dict
from uuid import UUID
from maleo_identity.enums.organization_registration_code import MaleoIdentityOrganizationRegistrationCodeEnums

class MaleoIdentityOrganizationRegistrationCodeConstants:
    IDENTIFIER_TYPE_VALUE_TYPE_MAP:Dict[
        MaleoIdentityOrganizationRegistrationCodeEnums.IdentifierType,
        object
    ] = {
        MaleoIdentityOrganizationRegistrationCodeEnums.IdentifierType.ID: int,
        MaleoIdentityOrganizationRegistrationCodeEnums.IdentifierType.UUID: UUID,
        MaleoIdentityOrganizationRegistrationCodeEnums.IdentifierType.ORGANIZATION_ID: int,
        MaleoIdentityOrganizationRegistrationCodeEnums.IdentifierType.CODE: UUID
    }