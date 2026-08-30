"""Security utilities: hashing, JWT, current-user dependencies."""
from app.security.password import hash_password, verify_password
from app.security.jwt_handler import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_refresh_token,
)
from app.security.dependencies import (
    get_current_user,
    get_current_active_user,
    require_roles,
)

__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "hash_refresh_token",
    "get_current_user",
    "get_current_active_user",
    "require_roles",
]
