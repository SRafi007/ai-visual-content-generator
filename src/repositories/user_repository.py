from typing import Optional, List
from sqlalchemy.orm import Session

from src.repositories.base import BaseRepository
from src.models.database.user import User


class UserRepository(BaseRepository[User]):
    """User repository."""

    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()

    def get_all_active(self) -> List[User]:
        """Get all active users."""
        return self.db.query(User).filter(User.is_active == True).all()

    def get_by_team(self, team: str) -> List[User]:
        """Get users by team."""
        return self.db.query(User).filter(User.team == team).all()

    def update_password(self, user_id, hashed_password: str) -> Optional[User]:
        """Update user password."""
        user = self.get_by_id(user_id)
        if user:
            user.password = hashed_password
            self.db.commit()
            self.db.refresh(user)
        return user
