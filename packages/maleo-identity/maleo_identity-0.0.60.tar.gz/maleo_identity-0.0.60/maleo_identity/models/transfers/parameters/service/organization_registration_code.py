from __future__ import annotations
from maleo_foundation.models.schemas.parameter import BaseParameterSchemas
from maleo_foundation.models.transfers.parameters.service import BaseServiceParametersTransfers
from maleo_identity.models.schemas.general import MaleoIdentityGeneralSchemas

class MaleoIdentityOrganizationRegistrationCodeServiceParametersTransfers:
    class GetMultipleFromOrganizationQuery(
        BaseServiceParametersTransfers.GetPaginatedMultipleQuery
    ): pass

    class GetMultipleQuery(
        BaseServiceParametersTransfers.GetPaginatedMultipleQuery,
        MaleoIdentityGeneralSchemas.OptionalListOfOrganizationIds
    ): pass

    class GetMultiple(
        BaseServiceParametersTransfers.GetPaginatedMultiple,
        MaleoIdentityGeneralSchemas.OptionalListOfOrganizationIds
    ): pass