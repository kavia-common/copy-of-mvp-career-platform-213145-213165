"""Pydantic schemas for authentication endpoints."""
from __future__ import annotations

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    """Request payload for user registration."""
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password (plaintext; will be hashed)")
    full_name: str | None = Field(None, description="Optional full name")


class LoginRequest(BaseModel):
    """Request payload for user login."""
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class TokenResponse(BaseModel):
    """Response containing a bearer token."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type (always 'bearer')")
