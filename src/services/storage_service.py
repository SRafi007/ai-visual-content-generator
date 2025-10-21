"""File storage service."""

import os
from pathlib import Path
from uuid import UUID
from PIL import Image
from io import BytesIO

from config.settings import get_settings
from src.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


class StorageService:
    """File storage service."""

    def __init__(self):
        self.storage_path = Path(settings.STORAGE_PATH)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.thumbnail_path = self.storage_path / "thumbnails"
        self.thumbnail_path.mkdir(exist_ok=True)

        logger.info(f"Storage initialized at: {self.storage_path}")

    def save_image(self, image_data: bytes, generation_id: UUID) -> str:
        """Save generated image."""
        try:
            filename = f"{generation_id}.png"
            filepath = self.storage_path / filename

            # Save bytes directly
            with open(filepath, "wb") as f:
                f.write(image_data)

            logger.info(f"✓ Image saved: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"✗ Failed to save image: {e}")
            raise

    def save_thumbnail(
        self, image_data: bytes, generation_id: UUID, size: tuple = (300, 300)
    ) -> str:
        """Create and save thumbnail."""
        try:
            # Create a fresh BytesIO object from bytes
            img_buffer = BytesIO(image_data)

            # Open image from bytes
            img = Image.open(img_buffer)

            # Convert to RGB if necessary (handles RGBA, P, etc.)
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')

            # Create thumbnail (maintains aspect ratio)
            img.thumbnail(size, Image.Resampling.LANCZOS)

            filename = f"{generation_id}_thumb.png"
            filepath = self.thumbnail_path / filename

            # Save thumbnail
            img.save(filepath, "PNG")

            logger.info(f"✓ Thumbnail saved: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"✗ Failed to save thumbnail: {e}")
            raise

    def save_image_with_thumbnail(
        self, image_data: bytes, generation_id: UUID, thumbnail_size: tuple = (300, 300)
    ) -> tuple[str, str]:
        """Save both full image and thumbnail. Returns (image_path, thumbnail_path)."""
        try:
            # Save full image
            image_path = self.save_image(image_data, generation_id)

            # Save thumbnail
            thumbnail_path = self.save_thumbnail(image_data, generation_id, thumbnail_size)

            logger.info(f"✓ Image and thumbnail saved for generation {generation_id}")
            return image_path, thumbnail_path

        except Exception as e:
            logger.error(f"✗ Failed to save image and thumbnail: {e}")
            raise

    def get_image_url(self, filepath: str) -> str:
        """Get image URL or path."""
        # For local storage, return the filepath
        # For cloud storage, this would return a URL
        return filepath

    def delete_image(self, filepath: str) -> bool:
        """Delete image file."""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"✓ Image deleted: {filepath}")
                return True
        except Exception as e:
            logger.error(f"✗ Failed to delete image: {e}")
        return False

    def image_exists(self, filepath: str) -> bool:
        """Check if image exists."""
        return os.path.exists(filepath) and os.path.isfile(filepath)
