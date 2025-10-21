"""File storage service with Supabase Storage support."""

import os
from pathlib import Path
from uuid import UUID
from PIL import Image
from io import BytesIO
from typing import Optional

from config.settings import get_settings
from src.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


class StorageService:
    """File storage service supporting both local and Supabase storage."""

    def __init__(self):
        self.storage_type = settings.STORAGE_TYPE
        self.storage_path = Path(settings.STORAGE_PATH)

        # Initialize local storage directories (fallback)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.thumbnail_path = self.storage_path / "thumbnails"
        self.thumbnail_path.mkdir(exist_ok=True)

        # Initialize Supabase client if using supabase storage
        self.supabase_client = None
        if self.storage_type == "supabase":
            try:
                from supabase import create_client, Client
                self.supabase_client: Client = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_ANON_KEY
                )
                logger.info(f"✓ Supabase Storage initialized (bucket: {settings.SUPABASE_BUCKET_NAME})")
            except Exception as e:
                logger.error(f"✗ Failed to initialize Supabase client: {e}")
                logger.warning("Falling back to local storage")
                self.storage_type = "local"

        logger.info(f"Storage initialized: {self.storage_type} at {self.storage_path}")

    def save_image(self, image_data: bytes, generation_id: UUID) -> str:
        """Save generated image. Returns URL (Supabase) or path (local)."""
        try:
            filename = f"{generation_id}.png"

            if self.storage_type == "supabase" and self.supabase_client:
                return self._save_to_supabase(image_data, filename, "images")
            else:
                return self._save_to_local(image_data, filename, self.storage_path)

        except Exception as e:
            logger.error(f"✗ Failed to save image: {e}")
            raise

    def save_thumbnail(
        self, image_data: bytes, generation_id: UUID, size: tuple = (300, 300)
    ) -> str:
        """Create and save thumbnail. Returns URL (Supabase) or path (local)."""
        try:
            # Create thumbnail from image data
            img_buffer = BytesIO(image_data)
            img = Image.open(img_buffer)

            # Convert to RGB if necessary
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')

            # Create thumbnail (maintains aspect ratio)
            img.thumbnail(size, Image.Resampling.LANCZOS)

            # Save to bytes
            thumb_buffer = BytesIO()
            img.save(thumb_buffer, "PNG")
            thumb_data = thumb_buffer.getvalue()

            filename = f"{generation_id}_thumb.png"

            if self.storage_type == "supabase" and self.supabase_client:
                return self._save_to_supabase(thumb_data, filename, "thumbnails")
            else:
                filepath = self.thumbnail_path / filename
                with open(filepath, "wb") as f:
                    f.write(thumb_data)
                logger.info(f"✓ Thumbnail saved locally: {filepath}")
                return str(filepath)

        except Exception as e:
            logger.error(f"✗ Failed to save thumbnail: {e}")
            raise

    def save_image_with_thumbnail(
        self, image_data: bytes, generation_id: UUID, thumbnail_size: tuple = (300, 300)
    ) -> tuple[str, str]:
        """Save both full image and thumbnail. Returns (image_url, thumbnail_url)."""
        try:
            # Save full image
            image_url = self.save_image(image_data, generation_id)

            # Save thumbnail
            thumbnail_url = self.save_thumbnail(image_data, generation_id, thumbnail_size)

            logger.info(f"✓ Image and thumbnail saved for generation {generation_id}")
            return image_url, thumbnail_url

        except Exception as e:
            logger.error(f"✗ Failed to save image and thumbnail: {e}")
            raise

    def get_image_url(self, filepath: str) -> str:
        """Get image URL or path."""
        # If it's already a URL (starts with http), return as-is
        if filepath.startswith("http"):
            return filepath
        # For local storage, return the filepath
        return filepath

    def delete_image(self, filepath_or_url: str) -> bool:
        """Delete image file from local or Supabase storage."""
        try:
            if filepath_or_url.startswith("http") and self.storage_type == "supabase":
                # Extract filename from URL and delete from Supabase
                filename = filepath_or_url.split("/")[-1]
                folder = "thumbnails" if "thumb" in filename else "images"
                return self._delete_from_supabase(filename, folder)
            else:
                # Delete from local filesystem
                if os.path.exists(filepath_or_url):
                    os.remove(filepath_or_url)
                    logger.info(f"✓ Image deleted: {filepath_or_url}")
                    return True
        except Exception as e:
            logger.error(f"✗ Failed to delete image: {e}")
        return False

    def image_exists(self, filepath_or_url: str) -> bool:
        """Check if image exists."""
        if filepath_or_url.startswith("http"):
            # For URLs, assume they exist (checking would require extra API call)
            return True
        return os.path.exists(filepath_or_url) and os.path.isfile(filepath_or_url)

    # Private helper methods

    def _save_to_local(self, data: bytes, filename: str, directory: Path) -> str:
        """Save file to local filesystem."""
        filepath = directory / filename
        with open(filepath, "wb") as f:
            f.write(data)
        logger.info(f"✓ File saved locally: {filepath}")
        return str(filepath)

    def _save_to_supabase(self, data: bytes, filename: str, folder: str) -> str:
        """Save file to Supabase Storage. Returns public URL."""
        try:
            path = f"{folder}/{filename}"

            # Upload to Supabase Storage
            self.supabase_client.storage.from_(settings.SUPABASE_BUCKET_NAME).upload(
                path=path,
                file=data,
                file_options={"content-type": "image/png", "upsert": "true"}
            )

            # Get public URL
            public_url = self.supabase_client.storage.from_(settings.SUPABASE_BUCKET_NAME).get_public_url(path)

            logger.info(f"✓ File uploaded to Supabase: {path}")
            return public_url

        except Exception as e:
            logger.error(f"✗ Failed to upload to Supabase: {e}")
            # Fallback to local storage
            logger.warning("Falling back to local storage")
            return self._save_to_local(data, filename, self.storage_path)

    def _delete_from_supabase(self, filename: str, folder: str) -> bool:
        """Delete file from Supabase Storage."""
        try:
            path = f"{folder}/{filename}"
            self.supabase_client.storage.from_(settings.SUPABASE_BUCKET_NAME).remove([path])
            logger.info(f"✓ File deleted from Supabase: {path}")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to delete from Supabase: {e}")
            return False
