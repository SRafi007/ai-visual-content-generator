# src/middleware/auth_middleware.py
from functools import wraps
from typing import Optional, Callable, Any
import streamlit as st

from src.utils.logger import get_logger

logger = get_logger(__name__)


def require_auth(func: Callable) -> Callable:
    """
    Decorator to require authentication for a page.

    Usage:
        @require_auth
        def my_page():
            st.title("Protected Page")
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Check if user is authenticated
        if "authenticated" not in st.session_state or not st.session_state.authenticated:
            st.error("⚠️ Please sign in to access this page")
            st.stop()
            return None

        if "user" not in st.session_state:
            st.error("⚠️ Session expired. Please sign in again")
            st.stop()
            return None

        return func(*args, **kwargs)

    return wrapper


def require_admin(func: Callable) -> Callable:
    """
    Decorator to require admin role for a page.

    Usage:
        @require_admin
        def admin_page():
            st.title("Admin Only")
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Check authentication first
        if "authenticated" not in st.session_state or not st.session_state.authenticated:
            st.error("⚠️ Please sign in to access this page")
            st.stop()
            return None

        if "user" not in st.session_state:
            st.error("⚠️ Session expired. Please sign in again")
            st.stop()
            return None

        # Check admin role
        user = st.session_state.user
        if user.get("role") != "admin":
            st.error("⚠️ Admin access required")
            logger.warning(f"Unauthorized admin access attempt by {user.get('email')}")
            st.stop()
            return None

        return func(*args, **kwargs)

    return wrapper


def get_current_user() -> Optional[dict]:
    """Get currently authenticated user from session."""
    if "user" in st.session_state and st.session_state.get("authenticated"):
        return st.session_state.user
    return None


def is_authenticated() -> bool:
    """Check if user is authenticated."""
    return st.session_state.get("authenticated", False)


def is_admin() -> bool:
    """Check if current user is admin."""
    user = get_current_user()
    return user is not None and user.get("role") == "admin"
