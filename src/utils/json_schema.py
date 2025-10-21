"""
JSON Schema Utility for Image Generation Prompts

This module provides the base JSON structure for image/logo generation prompts
and utilities for working with the schema.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
import json


def get_base_prompt_schema() -> Dict[str, Any]:
    """
    Returns the base prompt structure for image/logo generation.

    Returns:
        Dict containing the complete prompt schema
    """
    return {
        "prompt": {
            "title": "",
            "description": "",
            "elements": {
                "subject": "",
                "environment": "",
                "mood": "",
                "action": "",
                "camera": {
                    "angle": "",
                    "distance": "",
                    "lens": ""
                },
                "lighting": {
                    "style": "",
                    "intensity": "",
                    "color_temperature": ""
                },
                "color_palette": [],
                "composition": ""
            },
            "style": {
                "genre": [],
                "art_form": [],
                "inspiration": [],
                "techniques": []
            },
            "output_preferences": {
                "aspect_ratio": "1:1",
                "resolution": "1024x1024",
                "number_of_images": 1,
                "quality": "high",
                "style_strength": 0.7
            },
            "negative_prompt": {
                "undesired_elements": [],
                "exclude_styles": []
            },
            "metadata": {
                "version": "1.0",
                "creator": "",
                "created_at": ""
            }
        }
    }


def initialize_prompt(user_email: str) -> Dict[str, Any]:
    """
    Initialize a new prompt with metadata.

    Args:
        user_email: Email of the user creating the prompt

    Returns:
        Initialized prompt schema
    """
    schema = get_base_prompt_schema()
    schema["prompt"]["metadata"]["creator"] = user_email
    schema["prompt"]["metadata"]["created_at"] = datetime.utcnow().isoformat()
    return schema


def set_value_by_path(data: Dict[str, Any], path: str, value: Any) -> None:
    """
    Set a value in a nested dictionary using dot notation path.

    Args:
        data: The dictionary to modify
        path: Dot-notation path (e.g., "prompt.elements.mood")
        value: Value to set

    Example:
        >>> data = {"prompt": {"elements": {}}}
        >>> set_value_by_path(data, "prompt.elements.mood", "cozy")
        >>> data["prompt"]["elements"]["mood"]
        'cozy'
    """
    keys = path.split('.')
    for key in keys[:-1]:
        data = data.setdefault(key, {})
    data[keys[-1]] = value


def get_value_by_path(data: Dict[str, Any], path: str, default: Any = None) -> Any:
    """
    Get a value from a nested dictionary using dot notation path.

    Args:
        data: The dictionary to read from
        path: Dot-notation path (e.g., "prompt.elements.mood")
        default: Default value if path doesn't exist

    Returns:
        Value at path or default
    """
    keys = path.split('.')
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key)
            if data is None:
                return default
        else:
            return default
    return data


# Field mapping: maps common user concepts to JSON paths
FIELD_MAP = {
    "mood": "prompt.elements.mood",
    "feeling": "prompt.elements.mood",
    "vibe": "prompt.elements.mood",
    "style": "prompt.style.genre",
    "genre": "prompt.style.genre",
    "color": "prompt.elements.color_palette",
    "colors": "prompt.elements.color_palette",
    "palette": "prompt.elements.color_palette",
    "theme_color": "prompt.elements.color_palette",
    "environment": "prompt.elements.environment",
    "background": "prompt.elements.environment",
    "composition": "prompt.elements.composition",
    "layout": "prompt.elements.composition",
    "subject": "prompt.elements.subject",
    "main_focus": "prompt.elements.subject",
    "resolution": "prompt.output_preferences.resolution",
    "size": "prompt.output_preferences.resolution",
    "aspect_ratio": "prompt.output_preferences.aspect_ratio",
    "lighting": "prompt.elements.lighting.style",
    "lighting_style": "prompt.elements.lighting.style",
    "techniques": "prompt.style.techniques",
    "art_form": "prompt.style.art_form",
    "inspiration": "prompt.style.inspiration",
    "title": "prompt.title",
    "name": "prompt.title",
    "description": "prompt.description",
    "action": "prompt.elements.action",
    "undesired": "prompt.negative_prompt.undesired_elements",
    "exclude": "prompt.negative_prompt.exclude_styles",
}


def get_field_path(field_name: str) -> Optional[str]:
    """
    Get the JSON path for a field name.

    Args:
        field_name: Common name for a field

    Returns:
        Dot-notation path or None if not found
    """
    return FIELD_MAP.get(field_name.lower())


def is_prompt_complete(prompt: Dict[str, Any]) -> bool:
    """
    Check if a prompt has all required fields filled.

    Args:
        prompt: The prompt dictionary to validate

    Returns:
        True if all required fields are filled
    """
    required_fields = [
        "prompt.title",
        "prompt.description",
        "prompt.elements.subject",
        "prompt.elements.mood",
        "prompt.elements.environment",
        "prompt.elements.composition",
        "prompt.elements.color_palette",
        "prompt.style.genre",
        "prompt.style.art_form",
    ]

    for field_path in required_fields:
        value = get_value_by_path(prompt, field_path)
        if not value:  # Empty string, empty list, or None
            return False

    return True


def get_missing_fields(prompt: Dict[str, Any]) -> List[str]:
    """
    Get a list of required fields that are still empty.

    Args:
        prompt: The prompt dictionary to check

    Returns:
        List of field paths that are empty
    """
    required_fields = {
        "prompt.title": "title or name",
        "prompt.description": "detailed description",
        "prompt.elements.subject": "main subject",
        "prompt.elements.mood": "mood or feeling",
        "prompt.elements.environment": "environment or background",
        "prompt.elements.composition": "composition or layout",
        "prompt.elements.color_palette": "color palette",
        "prompt.style.genre": "style or genre",
        "prompt.style.art_form": "art form",
    }

    missing = []
    for field_path, field_name in required_fields.items():
        value = get_value_by_path(prompt, field_path)
        if not value:
            missing.append(field_name)

    return missing


def export_prompt_json(prompt: Dict[str, Any], filepath: str) -> None:
    """
    Export prompt to a JSON file.

    Args:
        prompt: The prompt dictionary to export
        filepath: Path to save the JSON file
    """
    with open(filepath, 'w') as f:
        json.dump(prompt, f, indent=2)


def compile_final_prompt(prompt: Dict[str, Any]) -> str:
    """
    Compile the structured prompt into a single text prompt for image generation.

    Args:
        prompt: The prompt dictionary

    Returns:
        Compiled text prompt
    """
    p = prompt.get("prompt", {})
    elements = p.get("elements", {})
    style = p.get("style", {})

    parts = []

    # Title and description
    if p.get("title"):
        parts.append(f"Title: {p['title']}")
    if p.get("description"):
        parts.append(p["description"])

    # Main elements
    if elements.get("subject"):
        parts.append(f"Subject: {elements['subject']}")
    if elements.get("mood"):
        parts.append(f"Mood: {elements['mood']}")
    if elements.get("environment"):
        parts.append(f"Environment: {elements['environment']}")
    if elements.get("composition"):
        parts.append(f"Composition: {elements['composition']}")

    # Color palette
    if elements.get("color_palette"):
        colors = ", ".join(elements["color_palette"])
        parts.append(f"Colors: {colors}")

    # Lighting
    lighting = elements.get("lighting", {})
    if lighting.get("style"):
        parts.append(f"Lighting: {lighting['style']}")

    # Style
    if style.get("genre"):
        genres = ", ".join(style["genre"]) if isinstance(style["genre"], list) else style["genre"]
        parts.append(f"Style: {genres}")
    if style.get("art_form"):
        art_forms = ", ".join(style["art_form"]) if isinstance(style["art_form"], list) else style["art_form"]
        parts.append(f"Art form: {art_forms}")
    if style.get("techniques"):
        techniques = ", ".join(style["techniques"]) if isinstance(style["techniques"], list) else style["techniques"]
        parts.append(f"Techniques: {techniques}")

    # Negative prompt
    negative = p.get("negative_prompt", {})
    if negative.get("undesired_elements"):
        undesired = ", ".join(negative["undesired_elements"])
        parts.append(f"Avoid: {undesired}")

    return ". ".join(parts)
