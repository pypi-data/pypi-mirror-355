from __future__ import annotations
from maleo_foundation.models.schemas.parameter import BaseParameterSchemas
from maleo_foundation.models.transfers.parameters.general import BaseGeneralParametersTransfers
from maleo_identity.models.schemas.general import MaleoIdentityGeneralSchemas
from maleo_identity.models.schemas.organization_registration_code import MaleoIdentityOrganizationRegistrationCodeSchemas

class MaleoIdentityOrganizationRegistrationCodeGeneralParametersTransfers:
    class GetSingleQuery(BaseGeneralParametersTransfers.GetSingleQuery): pass

    class GetSingle(
        BaseParameterSchemas.OptionalListOfStatuses,
        BaseParameterSchemas.IdentifierValue,
        MaleoIdentityOrganizationRegistrationCodeSchemas.IdentifierType
    ): pass

    class CreateFromOrganizationData(
        MaleoIdentityOrganizationRegistrationCodeSchemas.MaxUses
    ): pass

    class CreateData(
        MaleoIdentityGeneralSchemas.OrganizationId,
        MaleoIdentityOrganizationRegistrationCodeSchemas.MaxUses
    ): pass

    class Create(CreateData): pass

    class UpdateData(MaleoIdentityOrganizationRegistrationCodeSchemas.MaxUses): pass

    class Update(
        UpdateData,
        BaseParameterSchemas.IdentifierValue,
        MaleoIdentityOrganizationRegistrationCodeSchemas.IdentifierType
    ): pass