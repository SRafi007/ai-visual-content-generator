from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr
    name: str
    role: str = "user"  # admin or user
    team: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating user."""

    password: str  # Plain password (will be hashed before storage)


class User(UserBase):
    """User response schema."""

    id: UUID
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
