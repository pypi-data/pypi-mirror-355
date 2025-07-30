from sqlalchemy import Column
from sqlalchemy.orm import relationship
from sqlalchemy.types import String, Enum
from maleo_metadata.enums.user_type import MaleoMetadataUserTypeEnums
from maleo_identity.db import MaleoIdentityMetadataManager
from maleo_foundation.models.table import DataTable

class UsersMixin:
    user_type = Column(
        name="user_type",
        type_=Enum(MaleoMetadataUserTypeEnums.UserType, name="user_type"),
        default=MaleoMetadataUserTypeEnums.UserType.REGULAR,
        nullable=False
    )
    username = Column(name="username", type_=String(50), unique=True, nullable=False)
    email = Column(name="email", type_=String(255), unique=True, nullable=False)
    phone = Column(name="phone", type_=String(15), nullable=False)
    password = Column(name="password", type_=String(255), nullable=False)

class UsersTable(
    UsersMixin,
    DataTable,
    MaleoIdentityMetadataManager.Base
):
    __tablename__ = "users"

    profile = relationship(
        "UserProfilesTable",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    system_roles = relationship(
        "UserSystemRolesTable",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    user_organization = relationship(
        "UserOrganizationsTable",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False
    )