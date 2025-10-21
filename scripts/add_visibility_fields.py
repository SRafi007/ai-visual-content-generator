"""
Migration script to add visibility and image URL fields to generation_history table.

Run this script to update your existing database schema:
    python scripts/add_visibility_fields.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from config.database import engine
from sqlalchemy import text
from src.utils.logger import get_logger

logger = get_logger(__name__)


def add_fields_to_generation_history():
    """Add new fields to generation_history table."""

    print(">> Adding new fields to generation_history table...")

    try:
        with engine.connect() as connection:
            # Start transaction
            trans = connection.begin()

            try:
                # Add generated_image_url column
                logger.info("Adding generated_image_url column...")
                connection.execute(text("""
                    ALTER TABLE generation_history
                    ADD COLUMN IF NOT EXISTS generated_image_url TEXT;
                """))
                print("[OK] Added generated_image_url column")

                # Add thumbnail_url column
                logger.info("Adding thumbnail_url column...")
                connection.execute(text("""
                    ALTER TABLE generation_history
                    ADD COLUMN IF NOT EXISTS thumbnail_url TEXT;
                """))
                print("[OK] Added thumbnail_url column")

                # Add visibility column with default 'private'
                logger.info("Adding visibility column...")
                connection.execute(text("""
                    ALTER TABLE generation_history
                    ADD COLUMN IF NOT EXISTS visibility VARCHAR(20) DEFAULT 'private';
                """))
                print("[OK] Added visibility column")

                # Create index on visibility for faster queries
                logger.info("Creating index on visibility...")
                connection.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_generation_history_visibility
                    ON generation_history(visibility);
                """))
                print("[OK] Created index on visibility")

                # Commit transaction
                trans.commit()
                print("\n[SUCCESS] Migration completed successfully!")

                # Show table info
                result = connection.execute(text("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = 'generation_history'
                    ORDER BY ordinal_position;
                """))

                print("\n[INFO] Current generation_history schema:")
                print("-" * 80)
                for row in result:
                    print(f"  {row[0]:<30} {row[1]:<15} NULL: {row[2]:<5} DEFAULT: {row[3]}")
                print("-" * 80)

            except Exception as e:
                trans.rollback()
                raise e

    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        print(f"\n[ERROR] Migration failed: {str(e)}")
        print("\nTroubleshooting:")
        print("  - Check your DATABASE_URL in .env")
        print("  - Ensure your database is accessible")
        print("  - Check the logs for more details")
        sys.exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Add visibility and image URL fields to generation_history table")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()

    print("=" * 80)
    print("Database Migration: Add Visibility and Image URL Fields")
    print("=" * 80)
    print()

    if args.yes:
        add_fields_to_generation_history()
    else:
        response = input("This will modify your database schema. Continue? (y/N): ")

        if response.lower() == 'y':
            add_fields_to_generation_history()
        else:
            print("[CANCELLED] Migration cancelled")
            sys.exit(0)
