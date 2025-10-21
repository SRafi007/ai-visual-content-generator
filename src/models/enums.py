from enum import Enum


class GenerationStatus(str, Enum):
    """
    Generation status enumeration.

    Used to track the lifecycle of image generation requests.
    Stored in generation_history.status column.
    """

    DRAFTING = "drafting"  # User is still refining the prompt
    GENERATING = "generating"  # Image generation in progress
    COMPLETED = "completed"  # Image successfully generated
    FAILED = "failed"  # Generation failed with error


class UserRole(str, Enum):
    """
    User role enumeration.

    Defines team roles for organizational purposes.
    Can be extended for future permission systems.
    """

    DESIGN = "Design"
    MARKETING = "Marketing"
    PRODUCT = "Product"
