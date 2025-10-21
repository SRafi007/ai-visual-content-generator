"""Utility functions for project name generation."""

import re
from datetime import datetime


def generate_project_name(user_input: str, max_length: int = 50) -> str:
    """
    Generate a project name from user input.

    Args:
        user_input: The user's prompt or description
        max_length: Maximum length of the project name

    Returns:
        A clean project name suitable for database storage
    """
    if not user_input or not user_input.strip():
        # Fallback to timestamp-based name
        return f"Generation {datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Clean the input
    cleaned = user_input.strip()

    # Remove special characters, keep alphanumeric and spaces
    cleaned = re.sub(r"[^\w\s-]", "", cleaned)

    # Replace multiple spaces with single space
    cleaned = re.sub(r"\s+", " ", cleaned)

    # Truncate to max length
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length].rsplit(" ", 1)[0]  # Break at word boundary

    # If still too short or empty, use fallback
    if len(cleaned) < 3:
        return f"Generation {datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Capitalize first letter of each word
    cleaned = cleaned.title()

    return cleaned


def extract_key_words(text: str, num_words: int = 4) -> str:
    """
    Extract key words from text for project naming.

    Args:
        text: Input text
        num_words: Number of words to extract

    Returns:
        String with key words
    """
    # Common words to skip
    stop_words = {
        "a",
        "an",
        "the",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "from",
        "i",
        "want",
        "need",
        "create",
        "generate",
        "make",
        "image",
        "picture",
        "photo",
    }

    # Split into words
    words = re.findall(r"\w+", text.lower())

    # Filter out stop words and short words
    key_words = [w for w in words if w not in stop_words and len(w) > 2]

    # Take first num_words
    key_words = key_words[:num_words]

    if not key_words:
        return generate_project_name(text)

    # Join and capitalize
    result = " ".join(key_words).title()
    return result
