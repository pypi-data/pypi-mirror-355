from __future__ import annotations
from pydantic import Field
from maleo_foundation.models.transfers.results.service.general import BaseServiceGeneralResultsTransfers
from maleo_identity.models.transfers.general.organization_registration_code import OrganizationRegistrationCodeTransfers

class MaleoIdentityOrganizationRegistrationCodeServiceResultsTransfers:
    class Fail(BaseServiceGeneralResultsTransfers.Fail): pass

    class NoData(BaseServiceGeneralResultsTransfers.NoData): pass

    class SingleData(BaseServiceGeneralResultsTransfers.SingleData):
        data:OrganizationRegistrationCodeTransfers = Field(..., description="Single organization registration code data")

    class MultipleData(BaseServiceGeneralResultsTransfers.PaginatedMultipleData):
        data:list[OrganizationRegistrationCodeTransfers] = Field(..., description="Multiple organization registration codes data")