# src/services/auth_service.py
from typing import Optional, Dict, Any
from google.oauth2 import id_token
from google.auth.transport import requests
import secrets
from datetime import datetime, timedelta

from src.utils.logger import get_logger
from src.services.user_service import UserService
from src.utils.password import verify_password

logger = get_logger(__name__)


class AuthService:
    """Google OAuth authentication service."""

    def __init__(self, user_service: UserService, google_client_id: str):
        self.user_service = user_service
        self.google_client_id = google_client_id
        self._sessions: Dict[str, Dict[str, Any]] = {}  # In-memory sessions (use Redis in production)

    def verify_google_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify Google OAuth token and extract user info.

        Returns user info dict with email, name, picture if valid.
        Returns None if invalid.
        """
        try:
            # Verify the token with Google
            idinfo = id_token.verify_oauth2_token(
                token, requests.Request(), self.google_client_id
            )

            # Token is valid, extract user info
            user_info = {
                "email": idinfo.get("email"),
                "name": idinfo.get("name"),
                "picture": idinfo.get("picture"),
                "google_id": idinfo.get("sub"),
            }

            logger.info(f"Google token verified for {user_info['email']}")
            return user_info

        except ValueError as e:
            # Invalid token
            logger.error(f"Invalid Google token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error verifying Google token: {e}")
            return None

    def authenticate_user(self, google_token: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user with Google token.

        Returns session info if user is authorized (exists in database).
        Returns None if user not authorized.
        """
        try:
            # Verify Google token
            google_user = self.verify_google_token(google_token)
            if not google_user:
                logger.warning("Google token verification failed")
                return None

            # Check if user exists in our database
            email = google_user["email"]
            user = self.user_service.get_user_by_email(email)

            if not user:
                logger.warning(f"Unauthorized access attempt by {email}")
                return None

            if not user.is_active:
                logger.warning(f"Inactive user attempted login: {email}")
                return None

            # Create session
            session_token = self._create_session(user.email, user.name, user.role)

            logger.info(f"User authenticated: {email} (role: {user.role})")

            return {
                "session_token": session_token,
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "name": user.name,
                    "role": user.role,
                    "team": user.team,
                    "picture": google_user.get("picture"),
                }
            }

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None

    def _create_session(self, email: str, name: str, role: str) -> str:
        """Create a new session and return session token."""
        session_token = secrets.token_urlsafe(32)

        self._sessions[session_token] = {
            "email": email,
            "name": name,
            "role": role,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=24),
        }

        return session_token

    def verify_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        Verify session token and return user info.

        Returns user info if session is valid.
        Returns None if session is invalid or expired.
        """
        session = self._sessions.get(session_token)

        if not session:
            return None

        # Check if session expired
        if datetime.utcnow() > session["expires_at"]:
            logger.info(f"Session expired for {session['email']}")
            del self._sessions[session_token]
            return None

        return session

    def logout(self, session_token: str) -> bool:
        """Logout user by invalidating session."""
        if session_token in self._sessions:
            email = self._sessions[session_token]["email"]
            del self._sessions[session_token]
            logger.info(f"User logged out: {email}")
            return True
        return False

    def is_admin(self, session_token: str) -> bool:
        """Check if session belongs to an admin user."""
        session = self.verify_session(session_token)
        return session is not None and session.get("role") == "admin"

    def refresh_session(self, session_token: str) -> Optional[str]:
        """Refresh session expiration time."""
        session = self._sessions.get(session_token)

        if not session:
            return None

        # Extend expiration
        session["expires_at"] = datetime.utcnow() + timedelta(hours=24)
        logger.info(f"Session refreshed for {session['email']}")

        return session_token

    def authenticate_with_password(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user with email and password.

        Returns session info if credentials are valid.
        Returns None if authentication fails.
        """
        try:
            # Get user from database
            user = self.user_service.get_user_by_email(email)

            if not user:
                logger.warning(f"Login attempt for non-existent user: {email}")
                return None

            if not user.is_active:
                logger.warning(f"Inactive user attempted login: {email}")
                return None

            # Get user model to access password hash
            from src.repositories.user_repository import UserRepository
            from config.database import SessionLocal

            db = SessionLocal()
            user_repo = UserRepository(db)
            user_model = user_repo.get_by_email(email)
            db.close()

            if not user_model:
                return None

            # Verify password
            if not verify_password(password, user_model.password):
                logger.warning(f"Invalid password attempt for user: {email}")
                return None

            # Create session
            session_token = self._create_session(user.email, user.name, user.role)

            logger.info(f"User authenticated with password: {email} (role: {user.role})")

            return {
                "session_token": session_token,
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "name": user.name,
                    "role": user.role,
                    "team": user.team,
                }
            }

        except Exception as e:
            logger.error(f"Password authentication error: {e}")
            return None

    def change_password_authenticated(self, session_token: str, current_password: str, new_password: str) -> bool:
        """
        Change password for authenticated user.

        Args:
            session_token: Valid session token
            current_password: Current password for verification
            new_password: New password to set

        Returns:
            True if password changed successfully, False otherwise
        """
        try:
            # Verify session
            session = self.verify_session(session_token)
            if not session:
                logger.warning("Invalid session for password change")
                return False

            # Use user service to change password
            return self.user_service.change_password(
                session["email"],
                current_password,
                new_password
            )

        except Exception as e:
            logger.error(f"Failed to change password via session: {e}")
            return False
