from sqlalchemy import Table, Column, Integer, ForeignKey
from .base_model import Base

# Association table for User and Role (Many-to-Many)
user_roles_association = Table(
    'user_roles', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete="CASCADE"), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id', ondelete="CASCADE"), primary_key=True)
)

# Association table for Role and Permission (Many-to-Many)
role_permissions_association = Table(
    'role_permissions', Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id', ondelete="CASCADE"), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id', ondelete="CASCADE"), primary_key=True)
)