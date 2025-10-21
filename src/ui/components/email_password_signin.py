"""Email/Password sign-in component."""

import streamlit as st
from src.services.auth_service import AuthService
from src.services.user_service import UserService
from src.utils.logger import get_logger

logger = get_logger(__name__)


def render_email_password_signin(user_service: UserService, auth_service: AuthService) -> bool:
    """
    Render email/password sign-in form.

    Args:
        user_service: UserService instance
        auth_service: AuthService instance

    Returns:
        True if authentication successful, False otherwise
    """
    st.markdown("#### Sign in with Email & Password")

    with st.form("email_password_signin", clear_on_submit=False):
        email = st.text_input(
            "Email",
            placeholder="your.email@arboraistudio.com",
            help="Enter your registered email address"
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
            help="Default password: arbor2024"
        )

        col1, col2 = st.columns([1, 1])

        with col1:
            submit_button = st.form_submit_button(
                "Sign In",
                use_container_width=True,
                type="primary"
            )

        with col2:
            forgot_password = st.form_submit_button(
                "Forgot Password?",
                use_container_width=True
            )

        if submit_button:
            if not email or not password:
                st.error("Please enter both email and password")
                return False

            # Show loading spinner
            with st.spinner("🔐 Signing in..."):
                try:
                    # Authenticate with password
                    auth_result = auth_service.authenticate_with_password(email, password)

                    if auth_result:
                        # Clear old Redis sessions before signing in
                        try:
                            from config.redis import get_redis
                            from src.services.session_manager import SessionManager

                            redis_client = get_redis()
                            session_manager = SessionManager(redis_client)

                            # Clean up old sessions (older than 24 hours)
                            session_manager.cleanup_old_sessions(max_age_hours=24)

                            # Clear any existing session for this user
                            session_manager.cleanup_all_user_data(email)
                        except Exception as e:
                            logger.warning(f"Redis cleanup failed during login: {e}")
                            # Continue with login even if cleanup fails

                        # Set session state
                        st.session_state.authenticated = True
                        st.session_state.user = auth_result["user"]
                        st.session_state.session_token = auth_result["session_token"]

                        logger.info(f"Email/password authentication successful: {email}")
                        st.success(f"✅ Welcome, {auth_result['user']['name']}!")
                        st.rerun()
                        return True
                    else:
                        st.error("❌ Invalid email or password")
                        logger.warning(f"Failed login attempt for: {email}")
                        return False

                except Exception as e:
                    st.error(f"⚠️ An error occurred during sign-in: {str(e)}")
                    logger.error(f"Email/password authentication error for {email}: {e}")
                    return False

        if forgot_password:
            st.info(
                "To reset your password, please contact your administrator or "
                "use the Settings page after signing in."
            )
            return False

    return False
