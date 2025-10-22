"""
Test script to verify Supabase Storage upload.
"""

import sys
from pathlib import Path
from io import BytesIO
from PIL import Image

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from config.settings import get_settings
from src.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


def test_upload():
    """Test uploading to Supabase Storage."""
    try:
        from supabase import create_client

        # Initialize Supabase client
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)

        bucket_name = settings.SUPABASE_BUCKET_NAME

        logger.info(f"Testing Supabase Storage upload to bucket: {bucket_name}")

        # Create a test image
        img = Image.new('RGB', (100, 100), color='red')
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        test_image_data = buffer.getvalue()

        # Try to upload
        path = "test/test_image.png"

        logger.info(f"Uploading test image to: {path}")

        result = supabase.storage.from_(bucket_name).upload(
            path=path,
            file=test_image_data,
            file_options={"content-type": "image/png", "upsert": "true"}
        )

        logger.info(f"Upload result: {result}")

        # Get public URL
        public_url = supabase.storage.from_(bucket_name).get_public_url(path)
        logger.info(f"Public URL: {public_url}")

        print("\n" + "="*60)
        print("SUCCESS! Upload test passed")
        print("="*60)
        print(f"Bucket: {bucket_name}")
        print(f"Path: {path}")
        print(f"URL: {public_url}")
        print("\nTest the URL in your browser to verify the image is accessible.")

        # Cleanup
        logger.info("Cleaning up test file...")
        supabase.storage.from_(bucket_name).remove([path])
        logger.info("Test file removed")

    except ImportError:
        logger.error("Supabase package not installed. Run: pip install supabase")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Upload test failed: {e}")
        print("\n" + "="*60)
        print("FAILED! Upload test did not pass")
        print("="*60)
        print(f"Error: {e}")
        print("\nPossible issues:")
        print("1. Bucket 'arbor_images' doesn't exist - create it in Supabase Dashboard")
        print("2. Bucket is not public - enable public access in Supabase Dashboard")
        print("3. RLS policies are blocking - check Storage policies")
        print("4. SUPABASE_ANON_KEY is incorrect")
        sys.exit(1)


if __name__ == "__main__":
    logger.info("Starting Supabase Storage upload test...")

    # Verify environment variables
    if not settings.SUPABASE_URL:
        logger.error("SUPABASE_URL not set in .env file")
        sys.exit(1)

    if not settings.SUPABASE_ANON_KEY:
        logger.error("SUPABASE_ANON_KEY not set in .env file")
        sys.exit(1)

    test_upload()
