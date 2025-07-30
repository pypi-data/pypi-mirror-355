from .roles import IRoleRepository, IPermissionRepository
from .users import IUserRepository
from .oauths import IOAuthRepository

__all__ = [
    "IRoleRepository",
    "IPermissionRepository",
    "IUserRepository",
    "IOAuthRepository",
]
