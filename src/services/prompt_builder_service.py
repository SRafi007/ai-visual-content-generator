"""
Prompt Builder Service

This service orchestrates the conversational prompt building process:
- Manages prompt state
- Updates fields from user input
- Validates completeness
- Coordinates with LLM service
"""

from typing import Dict, Any, List, Optional
from src.utils.logger import get_logger
from src.utils.json_schema import (
    get_base_prompt_schema,
    initialize_prompt,
    set_value_by_path,
    get_value_by_path,
    get_field_path,
    is_prompt_complete,
    get_missing_fields,
    compile_final_prompt,
    FIELD_MAP
)

logger = get_logger(__name__)


class PromptBuilderService:
    """Service for managing the prompt building workflow."""

    def __init__(self):
        """Initialize the prompt builder service."""
        logger.info("Prompt Builder Service initialized")

    def create_new_prompt(self, user_email: str) -> Dict[str, Any]:
        """
        Create a new prompt with initialized metadata.

        Args:
            user_email: Email of the user creating the prompt

        Returns:
            Initialized prompt schema
        """
        prompt = initialize_prompt(user_email)
        logger.info(f"Created new prompt for user: {user_email}")
        return prompt

    def update_prompt_from_extraction(
        self,
        current_prompt: Dict[str, Any],
        extracted_fields: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update prompt with fields extracted from user input.

        Args:
            current_prompt: Current prompt state
            extracted_fields: Dictionary of {field_path: value} from LLM analysis

        Returns:
            Updated prompt
        """
        updated_count = 0

        for field_path, value in extracted_fields.items():
            try:
                # Get current value
                current_value = get_value_by_path(current_prompt, field_path)

                # Handle list fields (append rather than replace)
                if isinstance(current_value, list) and isinstance(value, list):
                    # Merge lists, avoiding duplicates
                    existing_set = set(str(v).lower() for v in current_value)
                    for new_val in value:
                        if str(new_val).lower() not in existing_set:
                            current_value.append(new_val)
                            updated_count += 1
                elif isinstance(current_value, list) and not isinstance(value, list):
                    # Convert single value to list
                    if str(value).lower() not in set(str(v).lower() for v in current_value):
                        current_value.append(value)
                        updated_count += 1
                else:
                    # For non-list fields, only update if currently empty
                    if not current_value or current_value == "":
                        set_value_by_path(current_prompt, field_path, value)
                        updated_count += 1
                        logger.debug(f"Updated {field_path} = {value}")

            except Exception as e:
                logger.error(f"Error updating field {field_path}: {str(e)}")

        logger.info(f"Updated {updated_count} fields in prompt")
        return current_prompt

    def update_single_field(
        self,
        current_prompt: Dict[str, Any],
        field_name: str,
        value: Any
    ) -> Dict[str, Any]:
        """
        Update a single field in the prompt.

        Args:
            current_prompt: Current prompt state
            field_name: Name or path of the field
            value: Value to set

        Returns:
            Updated prompt
        """
        # Try to get the full path
        field_path = get_field_path(field_name)

        if not field_path:
            # Assume it's already a full path
            field_path = field_name

        try:
            set_value_by_path(current_prompt, field_path, value)
            logger.info(f"Updated field: {field_path}")
        except Exception as e:
            logger.error(f"Error updating field {field_path}: {str(e)}")

        return current_prompt

    def validate_prompt(self, prompt: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate if prompt is complete and ready for generation.

        Args:
            prompt: The prompt to validate

        Returns:
            Tuple of (is_complete, list_of_missing_fields)
        """
        is_complete = is_prompt_complete(prompt)
        missing = get_missing_fields(prompt) if not is_complete else []

        logger.info(f"Prompt validation: complete={is_complete}, missing={len(missing)} fields")
        return is_complete, missing

    def get_completion_percentage(self, prompt: Dict[str, Any]) -> int:
        """
        Calculate what percentage of the prompt is complete.

        Args:
            prompt: The prompt to check

        Returns:
            Percentage (0-100)
        """
        total_fields = [
            "prompt.title",
            "prompt.description",
            "prompt.elements.subject",
            "prompt.elements.mood",
            "prompt.elements.environment",
            "prompt.elements.composition",
            "prompt.elements.color_palette",
            "prompt.style.genre",
            "prompt.style.art_form",
            "prompt.style.techniques",
        ]

        filled_count = 0
        for field_path in total_fields:
            value = get_value_by_path(prompt, field_path)
            if value:  # Not empty
                filled_count += 1

        percentage = int((filled_count / len(total_fields)) * 100)
        return percentage

    def compile_prompt_for_generation(self, prompt: Dict[str, Any]) -> str:
        """
        Compile the structured prompt into final text for image generation.

        Args:
            prompt: The completed prompt JSON

        Returns:
            Text prompt ready for image generation API
        """
        final_text = compile_final_prompt(prompt)
        logger.info("Compiled final prompt for generation")
        return final_text

    def get_prompt_summary(self, prompt: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get a summary of the current prompt state.

        Args:
            prompt: The prompt to summarize

        Returns:
            Dictionary with summary information
        """
        p = prompt.get("prompt", {})
        elements = p.get("elements", {})
        style = p.get("style", {})

        summary = {
            "title": p.get("title", "Untitled"),
            "subject": elements.get("subject", "Not specified"),
            "mood": elements.get("mood", "Not specified"),
            "colors": elements.get("color_palette", []),
            "style": style.get("genre", []),
            "completion_percentage": self.get_completion_percentage(prompt),
            "is_complete": is_prompt_complete(prompt),
            "missing_fields": get_missing_fields(prompt)
        }

        return summary

    def merge_prompts(
        self,
        base_prompt: Dict[str, Any],
        updates: Dict[str, Any],
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        Merge two prompts, combining their data.

        Args:
            base_prompt: The base prompt to update
            updates: Prompt with new data
            overwrite: If True, overwrite existing values. If False, only fill empty fields.

        Returns:
            Merged prompt
        """
        def merge_dict(base: Dict, update: Dict) -> Dict:
            """Recursively merge dictionaries."""
            for key, value in update.items():
                if key in base:
                    if isinstance(base[key], dict) and isinstance(value, dict):
                        merge_dict(base[key], value)
                    elif isinstance(base[key], list) and isinstance(value, list):
                        # Merge lists, avoiding duplicates
                        for item in value:
                            if item not in base[key]:
                                base[key].append(item)
                    elif overwrite or not base[key]:
                        base[key] = value
                else:
                    base[key] = value
            return base

        merged = merge_dict(base_prompt.copy(), updates)
        logger.info("Merged prompt updates")
        return merged

    def reset_prompt(self, user_email: str) -> Dict[str, Any]:
        """
        Reset to a fresh prompt.

        Args:
            user_email: User email for metadata

        Returns:
            Fresh prompt
        """
        logger.info(f"Resetting prompt for user: {user_email}")
        return self.create_new_prompt(user_email)

    def export_to_dict(self, prompt: Dict[str, Any]) -> Dict[str, Any]:
        """
        Export prompt in a format suitable for storage.

        Args:
            prompt: The prompt to export

        Returns:
            Exportable dictionary
        """
        return prompt.copy()

    def import_from_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Import prompt from stored format.

        Args:
            data: Stored prompt data

        Returns:
            Prompt object
        """
        return data.copy()
