"""Initialize database tables."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.database import engine, Base
# Import models to register them with SQLAlchemy Base
from src.models.database import User, GenerationHistory, Content  # noqa: F401
from src.utils.logger import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def init_database():
    """Create all database tables."""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✓ Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to create tables: {e}")
        return False


def drop_all_tables():
    """Drop all tables (use with caution)."""
    try:
        logger.warning("Dropping all database tables...")
        Base.metadata.drop_all(bind=engine)
        logger.info("✓ All tables dropped")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to drop tables: {e}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Database initialization")
    parser.add_argument("--reset", action="store_true", help="Drop and recreate tables")
    args = parser.parse_args()

    if args.reset:
        print("WARNING: This will delete all data!")
        confirm = input("Type 'yes' to continue: ")
        if confirm.lower() == "yes":
            drop_all_tables()
            init_database()
        else:
            print("Cancelled")
    else:
        init_database()
