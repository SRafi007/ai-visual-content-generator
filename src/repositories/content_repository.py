from typing import Optional, List
from sqlalchemy.orm import Session
from uuid import UUID

from src.repositories.base import BaseRepository
from src.models.database.content import Content


class ContentRepository(BaseRepository[Content]):
    """Content repository with additional query methods."""

    def __init__(self, db: Session):
        super().__init__(Content, db)

    def get_by_user(self, user_id: UUID) -> List[Content]:
        """Get all content for a specific user."""
        return (
            self.db.query(Content)
            .filter(Content.user_id == user_id)
            .order_by(Content.created_at.desc())
            .all()
        )

    def get_by_user_and_visibility(
        self, user_id: UUID, visibility: str
    ) -> List[Content]:
        """Get user's content filtered by visibility."""
        return (
            self.db.query(Content)
            .filter(Content.user_id == user_id, Content.visibility == visibility)
            .order_by(Content.created_at.desc())
            .all()
        )

    def get_public_content(self, limit: Optional[int] = None) -> List[Content]:
        """Get all public content."""
        query = (
            self.db.query(Content)
            .filter(Content.visibility == "public")
            .order_by(Content.created_at.desc())
        )

        if limit:
            query = query.limit(limit)

        return query.all()

    def get_by_generation(self, generation_id: UUID) -> Optional[Content]:
        """Get content by generation ID."""
        return (
            self.db.query(Content)
            .filter(Content.generation_id == generation_id)
            .first()
        )

    def update_visibility(self, content_id: UUID, visibility: str) -> Optional[Content]:
        """Update content visibility."""
        content = self.get_by_id(content_id)
        if content:
            content.visibility = visibility
            self.db.commit()
            self.db.refresh(content)
        return content

    def search_by_title(self, search_term: str, user_id: Optional[UUID] = None) -> List[Content]:
        """Search content by title."""
        query = self.db.query(Content).filter(
            Content.title.ilike(f"%{search_term}%")
        )

        if user_id:
            query = query.filter(Content.user_id == user_id)

        return query.order_by(Content.created_at.desc()).all()

    def get_recent_public(self, limit: int = 10) -> List[Content]:
        """Get recent public content."""
        return (
            self.db.query(Content)
            .filter(Content.visibility == "public")
            .order_by(Content.created_at.desc())
            .limit(limit)
            .all()
        )

    def count_by_user(self, user_id: UUID) -> int:
        """Count total content items for a user."""
        return self.db.query(Content).filter(Content.user_id == user_id).count()

    def count_public(self) -> int:
        """Count total public content items."""
        return self.db.query(Content).filter(Content.visibility == "public").count()
