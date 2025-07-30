from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from maleo_foundation.models.schemas.parameter import BaseParameterSchemas
from maleo_foundation.models.schemas.result import ResultMetadata
from maleo_foundation.types import BaseTypes
from maleo_identity.enums.user import MaleoIdentityUserEnums

class MaleoIdentityUserSchemas:
    class IdentifierType(BaseParameterSchemas.IdentifierType):
        identifier:MaleoIdentityUserEnums.IdentifierType = Field(..., description="User's identifier")

    class Expand(BaseParameterSchemas.Expand):
        expand:Optional[List[MaleoIdentityUserEnums.ExpandableFields]] = Field(None, description="Expanded field(s)")

    class Username(BaseModel):
        username:str = Field(..., max_length=50, description="User's username")

    class OptionalListOfUsernames(BaseModel):
        usernames:BaseTypes.OptionalListOfStrings = Field(None, description="Specific usernames")

    class Email(BaseModel):
        email:str = Field(..., max_length=255, description="User's email")

    class OptionalListOfEmails(BaseModel):
        emails:BaseTypes.OptionalListOfStrings = Field(None, description="Specific emails")

    class Phone(BaseModel):
        phone:str = Field(..., min_length=4, max_length=15, description="User's phone")

    class OptionalListOfPhones(BaseModel):
        phones:BaseTypes.OptionalListOfStrings = Field(None, description="Specific phones")

    class Password(BaseModel):
        password:str = Field(..., max_length=255, description="User's password")

    class PasswordConfirmation(BaseModel):
        password_confirmation:str = Field(..., max_length=255, description="User's password confirmation")

    class RegistrationCode(BaseModel):
        registration_code:UUID = Field(..., description="Registration code")

    class RegisterResultMetadata(ResultMetadata):
        organization_key:BaseTypes.OptionalString = Field(None, description="Organization key")