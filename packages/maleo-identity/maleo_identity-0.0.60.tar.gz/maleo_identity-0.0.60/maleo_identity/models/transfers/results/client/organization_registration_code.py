from __future__ import annotations
from pydantic import Field
from maleo_foundation.models.transfers.results.client.service import BaseClientServiceResultsTransfers
from maleo_identity.models.transfers.general.organization_registration_code import OrganizationRegistrationCodeTransfers

class MaleoIdentityOrganizationRegistrationCodeClientResultsTransfers:
    class Fail(BaseClientServiceResultsTransfers.Fail): pass

    class NoData(BaseClientServiceResultsTransfers.NoData): pass

    class SingleData(BaseClientServiceResultsTransfers.SingleData):
        data:OrganizationRegistrationCodeTransfers = Field(..., description="Single organization registration code data")

    class MultipleData(BaseClientServiceResultsTransfers.PaginatedMultipleData):
        data:list[OrganizationRegistrationCodeTransfers] = Field(..., description="Multiple organization registration codes data")