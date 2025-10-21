"""Test all services to verify they work correctly."""

import sys
from pathlib import Path
from uuid import UUID

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.database import SessionLocal
from config.redis import get_redis
from src.repositories.user_repository import UserRepository
from src.repositories.generation_repository import GenerationRepository
from src.services.user_service import UserService
from src.services.session_manager import SessionManager
from src.services.gemini_service import GeminiService
from src.services.storage_service import StorageService
from src.utils.logger import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def test_user_service():
    """Test user service operations."""
    try:
        logger.info("\n" + "=" * 60)
        logger.info("Testing UserService...")
        logger.info("=" * 60)

        db = SessionLocal()
        user_repo = UserRepository(db)
        user_service = UserService(user_repo)

        # Test 1: Get all users
        logger.info("Test 1: Get all users")
        users = user_service.get_all_users()
        logger.info(f"  Found {len(users)} users")
        for user in users:
            logger.info(f"    - {user.name} ({user.email}) - Team: {user.team}")

        if not users:
            logger.warning("  ⚠️ No users found. Run seed_users.py first.")
            return False

        # Test 2: Get user by email
        logger.info("\nTest 2: Get user by email")
        test_email = users[0].email
        user = user_service.get_user_by_email(test_email)
        if user:
            logger.info(f"  ✓ Found: {user.name}")
        else:
            logger.error(f"  ✗ User not found")
            return False

        # Test 3: Get user by ID
        logger.info("\nTest 3: Get user by ID")
        user_by_id = user_service.get_user_by_id(user.id)
        if user_by_id:
            logger.info(f"  ✓ Found: {user_by_id.name}")
        else:
            logger.error(f"  ✗ User not found")
            return False

        db.close()
        logger.info("\n✓ UserService: ALL TESTS PASSED")
        return True

    except Exception as e:
        logger.error(f"✗ UserService test failed: {e}")
        return False


def test_session_manager():
    """Test session manager operations."""
    try:
        logger.info("\n" + "=" * 60)
        logger.info("Testing SessionManager...")
        logger.info("=" * 60)

        redis = get_redis()
        session_manager = SessionManager(redis)

        test_email = "test@arborai.com"
        test_project = "Test Project"

        # Test 1: Create new session
        logger.info("Test 1: Create new session")
        session = session_manager.get_or_create_session(test_email, test_project)
        logger.info(f"  ✓ Session created: {session['conversation_id']}")
        logger.info(f"    Messages: {len(session['messages'])}")

        # Test 2: Update messages
        logger.info("\nTest 2: Update conversation messages")
        test_messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi! How can I help you?"},
        ]
        session_manager.update_messages(test_email, test_project, test_messages)

        # Verify update
        updated_session = session_manager.get_or_create_session(
            test_email, test_project
        )
        if len(updated_session["messages"]) == 2:
            logger.info(f"  ✓ Messages updated successfully")
            logger.info(f"    Message 1: {updated_session['messages'][0]['content']}")
            logger.info(f"    Message 2: {updated_session['messages'][1]['content']}")
        else:
            logger.error(f"  ✗ Message update failed")
            return False

        # Test 3: Add project to user's list
        logger.info("\nTest 3: Add project to user's list")
        session_manager.add_project(test_email, test_project)
        projects = session_manager.get_user_projects(test_email)
        if test_project in projects:
            logger.info(f"  ✓ Project added successfully")
            logger.info(f"    User projects: {projects}")
        else:
            logger.error(f"  ✗ Project not found in list")
            return False

        # Test 4: Clear session
        logger.info("\nTest 4: Clear session")
        session_manager.clear_session(test_email, test_project)
        logger.info(f"  ✓ Session cleared")

        logger.info("\n✓ SessionManager: ALL TESTS PASSED")
        return True

    except Exception as e:
        logger.error(f"✗ SessionManager test failed: {e}")
        return False


def test_gemini_service():
    """Test Gemini service operations."""
    try:
        logger.info("\n" + "=" * 60)
        logger.info("Testing GeminiService...")
        logger.info("=" * 60)

        gemini_service = GeminiService()

        # Test 1: Simple message
        logger.info("Test 1: Send simple message")
        conversation_history = []
        response = gemini_service.send_message(
            conversation_history, "Say 'Hello' in exactly one word."
        )
        logger.info(f"  ✓ Response received: {response[:100]}")

        # Test 2: Conversation with context
        logger.info("\nTest 2: Conversation with context")
        conversation_history = [
            {"role": "user", "content": "My favorite color is blue."},
            {"role": "assistant", "content": "That's great! Blue is a calming color."},
        ]
        response = gemini_service.send_message(
            conversation_history, "What was my favorite color?"
        )
        logger.info(f"  ✓ Response with context: {response[:100]}")
        if "blue" in response.lower():
            logger.info(f"    ✓ Context maintained correctly")
        else:
            logger.warning(f"    ⚠️ Context may not be maintained")

        # Test 3: Prompt refinement
        logger.info("\nTest 3: Prompt refinement")
        raw_input = "product photo of a smartwatch"
        parameters = {
            "style": "photorealistic",
            "lighting": "studio",
            "background": "solid white",
        }
        refined_prompt = gemini_service.refine_prompt(raw_input, parameters)
        logger.info(f"  ✓ Refined prompt generated:")
        logger.info(f"    {refined_prompt[:200]}...")

        logger.info("\n✓ GeminiService: ALL TESTS PASSED")
        return True

    except Exception as e:
        logger.error(f"✗ GeminiService test failed: {e}")
        logger.info(f"  Make sure GEMINI_API_KEY is set correctly in .env")
        return False


