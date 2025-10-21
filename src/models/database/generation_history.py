from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

from config.database import Base


class GenerationHistory(Base):
    """Generation history model."""

    __tablename__ = "generation_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    project_name = Column(String(255), nullable=True, index=True)  # Auto-generated from user input

    # Conversation data
    conversation_messages = Column(JSONB, nullable=False, default=list)
    final_prompt = Column(Text, nullable=False)
    raw_user_input = Column(Text)

    # Generation parameters
    selected_parameters = Column(JSONB, default=dict)

    # Generated image paths
    generated_image_url = Column(Text, nullable=True)
    thumbnail_url = Column(Text, nullable=True)

    # Visibility setting
    visibility = Column(String(20), default="private", index=True)  # 'public' or 'private'

    # Status and metadata
    status = Column(String(50), default="drafting", index=True)
    generation_metadata = Column(JSONB, default=dict)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<GenerationHistory {self.project_name} - {self.status}>"
