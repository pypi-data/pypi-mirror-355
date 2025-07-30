from typing import Union
from maleo_identity.models.transfers.results.client.organization_registration_code \
    import MaleoIdentityOrganizationRegistrationCodeClientResultsTransfers

class MaleoIdentityOrganizationRegistrationCodeClientResultsTypes:
    GetMultiple = Union[
        MaleoIdentityOrganizationRegistrationCodeClientResultsTransfers.Fail,
        MaleoIdentityOrganizationRegistrationCodeClientResultsTransfers.NoData,
        MaleoIdentityOrganizationRegistrationCodeClientResultsTransfers.MultipleData
    ]

    GetSingle = Union[
        MaleoIdentityOrganizationRegistrationCodeClientResultsTransfers.Fail,
        MaleoIdentityOrganizationRegistrationCodeClientResultsTransfers.SingleData
    ]

    Create = Union[
        MaleoIdentityOrganizationRegistrationCodeClientResultsTransfers.Fail,
        MaleoIdentityOrganizationRegistrationCodeClientResultsTransfers.SingleData
    ]