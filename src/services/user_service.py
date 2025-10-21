# src\services\user_service.py
from typing import List, Optional, Dict, Any
from uuid import UUID

from src.repositories.user_repository import UserRepository
from src.models.schemas.user import User as UserSchema, UserCreate
from src.models.database.user import User as UserModel
from src.utils.logger import get_logger
from src.utils.password import hash_password, verify_password

logger = get_logger(__name__)


class UserService:
    """User management service with schema validation."""

    def __init__(self, user_repo: UserRepository):
        self.repo = user_repo

    def _model_to_schema(self, user_model: UserModel) -> UserSchema:
        """Convert database model to Pydantic schema."""
        return UserSchema.model_validate(user_model)

    def get_all_users(self) -> List[UserSchema]:
        """Get all active users."""
        users = self.repo.get_all_active()
        return [self._model_to_schema(user) for user in users]

    def get_user_by_email(self, email: str) -> Optional[UserSchema]:
        """Get user by email."""
        user = self.repo.get_by_email(email)
        return self._model_to_schema(user) if user else None

    def get_user_by_id(self, user_id: UUID) -> Optional[UserSchema]:
        """Get user by ID."""
        user = self.repo.get_by_id(user_id)
        return self._model_to_schema(user) if user else None

    def create_user(self, user_create: UserCreate) -> UserSchema:
        """Create new user with schema validation."""
        user_data = user_create.model_dump()

        # Hash password before storing
        if "password" in user_data:
            user_data["password"] = hash_password(user_data["password"])

        created_user = self.repo.create(user_data)
        logger.info(f"User created: {created_user.email}")
        return self._model_to_schema(created_user)

    # ============= Admin Operations =============

    def update_user(self, user_id: UUID, update_data: Dict[str, Any], admin_email: str) -> Optional[UserSchema]:
        """Update user (admin only)."""
        try:
            # Verify admin
            admin = self.get_user_by_email(admin_email)
            if not admin or admin.role != "admin":
                logger.warning(f"Unauthorized update attempt by {admin_email}")
                raise PermissionError("Only admins can update users")

            # Hash password if it's being updated
            if "password" in update_data:
                update_data["password"] = hash_password(update_data["password"])

            # Update user
            updated_user = self.repo.update(user_id, update_data)
            if updated_user:
                logger.info(f"User {user_id} updated by admin {admin_email}")
                return self._model_to_schema(updated_user)
            return None
        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {e}")
            raise

    def delete_user(self, user_id: UUID, admin_email: str) -> bool:
        """Delete user (admin only)."""
        try:
            # Verify admin
            admin = self.get_user_by_email(admin_email)
            if not admin or admin.role != "admin":
                logger.warning(f"Unauthorized delete attempt by {admin_email}")
                raise PermissionError("Only admins can delete users")

            # Prevent self-deletion
            user_to_delete = self.get_user_by_id(user_id)
            if user_to_delete and user_to_delete.email == admin_email:
                raise ValueError("Cannot delete your own account")

            # Ensure at least one admin remains
            if user_to_delete and user_to_delete.role == "admin":
                all_admins = [u for u in self.get_all_users() if u.role == "admin"]
                if len(all_admins) <= 1:
                    raise ValueError("Cannot delete the last admin")

            # Delete user
            success = self.repo.delete(user_id)
            if success:
                logger.info(f"User {user_id} deleted by admin {admin_email}")
            return success
        except Exception as e:
            logger.error(f"Failed to delete user {user_id}: {e}")
            raise

    def promote_to_admin(self, user_id: UUID, admin_email: str) -> Optional[UserSchema]:
        """Promote user to admin role (admin only)."""
        try:
            # Verify admin
            admin = self.get_user_by_email(admin_email)
            if not admin or admin.role != "admin":
                logger.warning(f"Unauthorized promotion attempt by {admin_email}")
                raise PermissionError("Only admins can promote users")

            # Promote user
            updated_user = self.repo.update(user_id, {"role": "admin"})
            if updated_user:
                logger.info(f"User {user_id} promoted to admin by {admin_email}")
                return self._model_to_schema(updated_user)
            return None
        except Exception as e:
            logger.error(f"Failed to promote user {user_id}: {e}")
            raise

    def demote_from_admin(self, user_id: UUID, admin_email: str) -> Optional[UserSchema]:
        """Demote admin to user role (admin only)."""
        try:
            # Verify admin
            admin = self.get_user_by_email(admin_email)
            if not admin or admin.role != "admin":
                logger.warning(f"Unauthorized demotion attempt by {admin_email}")
                raise PermissionError("Only admins can demote users")

            # Prevent self-demotion
            user_to_demote = self.get_user_by_id(user_id)
            if user_to_demote and user_to_demote.email == admin_email:
                raise ValueError("Cannot demote yourself")

            # Ensure at least one admin remains
            all_admins = [u for u in self.get_all_users() if u.role == "admin"]
            if len(all_admins) <= 1:
                raise ValueError("Cannot demote the last admin")

            # Demote user
            updated_user = self.repo.update(user_id, {"role": "user"})
            if updated_user:
                logger.info(f"User {user_id} demoted from admin by {admin_email}")
                return self._model_to_schema(updated_user)
            return None
        except Exception as e:
            logger.error(f"Failed to demote user {user_id}: {e}")
            raise

    def add_user(self, email: str, name: str, team: str, role: str, password: str, admin_email: str) -> UserSchema:
        """Add new user to system (admin only)."""
        try:
            # Verify admin
            admin = self.get_user_by_email(admin_email)
            if not admin or admin.role != "admin":
                logger.warning(f"Unauthorized user creation attempt by {admin_email}")
                raise PermissionError("Only admins can add users")

            # Check if user already exists
            existing = self.get_user_by_email(email)
            if existing:
                raise ValueError(f"User with email {email} already exists")

            # Validate role
            if role not in ["admin", "user"]:
                raise ValueError(f"Invalid role: {role}. Must be 'admin' or 'user'")

            # Create user
            user_create = UserCreate(email=email, name=name, team=team, role=role, password=password)
            created_user = self.create_user(user_create)
            logger.info(f"User {email} added by admin {admin_email}")
            return created_user
        except Exception as e:
            logger.error(f"Failed to add user {email}: {e}")
            raise

    # ============= User Self-Service Operations =============

    def change_password(self, user_email: str, current_password: str, new_password: str) -> bool:
        """
        Change user's own password.

        Args:
            user_email: Email of the user changing password
            current_password: Current password for verification
            new_password: New password to set

        Returns:
            True if password changed successfully, False otherwise

        Raises:
            ValueError: If current password is incorrect or validation fails
        """
        try:
            # Get user
            user = self.get_user_by_email(user_email)
            if not user:
                logger.warning(f"Password change attempt for non-existent user: {user_email}")
                raise ValueError("User not found")

            if not user.is_active:
                logger.warning(f"Inactive user attempted password change: {user_email}")
                raise ValueError("User account is inactive")

            # Get user model to access current password hash
            user_model = self.repo.get_by_email(user_email)
            if not user_model:
                raise ValueError("User not found")

            # Verify current password
            if not verify_password(current_password, user_model.password):
                logger.warning(f"Invalid current password provided by user: {user_email}")
                raise ValueError("Current password is incorrect")

            # Validate new password
            if len(new_password) < 6:
                raise ValueError("New password must be at least 6 characters long")

            if new_password == current_password:
                raise ValueError("New password must be different from current password")

            # Hash and update password
            hashed_new_password = hash_password(new_password)
            updated_user = self.repo.update_password(user.id, hashed_new_password)

            if updated_user:
                logger.info(f"Password changed successfully for user: {user_email}")
                return True

            return False

        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Failed to change password for {user_email}: {e}")
            raise

    def reset_password(self, user_email: str, new_password: str, admin_email: str) -> bool:
        """
        Reset user password (admin only).

        Args:
            user_email: Email of the user whose password to reset
            new_password: New password to set
            admin_email: Email of the admin performing the reset

        Returns:
            True if password reset successfully, False otherwise

        Raises:
            PermissionError: If requester is not an admin
            ValueError: If user not found or validation fails
        """
        try:
            # Verify admin
            admin = self.get_user_by_email(admin_email)
            if not admin or admin.role != "admin":
                logger.warning(f"Unauthorized password reset attempt by {admin_email}")
                raise PermissionError("Only admins can reset passwords")

            # Get target user
            user = self.get_user_by_email(user_email)
            if not user:
                logger.warning(f"Password reset attempt for non-existent user: {user_email}")
                raise ValueError("User not found")

            # Validate new password
            if len(new_password) < 6:
                raise ValueError("New password must be at least 6 characters long")

            # Hash and update password
            hashed_new_password = hash_password(new_password)
            updated_user = self.repo.update_password(user.id, hashed_new_password)

            if updated_user:
                logger.info(f"Password reset by admin {admin_email} for user: {user_email}")
                return True

            return False

        except (PermissionError, ValueError):
            # Re-raise permission and validation errors
            raise
        except Exception as e:
            logger.error(f"Failed to reset password for {user_email}: {e}")
            raise
