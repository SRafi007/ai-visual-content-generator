# src\models\schemas\generation.py
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import List, Dict, Optional, Any


class Message(BaseModel):
    """Chat message schema."""

    role: str
    content: str
    timestamp: Optional[str] = None


class GenerationParameters(BaseModel):
    """Image generation parameters."""

    style: Optional[str] = None
    lighting: Optional[str] = None
    background: Optional[str] = None
    color_palette: Optional[str] = None
    aspect_ratio: Optional[str] = "1:1"
    quality: Optional[str] = "high"


class GenerationCreate(BaseModel):
    """Schema for creating generation."""

    user_id: UUID
    project_name: Optional[str] = None  # Auto-generated if not provided
    raw_user_input: str
    conversation_messages: List[Message] = []
    final_prompt: str
    selected_parameters: Optional[GenerationParameters] = None
    visibility: Optional[str] = "private"  # 'public' or 'private'


class GenerationUpdate(BaseModel):
    """Schema for updating generation."""

    conversation_messages: Optional[List[Message]] = None
    final_prompt: Optional[str] = None
    selected_parameters: Optional[GenerationParameters] = None
    status: Optional[str] = None
    generation_metadata: Optional[Dict[str, Any]] = None
    visibility: Optional[str] = None
    generated_image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None


class GenerationResponse(BaseModel):
    """Generation response schema."""

    id: UUID
    user_id: UUID
    project_name: str
    conversation_messages: List[Message]
    final_prompt: str
    raw_user_input: Optional[str]
    selected_parameters: Optional[Dict[str, Any]]
    status: str
    generation_metadata: Optional[Dict[str, Any]]
    visibility: Optional[str] = "private"
    generated_image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
