"""Seed users from team_members.yaml."""

import sys
from pathlib import Path
import yaml

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.database import SessionLocal
from src.repositories.user_repository import UserRepository
from src.utils.logger import setup_logging, get_logger
from src.utils.password import hash_password

setup_logging()
logger = get_logger(__name__)


def load_team_members():
    """Load team members from YAML file."""
    config_path = Path(__file__).parent.parent / "config" / "team_members.yaml"

    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
            return config.get("team_members", [])
    except FileNotFoundError:
        logger.error(f"✗ Config file not found: {config_path}")
        return []
    except Exception as e:
        logger.error(f"✗ Failed to load config: {e}")
        return []


def seed_users():
    """Seed users into database."""
    db = SessionLocal()
    user_repo = UserRepository(db)

    team_members = load_team_members()

    if not team_members:
        logger.error("✗ No team members found in config")
        return

    logger.info(f"Seeding {len(team_members)} users...")

    created_count = 0
    skipped_count = 0

    for member in team_members:
        try:
            existing = user_repo.get_by_email(member["email"])

            if existing:
                logger.info(
                    f"⏭  User exists: {member['name']} ({member['email']})"
                )
                skipped_count += 1
            else:
                # Hash password before storing
                plain_password = member.get("password", "arbor2024")  # Default password if not provided
                hashed_password = hash_password(plain_password)

                user_repo.create(
                    {
                        "email": member["email"],
                        "name": member["name"],
                        "password": hashed_password,
                        "role": member.get("role", "user"),
                        "team": member.get("team"),
                    }
                )
                logger.info(
                    f"✓ Created user: {member['name']} ({member['email']}) - Role: {member.get('role', 'user')}"
                )
                created_count += 1

        except Exception as e:
            logger.error(f"✗ Failed to create user {member['email']}: {e}")

    db.close()

    logger.info(f"\nSummary: {created_count} created, {skipped_count} skipped")


if __name__ == "__main__":
    seed_users()
