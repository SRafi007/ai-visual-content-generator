from typing import List, Optional
from sqlalchemy.orm import Session
from uuid import UUID

from src.repositories.base import BaseRepository
from src.models.database.generation_history import GenerationHistory


class GenerationRepository(BaseRepository[GenerationHistory]):
    """Generation history repository."""

    def __init__(self, db: Session):
        super().__init__(GenerationHistory, db)

    def get_by_user(self, user_id: UUID, limit: int = 20) -> List[GenerationHistory]:
        """Get generations by user."""
        return (
            self.db.query(GenerationHistory)
            .filter(GenerationHistory.user_id == user_id)
            .order_by(GenerationHistory.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_by_project(
        self, user_id: UUID, project_name: str
    ) -> List[GenerationHistory]:
        """Get generations by project."""
        return (
            self.db.query(GenerationHistory)
            .filter(
                GenerationHistory.user_id == user_id,
                GenerationHistory.project_name == project_name,
            )
            .order_by(GenerationHistory.created_at.desc())
            .all()
        )

    def get_user_projects(self, user_id: UUID) -> List[str]:
        """Get unique project names for user."""
        projects = (
            self.db.query(GenerationHistory.project_name)
            .filter(GenerationHistory.user_id == user_id)
            .distinct()
            .all()
        )
        return [p[0] for p in projects]

    def get_by_status(self, status: str) -> List[GenerationHistory]:
        """Get generations by status."""
        return (
            self.db.query(GenerationHistory)
            .filter(GenerationHistory.status == status)
            .all()
        )

    def get_public_generations(self, limit: int = 50) -> List[GenerationHistory]:
        """Get all public generations (for home feed)."""
        from src.models.database.user import User

        return (
            self.db.query(GenerationHistory)
            .join(User, GenerationHistory.user_id == User.id)
            .filter(
                GenerationHistory.visibility == "public",
                GenerationHistory.status == "completed",
                GenerationHistory.generated_image_url.isnot(None)
            )
            .order_by(GenerationHistory.created_at.desc())
            .limit(limit)
            .all()
        )

    def update_visibility(self, generation_id: UUID, visibility: str) -> Optional[GenerationHistory]:
        """Update visibility of a generation."""
        generation = self.get_by_id(generation_id)
        if generation:
            generation.visibility = visibility
            self.db.commit()
            self.db.refresh(generation)
        return generation
