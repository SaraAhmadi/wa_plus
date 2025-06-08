from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship
from .base_model import Base
from .role_permission import role_permissions_association 


class Permission(Base):
    __tablename__ = "permissions" # Explicitly set as per SSR 8.4.6 'Permissions table'

    name = Column(String(100), unique=True, index=True, nullable=False) # e.g., "view_basin_X_data"
    description = Column(Text, nullable=True)

    roles = relationship(
        "Role",
        secondary=role_permissions_association,
        back_populates="permissions"
    )

    def __repr__(self):
        return f"<Permission(id={self.id}, name='{self.name}')>"