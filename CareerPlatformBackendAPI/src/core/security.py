"""Security utilities: password hashing and JWT token helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# PUBLIC_INTERFACE
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against the stored hash."""
    return pwd_context.verify(plain_password, hashed_password)


# PUBLIC_INTERFACE
def get_password_hash(password: str) -> str:
    """Hash a plaintext password for storage."""
    return pwd_context.hash(password)


# PUBLIC_INTERFACE
def create_access_token(subject: str, extra_claims: Optional[Dict[str, Any]] = None) -> str:
    """Create a JWT access token for a subject (user id or email).

    Args:
        subject: The unique identifier for the token subject (e.g., user ID).
        extra_claims: Additional claims to embed in the token.

    Returns:
        A signed JWT token string.
    """
    settings = get_settings()
    to_encode: Dict[str, Any] = {"sub": subject, "iat": datetime.now(tz=timezone.utc)}
    if extra_claims:
        to_encode.update(extra_claims)

    expire_at = datetime.now(tz=timezone.utc) + settings.access_token_expires()
    to_encode.update({"exp": expire_at})

    token = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token


# PUBLIC_INTERFACE
def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT token.

    Args:
        token: The JWT token string.

    Returns:
        The decoded claims dictionary.

    Raises:
        JWTError: If the token is invalid or expired.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as e:
        raise e
    return payload
