# src\services\generation_service.py
"""Generation service with schema validation."""

from typing import List, Optional
from uuid import UUID

from src.repositories.generation_repository import GenerationRepository
from src.models.schemas.generation import (
    GenerationCreate,
    GenerationUpdate,
    GenerationResponse,
)
from src.models.database.generation_history import GenerationHistory as GenerationModel
from src.utils.project_utils import generate_project_name


class GenerationService:
    """Generation management service with schema validation."""

    def __init__(self, gen_repo: GenerationRepository):
        self.repo = gen_repo

    def _model_to_schema(self, gen_model: GenerationModel) -> GenerationResponse:
        """Convert database model to Pydantic schema."""
        return GenerationResponse.model_validate(gen_model)

    def create_generation(
        self, generation_create: GenerationCreate
    ) -> GenerationResponse:
        """Create new generation with schema validation."""
        gen_data = generation_create.model_dump()

        # Auto-generate project name if not provided
        if not gen_data.get("project_name"):
            raw_input = gen_data.get("raw_user_input", "")
            gen_data["project_name"] = generate_project_name(raw_input)

        # Convert Message schemas to dicts for database
        if gen_data.get("conversation_messages"):
            gen_data["conversation_messages"] = [
                msg.model_dump() if hasattr(msg, "model_dump") else msg
                for msg in gen_data["conversation_messages"]
            ]

        # Convert GenerationParameters to dict for database
        if gen_data.get("selected_parameters"):
            params = gen_data["selected_parameters"]
            gen_data["selected_parameters"] = (
                params.model_dump() if hasattr(params, "model_dump") else params
            )

        created_gen = self.repo.create(gen_data)
        return self._model_to_schema(created_gen)

    def update_generation(
        self, generation_id: UUID, generation_update: GenerationUpdate
    ) -> Optional[GenerationResponse]:
        """Update generation with schema validation."""
        update_data = generation_update.model_dump(exclude_unset=True)

        # Convert schemas to dicts for database
        if update_data.get("conversation_messages"):
            update_data["conversation_messages"] = [
                msg.model_dump() if hasattr(msg, "model_dump") else msg
                for msg in update_data["conversation_messages"]
            ]

        if update_data.get("selected_parameters"):
            params = update_data["selected_parameters"]
            update_data["selected_parameters"] = (
                params.model_dump() if hasattr(params, "model_dump") else params
            )

        updated_gen = self.repo.update(generation_id, update_data)
        return self._model_to_schema(updated_gen) if updated_gen else None

    def get_generation_by_id(self, generation_id: UUID) -> Optional[GenerationResponse]:
        """Get generation by ID."""
        gen = self.repo.get_by_id(generation_id)
        return self._model_to_schema(gen) if gen else None

    def get_user_generations(
        self, user_id: UUID, limit: int = 20
    ) -> List[GenerationResponse]:
        """Get generations by user."""
        generations = self.repo.get_by_user(user_id, limit)
        return [self._model_to_schema(gen) for gen in generations]

    def get_project_generations(
        self, user_id: UUID, project_name: str
    ) -> List[GenerationResponse]:
        """Get generations by project."""
        generations = self.repo.get_by_project(user_id, project_name)
        return [self._model_to_schema(gen) for gen in generations]

    def get_user_projects(self, user_id: UUID) -> List[str]:
        """Get unique project names for user."""
        return self.repo.get_user_projects(user_id)

    def delete_generation(self, generation_id: UUID) -> bool:
        """Delete generation."""
        return self.repo.delete(generation_id)

    def get_public_generations(self, limit: int = 50) -> List[GenerationResponse]:
        """Get all public generations for home feed."""
        generations = self.repo.get_public_generations(limit)
        return [self._model_to_schema(gen) for gen in generations]

    def update_visibility(self, generation_id: UUID, visibility: str) -> Optional[GenerationResponse]:
        """Update visibility of a generation."""
        updated = self.repo.update_visibility(generation_id, visibility)
        return self._model_to_schema(updated) if updated else None