def test_storage_service():
    """Test storage service operations."""
    try:
        logger.info("\n" + "=" * 60)
        logger.info("Testing StorageService...")
        logger.info("=" * 60)

        from PIL import Image
        from io import BytesIO
        from uuid import uuid4

        storage_service = StorageService()
        test_id = uuid4()

        # Create test image
        logger.info("Creating test image...")
        img = Image.new("RGB", (512, 512), color="red")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        image_data = buffer.getvalue()

        # Test 1: Save image
        logger.info("\nTest 1: Save image")
        filepath = storage_service.save_image(image_data, test_id)
        logger.info(f"  ✓ Image saved: {filepath}")

        # Verify file exists
        if Path(filepath).exists():
            logger.info(f"    ✓ File exists on disk")
            file_size = Path(filepath).stat().st_size
            logger.info(f"    File size: {file_size} bytes")
        else:
            logger.error(f"    ✗ File not found on disk")
            return False

        # Test 2: Create thumbnail
        logger.info("\nTest 2: Create thumbnail")
        thumb_path = storage_service.save_thumbnail(image_data, test_id)
        logger.info(f"  ✓ Thumbnail created: {thumb_path}")

        # Verify thumbnail
        if Path(thumb_path).exists():
            logger.info(f"    ✓ Thumbnail exists on disk")
            thumb_size = Path(thumb_path).stat().st_size
            logger.info(f"    Thumbnail size: {thumb_size} bytes")
        else:
            logger.error(f"    ✗ Thumbnail not found")
            return False

        # Test 3: Get image URL
        logger.info("\nTest 3: Get image URL")
        url = storage_service.get_image_url(filepath)
        logger.info(f"  ✓ Image URL: {url}")

        # Test 4: Delete test files
        logger.info("\nTest 4: Cleanup test files")
        storage_service.delete_image(filepath)
        storage_service.delete_image(thumb_path)
        logger.info(f"  ✓ Test files cleaned up")

        logger.info("\n✓ StorageService: ALL TESTS PASSED")
        return True

    except Exception as e:
        logger.error(f"✗ StorageService test failed: {e}")
        return False


def test_generation_repository():
    """Test generation repository operations."""
    try:
        logger.info("\n" + "=" * 60)
        logger.info("Testing GenerationRepository...")
        logger.info("=" * 60)

        db = SessionLocal()
        gen_repo = GenerationRepository(db)
        user_repo = UserRepository(db)

        # Get a test user
        users = user_repo.get_all_active()
        if not users:
            logger.warning("  ⚠️ No users found for testing")
            return False

        test_user = users[0]

        # Test 1: Create generation
        logger.info("Test 1: Create generation record")
        gen_data = {
            "user_id": test_user.id,
            "project_name": "Test Project",
            "conversation_messages": [
                {"role": "user", "content": "Create a test image"},
                {"role": "assistant", "content": "I'll help you create that."},
            ],
            "final_prompt": "Test prompt for image generation",
            "raw_user_input": "Create a test image",
            "selected_parameters": {"style": "test", "quality": "high"},
            "status": "drafting",
        }
        generation = gen_repo.create(gen_data)
        logger.info(f"  ✓ Generation created: {generation.id}")
        logger.info(f"    Project: {generation.project_name}")
        logger.info(f"    Status: {generation.status}")

        # Test 2: Get by user
        logger.info("\nTest 2: Get generations by user")
        user_gens = gen_repo.get_by_user(test_user.id, limit=5)
        logger.info(f"  ✓ Found {len(user_gens)} generations for user")

        # Test 3: Get user projects
        logger.info("\nTest 3: Get user's projects")
        projects = gen_repo.get_user_projects(test_user.id)
        logger.info(f"  ✓ User has {len(projects)} projects:")
        for project in projects:
            logger.info(f"    - {project}")

        # Test 4: Update generation
        logger.info("\nTest 4: Update generation status")
        gen_repo.update(generation.id, {"status": "completed"})
        updated = gen_repo.get_by_id(generation.id)
        logger.info(f"  ✓ Status updated: {updated.status}")

        # Test 5: Delete generation
        logger.info("\nTest 5: Delete test generation")
        gen_repo.delete(generation.id)
        logger.info(f"  ✓ Test generation deleted")

        db.close()
        logger.info("\n✓ GenerationRepository: ALL TESTS PASSED")
        return True

    except Exception as e:
        logger.error(f"✗ GenerationRepository test failed: {e}")
        return False


def run_all_tests():
    """Run all service tests."""
    logger.info("\n" + "=" * 60)
    logger.info("SERVICE TESTS")
    logger.info("=" * 60)

    results = {
        "UserService": test_user_service(),
        "SessionManager": test_session_manager(),
        "GeminiService": test_gemini_service(),
        "StorageService": test_storage_service(),
        "GenerationRepository": test_generation_repository(),
    }

    logger.info("\n" + "=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)

    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{name:25} {status}")

    all_passed = all(results.values())

    if all_passed:
        logger.info("\n✓ All service tests passed! Ready for UI development.")
    else:
        logger.warning("\n⚠️ Some tests failed. Check logs above.")

    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
