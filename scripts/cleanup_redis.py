"""
Redis Cleanup Script

Manually clean up Redis cache to fix slow sign-in issues.
Run this periodically or when experiencing performance issues.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from config.redis import get_redis
from src.services.session_manager import SessionManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


def cleanup_all_sessions():
    """Clean up all Redis sessions."""
    try:
        redis_client = get_redis()
        session_manager = SessionManager(redis_client)

        # Get all session keys
        all_keys = session_manager.get_all_session_keys()
        logger.info(f"Found {len(all_keys)} session keys in Redis")

        if not all_keys:
            print("✅ Redis is already clean - no sessions found")
            return

        # Clean up old sessions (older than 24 hours)
        logger.info("Cleaning up sessions older than 24 hours...")
        session_manager.cleanup_old_sessions(max_age_hours=24)

        # Check remaining
        remaining_keys = session_manager.get_all_session_keys()
        removed_count = len(all_keys) - len(remaining_keys)

        print(f"✅ Cleanup complete!")
        print(f"   - Removed: {removed_count} old sessions")
        print(f"   - Remaining: {len(remaining_keys)} active sessions")

        if remaining_keys:
            print("\nActive sessions:")
            for key in remaining_keys:
                print(f"   - {key}")

    except Exception as e:
        logger.error(f"Redis cleanup failed: {e}")
        print(f"❌ Error: {e}")


def cleanup_specific_user(email: str):
    """Clean up Redis cache for a specific user."""
    try:
        redis_client = get_redis()
        session_manager = SessionManager(redis_client)

        print(f"Cleaning up session for: {email}")
        session_manager.cleanup_all_user_data(email)

        print(f"✅ Session cleared for {email}")

    except Exception as e:
        logger.error(f"User cleanup failed: {e}")
        print(f"❌ Error: {e}")


def flush_all_redis():
    """DANGER: Flush all Redis data (use with caution!)"""
    try:
        redis_client = get_redis()

        confirm = input("⚠️  WARNING: This will delete ALL Redis data. Type 'YES' to confirm: ")

        if confirm == "YES":
            redis_client.client.flushall()
            print("✅ All Redis data has been flushed")
        else:
            print("❌ Operation cancelled")

    except Exception as e:
        logger.error(f"Redis flush failed: {e}")
        print(f"❌ Error: {e}")


def main():
    """Main cleanup script."""
    print("=" * 60)
    print("Redis Cleanup Utility")
    print("=" * 60)
    print()
    print("Options:")
    print("1. Clean up old sessions (>24 hours)")
    print("2. Clean up specific user session")
    print("3. Flush ALL Redis data (DANGER!)")
    print("4. Exit")
    print()

    choice = input("Select option (1-4): ").strip()

    if choice == "1":
        cleanup_all_sessions()
    elif choice == "2":
        email = input("Enter user email: ").strip()
        if email:
            cleanup_specific_user(email)
        else:
            print("❌ No email provided")
    elif choice == "3":
        flush_all_redis()
    elif choice == "4":
        print("Exiting...")
    else:
        print("❌ Invalid option")


if __name__ == "__main__":
    main()
