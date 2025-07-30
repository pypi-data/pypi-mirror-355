from typing import Union
from maleo_identity.models.transfers.results.service.organization_registration_code \
    import MaleoIdentityOrganizationRegistrationCodeServiceResultsTransfers

class MaleoIdentityOrganizationRegistrationCodeServiceResultsTypes:
    GetMultiple = Union[
        MaleoIdentityOrganizationRegistrationCodeServiceResultsTransfers.Fail,
        MaleoIdentityOrganizationRegistrationCodeServiceResultsTransfers.NoData,
        MaleoIdentityOrganizationRegistrationCodeServiceResultsTransfers.MultipleData
    ]

    GetSingle = Union[
        MaleoIdentityOrganizationRegistrationCodeServiceResultsTransfers.Fail,
        MaleoIdentityOrganizationRegistrationCodeServiceResultsTransfers.NoData,
        MaleoIdentityOrganizationRegistrationCodeServiceResultsTransfers.SingleData
    ]

    CreateOrUpdate = Union[
        MaleoIdentityOrganizationRegistrationCodeServiceResultsTransfers.Fail,
        MaleoIdentityOrganizationRegistrationCodeServiceResultsTransfers.SingleData
    ]