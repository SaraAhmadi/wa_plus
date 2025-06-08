from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship
from .base_model import Base
from .role_permission import user_roles_association, role_permissions_association


class Role(Base):
    # __tablename__ will be "roles" by Base default
    # As per SSR 8.4.5

    name = Column(String(100), unique=True, index=True, nullable=False) # e.g., "Administrator", "BasinManager"
    description = Column(Text, nullable=True)

    users = relationship(
        "User",
        secondary=user_roles_association,
        back_populates="roles"
    )

    permissions = relationship(
        "Permission",
        secondary=role_permissions_association,
        back_populates="roles"
    )

    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}')>"