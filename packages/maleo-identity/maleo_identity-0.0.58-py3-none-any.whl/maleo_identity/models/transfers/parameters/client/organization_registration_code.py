from __future__ import annotations
from maleo_foundation.models.schemas.parameter import BaseParameterSchemas
from maleo_foundation.models.transfers.parameters.client import BaseClientParametersTransfers
from maleo_identity.models.schemas.general import MaleoIdentityGeneralSchemas

class MaleoIdentityOrganizationRegistrationCodeClientParametersTransfers:
    class GetMultipleFromOrganization(
        BaseClientParametersTransfers.GetPaginatedMultiple,
        MaleoIdentityGeneralSchemas.OrganizationId
    ): pass
    
    class GetMultiple(
        BaseClientParametersTransfers.GetPaginatedMultiple,
        MaleoIdentityGeneralSchemas.OptionalListOfOrganizationIds
    ): pass

    class GetMultipleFromOrganizationQuery(
        BaseClientParametersTransfers.GetPaginatedMultipleQuery
    ): pass

    class GetMultipleQuery(
        BaseClientParametersTransfers.GetPaginatedMultipleQuery,
        MaleoIdentityGeneralSchemas.OptionalListOfOrganizationIds
    ): pass