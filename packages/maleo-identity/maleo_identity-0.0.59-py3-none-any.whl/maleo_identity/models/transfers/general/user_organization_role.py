from maleo_foundation.models.schemas.general import BaseGeneralSchemas
from maleo_identity.models.schemas.general import MaleoIdentityGeneralSchemas
from maleo_identity.models.schemas.user_organization_role import MaleoIdentityUserOrganizationRoleSchemas
from maleo_identity.models.transfers.general.organization import ExpandedOrganization
from maleo_identity.models.transfers.general.organization_role import ExpandedOrganizationRole
from maleo_identity.models.transfers.general.user import ExpandedUser
from maleo_identity.models.transfers.general.user_organization import ExpandedUserOrganization

class UserOrganizationRoleTransfers(
    ExpandedOrganizationRole,
    # ExpandedOrganization,
    # MaleoIdentityGeneralSchemas.OrganizationId,
    # ExpandedUser,
    # MaleoIdentityGeneralSchemas.UserId,
    ExpandedUserOrganization,
    BaseGeneralSchemas.Status,
    BaseGeneralSchemas.Timestamps,
    BaseGeneralSchemas.Identifiers
): pass