"""Cleanup utility for maintenance tasks."""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.database import SessionLocal
from config.redis import get_redis
from src.models.database import GenerationHistory
from src.utils.logger import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def cleanup_old_sessions(days: int = 7):
    """Remove Redis sessions older than specified days."""
    try:
        redis = get_redis()
        logger.info(f"Cleaning sessions older than {days} days...")

        # Redis TTL handles this automatically
        # This is a placeholder for manual cleanup if needed

        logger.info("✓ Session cleanup complete")
        return True

    except Exception as e:
        logger.error(f"✗ Session cleanup failed: {e}")
        return False


def cleanup_old_images(days: int = 30):
    """Remove image files older than specified days."""
    try:
        from config.settings import get_settings

        settings = get_settings()

        logger.info(f"Cleaning images older than {days} days...")

        storage_path = Path(settings.STORAGE_PATH)
        cutoff_date = datetime.now() - timedelta(days=days)

        deleted_count = 0

        for img_file in storage_path.glob("*.png"):
            file_time = datetime.fromtimestamp(img_file.stat().st_mtime)

            if file_time < cutoff_date:
                img_file.unlink()
                deleted_count += 1

        logger.info(f"✓ Deleted {deleted_count} old images")
        return True

    except Exception as e:
        logger.error(f"✗ Image cleanup failed: {e}")
        return False


def cleanup_failed_generations():
    """Remove failed generation records older than 7 days."""
    try:
        db = SessionLocal()
        cutoff_date = datetime.utcnow() - timedelta(days=7)

        logger.info("Cleaning failed generations...")

        failed = (
            db.query(GenerationHistory)
            .filter(
                GenerationHistory.status == "failed",
                GenerationHistory.created_at < cutoff_date,
            )
            .all()
        )

        for gen in failed:
            db.delete(gen)

        db.commit()
        db.close()

        logger.info(f"✓ Deleted {len(failed)} failed generation records")
        return True

    except Exception as e:
        logger.error(f"✗ Failed generation cleanup failed: {e}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Cleanup utility")
    parser.add_argument("--sessions", action="store_true", help="Clean old sessions")
    parser.add_argument("--images", action="store_true", help="Clean old images")
    parser.add_argument(
        "--failed", action="store_true", help="Clean failed generations"
    )
    parser.add_argument("--all", action="store_true", help="Run all cleanup tasks")
    parser.add_argument("--days", type=int, default=30, help="Age threshold in days")

    args = parser.parse_args()

    if args.all:
        cleanup_old_sessions(7)
        cleanup_old_images(args.days)
        cleanup_failed_generations()
    else:
        if args.sessions:
            cleanup_old_sessions(7)
        if args.images:
            cleanup_old_images(args.days)
        if args.failed:
            cleanup_failed_generations()

        if not any([args.sessions, args.images, args.failed]):
            parser.print_help()
