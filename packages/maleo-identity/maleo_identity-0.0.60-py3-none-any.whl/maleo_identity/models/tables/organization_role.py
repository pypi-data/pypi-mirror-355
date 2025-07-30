from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.types import Integer, String, Boolean
from maleo_identity.db import MaleoIdentityMetadataManager
from maleo_foundation.models.table import DataTable

class OrganizationRolesMixin:
    #* Foreign Key OrganizationsTable
    organization_id = Column(
        Integer,
        ForeignKey(
            "organizations.id",
            ondelete="CASCADE",
            onupdate="CASCADE"
        ),
        nullable=False
    )
    is_default = Column(name="is_default", type_=Boolean, nullable=False, default=False)
    order = Column(name="order", type_=Integer)
    key = Column(name="key", type_=String(50), nullable=False)
    name = Column(name="name", type_=String(50), nullable=False)

class OrganizationRolesTable(
    OrganizationRolesMixin,
    DataTable,
    MaleoIdentityMetadataManager.Base
):
    __tablename__ = "organization_roles"

    organization = relationship(
        "OrganizationsTable",
        back_populates="organization_roles",
        cascade="all",
        lazy="select",
        uselist=False
    )

    user_organization_roles = relationship(
        "UserOrganizationRolesTable",
        back_populates="organization_role",
        cascade="all, delete-orphan",
        lazy="select"
    )