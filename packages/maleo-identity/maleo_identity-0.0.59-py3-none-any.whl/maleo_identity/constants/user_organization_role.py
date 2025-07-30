from typing import Dict, List
from maleo_identity.enums.user import MaleoIdentityUserEnums
from maleo_identity.enums.organization import MaleoIdentityOrganizationEnums
from maleo_identity.enums.user_organization_role import MaleoIdentityUserOrganizationRoleEnums

class MaleoIdentityUserOrganizationRoleConstants:
    EXPANDABLE_FIELDS_DEPENDENCIES_MAP:Dict[
        MaleoIdentityUserOrganizationRoleEnums.ExpandableFields,
        List[MaleoIdentityUserOrganizationRoleEnums.ExpandableFields]
    ] = {
        MaleoIdentityUserOrganizationRoleEnums.ExpandableFields.USER: [
            MaleoIdentityUserOrganizationRoleEnums.ExpandableFields.USER_TYPE,
            MaleoIdentityUserOrganizationRoleEnums.ExpandableFields.PROFILE
        ],
        MaleoIdentityUserOrganizationRoleEnums.ExpandableFields.ORGANIZATION: [
            MaleoIdentityUserOrganizationRoleEnums.ExpandableFields.ORGANIZATION_TYPE,
            MaleoIdentityUserOrganizationRoleEnums.ExpandableFields.REGISTRATION_CODE
        ]
    }

    USER_EXPANDABLE_FIELDS_MAP:Dict[
        MaleoIdentityUserOrganizationRoleEnums.ExpandableFields,
        MaleoIdentityUserEnums.ExpandableFields
    ] = {
        MaleoIdentityUserOrganizationRoleEnums.ExpandableFields.USER_TYPE: MaleoIdentityUserEnums.ExpandableFields.USER_TYPE,
        MaleoIdentityUserOrganizationRoleEnums.ExpandableFields.PROFILE: MaleoIdentityUserEnums.ExpandableFields.PROFILE
    }

    ORGANIZATION_EXPANDABLE_FIELDS_MAP:Dict[
        MaleoIdentityUserOrganizationRoleEnums.ExpandableFields,
        MaleoIdentityOrganizationEnums.ExpandableFields
    ] = {
        MaleoIdentityUserOrganizationRoleEnums.ExpandableFields.ORGANIZATION_TYPE: MaleoIdentityOrganizationEnums.ExpandableFields.ORGANIZATION_TYPE,
        MaleoIdentityUserOrganizationRoleEnums.ExpandableFields.REGISTRATION_CODE: MaleoIdentityOrganizationEnums.ExpandableFields.REGISTRATION_CODE
    }