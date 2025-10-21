# src/models/schemas/content.py
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, Literal


class ContentBase(BaseModel):
    """Base content schema."""

    title: str = Field(..., min_length=1, max_length=255, description="Content title")
    prompt: str = Field(..., min_length=1, description="Generation prompt used")
    visibility: Literal["public", "private"] = Field(default="private", description="Content visibility")


class ContentCreate(ContentBase):
    """Schema for creating content."""

    user_id: UUID
    generation_id: Optional[UUID] = None
    generated_image_url: str = Field(..., description="Path or URL to generated image")
    thumbnail_url: Optional[str] = Field(None, description="Path or URL to thumbnail")


class ContentUpdate(BaseModel):
    """Schema for updating content."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    prompt: Optional[str] = Field(None, min_length=1)
    visibility: Optional[Literal["public", "private"]] = None
    generated_image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None


class ContentResponse(ContentBase):
    """Content response schema."""

    id: UUID
    user_id: UUID
    generation_id: Optional[UUID]
    generated_image_url: str
    thumbnail_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ContentListItem(BaseModel):
    """Simplified content schema for list views."""

    id: UUID
    title: str
    thumbnail_url: Optional[str]
    visibility: str
    created_at: datetime

    class Config:
        from_attributes = True


class ContentVisibilityUpdate(BaseModel):
    """Schema for updating content visibility."""

    visibility: Literal["public", "private"] = Field(..., description="New visibility setting")
