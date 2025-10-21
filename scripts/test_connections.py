# scripts\test_connections.py
"""Test database and Redis connections."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from config.database import engine, SessionLocal
from config.redis import get_redis
from config.settings import get_settings
from src.utils.logger import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)
settings = get_settings()


def test_database_connection():
    """Test PostgreSQL connection."""
    try:
        logger.info("Testing database connection...")

        # Try to connect
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()

        logger.info(f"✓ Database connection successful")
        logger.info(f"  URL: {settings.DATABASE_URL.split('@')[1]}")  # Hide credentials
        return True

    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        return False


def test_redis_connection():
    """Test Redis connection."""
    try:
        logger.info("Testing Redis connection...")

        redis = get_redis()

        # Test write
        test_key = "test_connection"
        test_value = {"status": "ok"}
        redis.set(test_key, test_value, ttl=10)

        # Test read
        result = redis.get(test_key)

        if result and result.get("status") == "ok":
            logger.info(f"✓ Redis connection successful")
            logger.info(f"  URL: {settings.REDIS_URL}")

            # Cleanup
            redis.delete(test_key)
            return True
        else:
            logger.error("✗ Redis read/write test failed")
            return False

    except Exception as e:
        logger.error(f"✗ Redis connection failed: {e}")
        return False


def test_gemini_api():
    """Test Gemini API key."""
    try:
        logger.info("Testing Gemini API...")

        import google.generativeai as genai

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(settings.GEMINI_MODEL)

        # Simple test
        response = model.generate_content("Say 'OK' if you can hear me")

        if response.text:
            logger.info(f"✓ Gemini API working")
            logger.info(f"  Model: {settings.GEMINI_MODEL}")
            return True
        else:
            logger.error("✗ Gemini API returned empty response")
            return False

    except Exception as e:
        logger.error(f"✗ Gemini API test failed: {e}")
        logger.info("  Check your GEMINI_API_KEY in .env")
        return False


def test_storage_directories():
    """Test storage directories exist and are writable."""
    try:
        logger.info("Testing storage directories...")

        storage_path = Path(settings.STORAGE_PATH)
        storage_path.mkdir(parents=True, exist_ok=True)

        thumbnail_path = storage_path / "thumbnails"
        thumbnail_path.mkdir(exist_ok=True)

        # Test write
        test_file = storage_path / ".test"
        test_file.write_text("test")
        test_file.unlink()

        logger.info(f"✓ Storage directories ready")
        logger.info(f"  Path: {storage_path}")
        return True

    except Exception as e:
        logger.error(f"✗ Storage test failed: {e}")
        return False


def run_all_tests():
    """Run all connection tests."""
    logger.info("=" * 60)
    logger.info("CONNECTION TESTS")
    logger.info("=" * 60)

    results = {
        "Database": test_database_connection(),
        "Redis": test_redis_connection(),
        "Gemini API": test_gemini_api(),
        "Storage": test_storage_directories(),
    }

    logger.info("\n" + "=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)

    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{name:20} {status}")

    all_passed = all(results.values())

    if all_passed:
        logger.info("\n✓ All tests passed! System is ready.")
    else:
        logger.warning("\n⚠ Some tests failed. Check configuration.")

    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
