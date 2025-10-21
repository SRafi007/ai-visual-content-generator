from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from config.database import Base


class Content(Base):
    """Content model for generated images and prompts."""

    __tablename__ = "content"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    generation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("generation_history.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Content details
    title = Column(String(255), nullable=False, index=True)
    prompt = Column(Text, nullable=False)
    generated_image_url = Column(Text, nullable=False)
    thumbnail_url = Column(Text)

    # Visibility control
    visibility = Column(String(20), default="private", nullable=False, index=True)  # 'public' or 'private'

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Content {self.title} - {self.visibility}>"
