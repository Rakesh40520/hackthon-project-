"""Password hashing using bcrypt."""
from passlib.context import CryptContext

from app.config import settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=settings.BCRYPT_ROUNDS)


def hash_password(plain: str) -> str:
    """Hash a plaintext password."""
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a password against a hash."""
    try:
        return _pwd_context.verify(plain, hashed)
    except Exception:
        return False
