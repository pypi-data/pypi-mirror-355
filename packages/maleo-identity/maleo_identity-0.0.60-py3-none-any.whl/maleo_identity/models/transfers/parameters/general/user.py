from __future__ import annotations
from maleo_foundation.models.schemas.parameter import BaseParameterSchemas
from maleo_metadata.models.expanded_schemas.blood_type import MaleoMetadataBloodTypeExpandedSchemas
from maleo_metadata.models.expanded_schemas.gender import MaleoMetadataGenderExpandedSchemas
from maleo_metadata.models.expanded_schemas.user_type import MaleoMetadataUserTypeExpandedSchemas
from maleo_identity.models.schemas.general import MaleoIdentityGeneralSchemas
from maleo_identity.models.schemas.user import MaleoIdentityUserSchemas
from maleo_identity.models.schemas.user_profile import MaleoIdentityUserProfileSchemas

class MaleoIdentityUserGeneralParametersTransfers:
    class GetSingleQuery(
        MaleoIdentityUserSchemas.Expand,
        BaseParameterSchemas.OptionalListOfStatuses
    ): pass

    class BaseGetSingle(
        BaseParameterSchemas.IdentifierValue,
        MaleoIdentityUserSchemas.IdentifierType
    ): pass

    class GetSinglePassword(BaseGetSingle): pass

    class GetSingle(
        MaleoIdentityUserSchemas.Expand,
        BaseParameterSchemas.OptionalListOfStatuses,
        BaseGetSingle
    ): pass

    class CreateOrUpdateQuery(MaleoIdentityUserSchemas.Expand): pass

    class UpdateData(
        MaleoIdentityUserSchemas.Phone,
        MaleoIdentityUserSchemas.Email,
        MaleoIdentityUserSchemas.Username
    ): pass

    class CreateData(
        MaleoIdentityUserSchemas.Password,
        UpdateData,
        MaleoMetadataUserTypeExpandedSchemas.SimpleUserType,
        MaleoIdentityGeneralSchemas.OptionalOrganizationId
    ): pass

    class Update(
        CreateOrUpdateQuery,
        UpdateData,
        BaseParameterSchemas.IdentifierValue,
        MaleoIdentityUserSchemas.IdentifierType
    ): pass

    class Create(
        CreateOrUpdateQuery,
        CreateData
    ): pass

    class Register(
        CreateOrUpdateQuery,
        MaleoIdentityUserProfileSchemas.OptionalAvatarName,
        MaleoIdentityUserProfileSchemas.OptionalAvatarContentType,
        MaleoIdentityUserProfileSchemas.OptionalAvatar,
        MaleoMetadataBloodTypeExpandedSchemas.OptionalSimpleBloodType,
        MaleoMetadataGenderExpandedSchemas.OptionalSimpleGender,
        MaleoIdentityUserProfileSchemas.BirthDate,
        MaleoIdentityUserProfileSchemas.BirthPlace,
        MaleoIdentityUserProfileSchemas.EndingTitle,
        MaleoIdentityUserProfileSchemas.LastName,
        MaleoIdentityUserProfileSchemas.MiddleName,
        MaleoIdentityUserProfileSchemas.FirstName,
        MaleoIdentityUserProfileSchemas.LeadingTitle,
        MaleoIdentityUserProfileSchemas.OptionalIdCard,
        MaleoIdentityUserSchemas.PasswordConfirmation,
        MaleoIdentityUserSchemas.Password,
        MaleoIdentityUserSchemas.Phone,
        MaleoIdentityUserSchemas.Email,
        MaleoIdentityUserSchemas.Username,
        MaleoIdentityUserSchemas.RegistrationCode
    ): pass