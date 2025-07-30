from __future__ import annotations
from pydantic import Field
from typing import Optional
from maleo_foundation.models.transfers.results.service.repository import BaseServiceRepositoryResultsTransfers
from maleo_identity.models.schemas.user import MaleoIdentityUserSchemas
from maleo_identity.models.transfers.general.user import UserTransfers, PasswordTransfers

class MaleoIdentityUserRepositoryResultsTransfers:
    class Fail(BaseServiceRepositoryResultsTransfers.Fail): pass

    class NoData(BaseServiceRepositoryResultsTransfers.NoData): pass

    class SingleData(BaseServiceRepositoryResultsTransfers.SingleData):
        data:UserTransfers = Field(..., description="Single user data")

    class MultipleData(BaseServiceRepositoryResultsTransfers.PaginatedMultipleData):
        data:list[UserTransfers] = Field(..., description="Single users data")

    class SinglePassword(BaseServiceRepositoryResultsTransfers.SingleData):
        data:PasswordTransfers = Field(..., description="Single password data")

    class SingleRegisterData(BaseServiceRepositoryResultsTransfers.SingleData):
        data:UserTransfers = Field(..., description="Single user data")
        metadata:Optional[MaleoIdentityUserSchemas.RegisterResultMetadata] = Field(None, description="Optional metadata")