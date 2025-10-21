# src/services/content_service.py
from typing import List, Optional
from uuid import UUID

from src.repositories.content_repository import ContentRepository
from src.models.schemas.content import (
    ContentResponse,
    ContentCreate,
    ContentUpdate,
    ContentListItem,
)
from src.models.database.content import Content as ContentModel
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ContentService:
    """Content management service with schema validation."""

    def __init__(self, content_repo: ContentRepository):
        self.repo = content_repo

    def _model_to_schema(self, content_model: ContentModel) -> ContentResponse:
        """Convert database model to Pydantic schema."""
        return ContentResponse.model_validate(content_model)

    def _model_to_list_item(self, content_model: ContentModel) -> ContentListItem:
        """Convert database model to list item schema."""
        return ContentListItem.model_validate(content_model)

    def create_content(self, content_create: ContentCreate) -> ContentResponse:
        """Create new content."""
        try:
            content_data = content_create.model_dump()
            created_content = self.repo.create(content_data)
            logger.info(
                f"Content created: {created_content.title} by user {content_create.user_id}"
            )
            return self._model_to_schema(created_content)
        except Exception as e:
            logger.error(f"Failed to create content: {e}")
            raise

    def get_content(self, content_id: UUID) -> Optional[ContentResponse]:
        """Get content by ID."""
        content = self.repo.get_by_id(content_id)
        return self._model_to_schema(content) if content else None

    def get_user_content(self, user_id: UUID) -> List[ContentResponse]:
        """Get all content for a user."""
        content_list = self.repo.get_by_user(user_id)
        return [self._model_to_schema(c) for c in content_list]

    def get_user_content_list(self, user_id: UUID) -> List[ContentListItem]:
        """Get simplified content list for a user."""
        content_list = self.repo.get_by_user(user_id)
        return [self._model_to_list_item(c) for c in content_list]

    def get_public_content(self, limit: Optional[int] = None) -> List[ContentResponse]:
        """Get all public content."""
        content_list = self.repo.get_public_content(limit)
        return [self._model_to_schema(c) for c in content_list]

    def get_public_content_list(
        self, limit: Optional[int] = None
    ) -> List[ContentListItem]:
        """Get simplified public content list."""
        content_list = self.repo.get_public_content(limit)
        return [self._model_to_list_item(c) for c in content_list]

    def update_content(
        self, content_id: UUID, content_update: ContentUpdate, user_id: UUID
    ) -> Optional[ContentResponse]:
        """
        Update content (owner only).

        Args:
            content_id: ID of content to update
            content_update: Update data
            user_id: ID of user making the request

        Returns:
            Updated content or None if not found/unauthorized
        """
        try:
            # Verify ownership
            content = self.repo.get_by_id(content_id)
            if not content:
                logger.warning(f"Content not found: {content_id}")
                return None

            if content.user_id != user_id:
                logger.warning(
                    f"Unauthorized update attempt by user {user_id} on content {content_id}"
                )
                raise PermissionError("You don't have permission to update this content")

            # Update content
            update_data = content_update.model_dump(exclude_unset=True)
            updated_content = self.repo.update(content_id, update_data)

            if updated_content:
                logger.info(f"Content {content_id} updated by user {user_id}")
                return self._model_to_schema(updated_content)

            return None

        except PermissionError:
            raise
        except Exception as e:
            logger.error(f"Failed to update content {content_id}: {e}")
            raise

    def update_visibility(
        self, content_id: UUID, visibility: str, user_id: UUID
    ) -> Optional[ContentResponse]:
        """
        Update content visibility (owner only).

        Args:
            content_id: ID of content to update
            visibility: New visibility ('public' or 'private')
            user_id: ID of user making the request

        Returns:
            Updated content or None if not found/unauthorized
        """
        try:
            # Verify ownership
            content = self.repo.get_by_id(content_id)
            if not content:
                logger.warning(f"Content not found: {content_id}")
                return None

            if content.user_id != user_id:
                logger.warning(
                    f"Unauthorized visibility update attempt by user {user_id} on content {content_id}"
                )
                raise PermissionError(
                    "You don't have permission to update this content's visibility"
                )

            # Validate visibility
            if visibility not in ["public", "private"]:
                raise ValueError("Visibility must be 'public' or 'private'")

            # Update visibility
            updated_content = self.repo.update_visibility(content_id, visibility)

            if updated_content:
                logger.info(
                    f"Content {content_id} visibility changed to {visibility} by user {user_id}"
                )
                return self._model_to_schema(updated_content)

            return None

        except (PermissionError, ValueError):
            raise
        except Exception as e:
            logger.error(f"Failed to update content visibility {content_id}: {e}")
            raise

    def delete_content(self, content_id: UUID, user_id: UUID) -> bool:
        """
        Delete content (owner only).

        Args:
            content_id: ID of content to delete
            user_id: ID of user making the request

        Returns:
            True if deleted, False otherwise
        """
        try:
            # Verify ownership
            content = self.repo.get_by_id(content_id)
            if not content:
                logger.warning(f"Content not found: {content_id}")
                return False

            if content.user_id != user_id:
                logger.warning(
                    f"Unauthorized delete attempt by user {user_id} on content {content_id}"
                )
                raise PermissionError("You don't have permission to delete this content")

            # Delete content
            success = self.repo.delete(content_id)

            if success:
                logger.info(f"Content {content_id} deleted by user {user_id}")

            return success

        except PermissionError:
            raise
        except Exception as e:
            logger.error(f"Failed to delete content {content_id}: {e}")
            raise

    def search_content(
        self, search_term: str, user_id: Optional[UUID] = None
    ) -> List[ContentResponse]:
        """
        Search content by title.

        Args:
            search_term: Search term for title
            user_id: Optional user ID to filter by owner

        Returns:
            List of matching content
        """
        try:
            content_list = self.repo.search_by_title(search_term, user_id)
            return [self._model_to_schema(c) for c in content_list]
        except Exception as e:
            logger.error(f"Failed to search content: {e}")
            raise

    def get_content_stats(self, user_id: UUID) -> dict:
        """Get content statistics for a user."""
        try:
            total_content = self.repo.count_by_user(user_id)
            user_content = self.repo.get_by_user(user_id)

            public_count = sum(1 for c in user_content if c.visibility == "public")
            private_count = sum(1 for c in user_content if c.visibility == "private")

            return {
                "total_content": total_content,
                "public_content": public_count,
                "private_content": private_count,
            }
        except Exception as e:
            logger.error(f"Failed to get content stats for user {user_id}: {e}")
            raise

    def get_recent_public_content(self, limit: int = 10) -> List[ContentListItem]:
        """Get recent public content."""
        try:
            content_list = self.repo.get_recent_public(limit)
            return [self._model_to_list_item(c) for c in content_list]
        except Exception as e:
            logger.error(f"Failed to get recent public content: {e}")
            raise
