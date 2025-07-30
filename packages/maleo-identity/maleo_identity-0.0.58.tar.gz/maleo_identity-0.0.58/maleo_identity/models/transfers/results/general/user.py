from __future__ import annotations
from pydantic import Field
from typing import Optional
from maleo_foundation.models.transfers.results.service.general import BaseServiceGeneralResultsTransfers
from maleo_identity.models.schemas.user import MaleoIdentityUserSchemas
from maleo_identity.models.transfers.general.user import UserTransfers, PasswordTransfers

class MaleoIdentityUserGeneralResultsTransfers:
    class Fail(BaseServiceGeneralResultsTransfers.Fail): pass

    class NoData(BaseServiceGeneralResultsTransfers.NoData): pass

    class SingleData(BaseServiceGeneralResultsTransfers.SingleData):
        data:UserTransfers = Field(..., description="Single user data")

    class MultipleData(BaseServiceGeneralResultsTransfers.PaginatedMultipleData):
        data:list[UserTransfers] = Field(..., description="Multiple users data")

    class SinglePassword(BaseServiceGeneralResultsTransfers.SingleData):
        data:PasswordTransfers = Field(..., description="Single user password")

    class SingleRegisterData(BaseServiceGeneralResultsTransfers.SingleData):
        data:UserTransfers = Field(..., description="Single user data")
        metadata:Optional[MaleoIdentityUserSchemas.RegisterResultMetadata] = Field(None, description="Optional metadata")