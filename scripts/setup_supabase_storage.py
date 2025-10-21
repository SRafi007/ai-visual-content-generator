"""
Setup script for Supabase Storage bucket.

This script creates the required bucket and folder structure in Supabase Storage.
Run this once after setting up your Supabase project.

Usage:
    python scripts/setup_supabase_storage.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from config.settings import get_settings
from src.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


def setup_storage():
    """Setup Supabase Storage bucket and folder structure."""
    try:
        from supabase import create_client

        # Initialize Supabase client
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)

        bucket_name = settings.SUPABASE_BUCKET_NAME

        logger.info(f"Setting up Supabase Storage bucket: {bucket_name}")

        # Try to create bucket (will fail if already exists, which is fine)
        try:
            supabase.storage.create_bucket(
                bucket_name,
                options={"public": True}  # Make bucket public for CDN access
            )
            logger.info(f"✓ Created bucket: {bucket_name}")
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.info(f"✓ Bucket already exists: {bucket_name}")
            else:
                logger.error(f"✗ Failed to create bucket: {e}")
                raise

        # Create folder structure by uploading placeholder files
        # (Supabase doesn't have explicit folders, they're created via file paths)
        folders = ["images", "thumbnails"]

        for folder in folders:
            try:
                # Upload a .gitkeep file to create the folder
                placeholder_content = b"# This file ensures the folder exists"
                path = f"{folder}/.gitkeep"

                supabase.storage.from_(bucket_name).upload(
                    path=path,
                    file=placeholder_content,
                    file_options={"content-type": "text/plain", "upsert": "true"}
                )
                logger.info(f"✓ Created folder: {folder}/")
            except Exception as e:
                logger.warning(f"Could not create folder {folder}: {e}")

        logger.info("\n" + "="*60)
        logger.info("✓ Supabase Storage setup complete!")
        logger.info("="*60)
        logger.info(f"\nBucket: {bucket_name}")
        logger.info(f"URL: {settings.SUPABASE_URL}")
        logger.info("\nFolder structure:")
        logger.info("  - images/")
        logger.info("  - thumbnails/")
        logger.info("\nYou can now use STORAGE_TYPE=supabase in your .env file")

    except ImportError:
        logger.error("✗ Supabase package not installed. Run: pip install supabase")
        sys.exit(1)
    except Exception as e:
        logger.error(f"✗ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    logger.info("Starting Supabase Storage setup...")

    # Verify environment variables
    if not settings.SUPABASE_URL:
        logger.error("✗ SUPABASE_URL not set in .env file")
        sys.exit(1)

    if not settings.SUPABASE_ANON_KEY:
        logger.error("✗ SUPABASE_ANON_KEY not set in .env file")
        sys.exit(1)

    setup_storage()
