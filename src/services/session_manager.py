# src\services\session_manager.py
from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import uuid4

from config.redis import RedisClient
from src.models.schemas.generation import Message


class SessionManager:
    """Manages user sessions and conversation context with schema support."""

    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client

    def get_or_create_session(self, user_email: str) -> Dict:
        """Get existing session or create new one for user."""
        key = f"session:{user_email}"
        session = self.redis.get(key)

        if session:
            session["last_active"] = datetime.utcnow().isoformat()
            self.redis.set(key, session)
            return session

        new_session = {
            "conversation_id": str(uuid4()),
            "messages": [],
            "prompt_state": None,  # For storing current prompt being built
            "created_at": datetime.utcnow().isoformat(),
            "last_active": datetime.utcnow().isoformat(),
        }
        self.redis.set(key, new_session)
        return new_session

    def update_messages(self, user_email: str, messages: List[Dict]):
        """Update conversation messages (accepts dicts from serialized schemas)."""
        key = f"session:{user_email}"
        session = self.redis.get(key)

        if session:
            session["messages"] = messages
            session["last_active"] = datetime.utcnow().isoformat()
            self.redis.set(key, session)

    def get_messages_as_schemas(self, user_email: str) -> List[Message]:
        """Get conversation messages as Message schemas."""
        key = f"session:{user_email}"
        session = self.redis.get(key)

        if session and session.get("messages"):
            try:
                return [Message(**msg) for msg in session["messages"]]
            except Exception:
                return []
        return []

    def clear_session(self, user_email: str):
        """Clear session data for user."""
        key = f"session:{user_email}"
        self.redis.delete(key)

    def update_prompt_state(self, user_email: str, prompt_state: Dict):
        """Update the current prompt state for user."""
        key = f"session:{user_email}"
        session = self.redis.get(key)

        if session:
            session["prompt_state"] = prompt_state
            session["last_active"] = datetime.utcnow().isoformat()
            self.redis.set(key, session)

    def get_prompt_state(self, user_email: str) -> Optional[Dict]:
        """Get the current prompt state for user."""
        key = f"session:{user_email}"
        session = self.redis.get(key)

        if session:
            return session.get("prompt_state")
        return None

    def clear_prompt_state(self, user_email: str):
        """Clear only the prompt state, keeping conversation history."""
        key = f"session:{user_email}"
        session = self.redis.get(key)

        if session:
            session["prompt_state"] = None
            session["last_active"] = datetime.utcnow().isoformat()
            self.redis.set(key, session)

    def clear_all_messages(self, user_email: str):
        """Clear all conversation messages for user."""
        key = f"session:{user_email}"
        session = self.redis.get(key)

        if session:
            session["messages"] = []
            session["prompt_state"] = None
            session["last_active"] = datetime.utcnow().isoformat()
            self.redis.set(key, session)

    def cleanup_all_user_data(self, user_email: str):
        """Complete cleanup of all user session data from Redis."""
        patterns = [
            f"session:{user_email}",
            f"prompt:{user_email}:*",
            f"chat:{user_email}:*",
            f"user:{user_email}:*"
        ]

        # Delete all keys matching patterns
        for pattern in patterns:
            if "*" in pattern:
                # Scan for keys matching pattern
                try:
                    keys = self.redis.client.keys(pattern)
                    if keys:
                        self.redis.client.delete(*keys)
                except Exception:
                    pass
            else:
                self.redis.delete(pattern)

    def get_all_session_keys(self) -> list:
        """Get all session keys (for debugging/cleanup)."""
        try:
            return self.redis.client.keys("session:*")
        except Exception:
            return []

    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Clean up sessions older than max_age_hours."""
        try:
            session_keys = self.redis.client.keys("session:*")
            now = datetime.utcnow()

            for key in session_keys:
                session = self.redis.get(key)
                if session and "last_active" in session:
                    try:
                        last_active = datetime.fromisoformat(session["last_active"])
                        age_hours = (now - last_active).total_seconds() / 3600

                        if age_hours > max_age_hours:
                            self.redis.delete(key)
                    except Exception:
                        # If we can't parse date, delete it
                        self.redis.delete(key)
        except Exception as e:
            # Log but don't fail
            pass
