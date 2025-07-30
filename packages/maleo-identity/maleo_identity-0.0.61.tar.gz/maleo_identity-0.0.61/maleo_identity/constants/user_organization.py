from typing import Dict, List
from maleo_identity.enums.user import MaleoIdentityUserEnums
from maleo_identity.enums.organization import MaleoIdentityOrganizationEnums
from maleo_identity.enums.user_organization import MaleoIdentityUserOrganizationEnums

class MaleoIdentityUserOrganizationConstants:
    EXPANDABLE_FIELDS_DEPENDENCIES_MAP:Dict[
        MaleoIdentityUserOrganizationEnums.ExpandableFields,
        List[MaleoIdentityUserOrganizationEnums.ExpandableFields]
    ] = {
        MaleoIdentityUserOrganizationEnums.ExpandableFields.USER: [
            MaleoIdentityUserOrganizationEnums.ExpandableFields.USER_TYPE,
            MaleoIdentityUserOrganizationEnums.ExpandableFields.PROFILE
        ],
        MaleoIdentityUserOrganizationEnums.ExpandableFields.PROFILE: [
            MaleoIdentityUserOrganizationEnums.ExpandableFields.BLOOD_TYPE,
            MaleoIdentityUserOrganizationEnums.ExpandableFields.GENDER
        ],
        MaleoIdentityUserOrganizationEnums.ExpandableFields.SYSTEM_ROLES: [
            MaleoIdentityUserOrganizationEnums.ExpandableFields.SYSTEM_ROLE_DETAILS
        ],
        MaleoIdentityUserOrganizationEnums.ExpandableFields.ORGANIZATION: [
            MaleoIdentityUserOrganizationEnums.ExpandableFields.ORGANIZATION_TYPE,
            MaleoIdentityUserOrganizationEnums.ExpandableFields.REGISTRATION_CODE
        ]
    }

    USER_EXPANDABLE_FIELDS_MAP:Dict[
        MaleoIdentityUserOrganizationEnums.ExpandableFields,
        MaleoIdentityUserEnums.ExpandableFields
    ] = {
        MaleoIdentityUserOrganizationEnums.ExpandableFields.USER_TYPE: MaleoIdentityUserEnums.ExpandableFields.USER_TYPE,
        MaleoIdentityUserOrganizationEnums.ExpandableFields.PROFILE: MaleoIdentityUserEnums.ExpandableFields.PROFILE,
        MaleoIdentityUserOrganizationEnums.ExpandableFields.BLOOD_TYPE: MaleoIdentityUserEnums.ExpandableFields.BLOOD_TYPE,
        MaleoIdentityUserOrganizationEnums.ExpandableFields.GENDER: MaleoIdentityUserEnums.ExpandableFields.GENDER,
        MaleoIdentityUserOrganizationEnums.ExpandableFields.SYSTEM_ROLES: MaleoIdentityUserEnums.ExpandableFields.SYSTEM_ROLES,
        MaleoIdentityUserOrganizationEnums.ExpandableFields.SYSTEM_ROLE_DETAILS: MaleoIdentityUserEnums.ExpandableFields.SYSTEM_ROLE_DETAILS
    }

    ORGANIZATION_EXPANDABLE_FIELDS_MAP:Dict[
        MaleoIdentityUserOrganizationEnums.ExpandableFields,
        MaleoIdentityOrganizationEnums.ExpandableFields
    ] = {
        MaleoIdentityUserOrganizationEnums.ExpandableFields.ORGANIZATION_TYPE: MaleoIdentityOrganizationEnums.ExpandableFields.ORGANIZATION_TYPE,
        MaleoIdentityUserOrganizationEnums.ExpandableFields.REGISTRATION_CODE: MaleoIdentityOrganizationEnums.ExpandableFields.REGISTRATION_CODE
    }