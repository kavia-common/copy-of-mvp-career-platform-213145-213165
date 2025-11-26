"""Authentication routes: register, login, logout, profile."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.deps import get_current_user, get_db
from src.core.security import create_access_token, get_password_hash, verify_password
from src.models.audit import AuditLog
from src.models.user import User
from src.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from src.schemas.user import ProfileUpdate, UserOut

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


# PUBLIC_INTERFACE
@router.post(
    "/register",
    response_model=UserOut,
    summary="Register a new user",
    description="Create a new user account.",
    responses={
        201: {"description": "User registered"},
        409: {"description": "User already exists"},
    },
    status_code=status.HTTP_201_CREATED,
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> UserOut:
    """Register a new user.

    Args:
        payload: The RegisterRequest containing email, password, and optional full_name.
        db: Database session.

    Returns:
        UserOut: The created user (without password hash).
    """
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        password_hash=get_password_hash(payload.password),
    )
    db.add(user)
    db.flush()
    db.add(AuditLog(user_id=user.id, action="register", entity_type="User", entity_id=str(user.id)))
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


# PUBLIC_INTERFACE
@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User login",
    description="Authenticate with email/password and receive a JWT token.",
    responses={200: {"description": "JWT token"}, 401: {"description": "Unauthorized"}},
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Authenticate user and return JWT token."""
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(subject=str(user.id), extra_claims={"email": user.email})
    user.last_login_at = user.last_login_at  # no-op to keep schema simple
    db.add(AuditLog(user_id=user.id, action="login", entity_type="User", entity_id=str(user.id)))
    db.commit()
    return TokenResponse(access_token=token)


# PUBLIC_INTERFACE
@router.post(
    "/logout",
    summary="User logout",
    description="Stateless logout (JWT invalidation not persisted).",
    responses={200: {"description": "Logged out"}},
)
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    """Placeholder logout endpoint. Records an audit event."""
    db.add(AuditLog(user_id=current_user.id, action="logout", entity_type="User", entity_id=str(current_user.id)))
    db.commit()
    return {"status": "ok"}


# PUBLIC_INTERFACE
@router.get(
    "/profile",
    response_model=UserOut,
    summary="Get user profile",
    description="Return basic profile data for the authenticated user.",
    responses={200: {"description": "Profile"}, 401: {"description": "Unauthorized"}},
)
def get_profile(current_user: User = Depends(get_current_user)) -> UserOut:
    """Return the current user's profile."""
    return UserOut.model_validate(current_user)


# PUBLIC_INTERFACE
@router.put(
    "/profile",
    response_model=UserOut,
    summary="Update user profile",
    description="Update basic profile fields.",
)
def update_profile(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserOut:
    """Update profile fields."""
    if payload.full_name is not None:
        current_user.full_name = payload.full_name
    db.add(current_user)
    db.add(
        AuditLog(
            user_id=current_user.id,
            action="profile_update",
            entity_type="User",
            entity_id=str(current_user.id),
            details={"full_name": payload.full_name},
        )
    )
    db.commit()
    db.refresh(current_user)
    return UserOut.model_validate(current_user)
