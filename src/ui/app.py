# src/ui/app.py
"""Arbor AI Studio - Sign In Page"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

import streamlit as st
import os
from dotenv import load_dotenv

from config.database import SessionLocal
from src.repositories.user_repository import UserRepository
from src.services.user_service import UserService
from src.services.auth_service import AuthService
from src.utils.logger import setup_logging, get_logger
from src.ui.components.google_auth_button import render_google_signin
from src.ui.components.email_password_signin import render_email_password_signin

# Load environment variables
load_dotenv()

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Page config
st.set_page_config(
    page_title="AI Content Generator - Sign In",
    page_icon="🌳",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Custom CSS - Minimalistic Ash/White/Cyan Theme
st.markdown(
    """
<style>
    /* Global Styles */
    .stApp {
        background-color: #2b2d31;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Text colors */
    h1, h2, h3, h4, h5, h6, p, div, span, label {
        color: #ffffff !important;
    }

    /* Cyan highlights */
    .highlight {
        color: #00d9ff !important;
    }

    /* Sign-in container */
    .signin-container {
        background-color: #383a40;
        padding: 3rem 2rem;
        border-radius: 12px;
        text-align: center;
        margin-top: 5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }

    /* Logo/Title */
    .app-title {
        font-size: 2.5rem;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 0.5rem;
    }

    .app-subtitle {
        font-size: 1.1rem;
        color: #00d9ff;
        margin-bottom: 2rem;
    }

    /* Buttons */
    .stButton > button {
        background-color: #00d9ff !important;
        color: #2b2d31 !important;
        border: none !important;
        padding: 0.75rem 2rem !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
    }

    .stButton > button:hover {
        background-color: #00b8d4 !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 217, 255, 0.3) !important;
    }

    /* Error/Warning messages */
    .stAlert {
        background-color: #383a40 !important;
        border-left: 4px solid #ff4444 !important;
        color: #ffffff !important;
    }

    /* Info messages */
    .stInfo {
        background-color: #383a40 !important;
        border-left: 4px solid #00d9ff !important;
        color: #ffffff !important;
    }

    /* Input fields */
    .stTextInput input {
        background-color: #383a40 !important;
        color: #ffffff !important;
        border: 1px solid #4a4d57 !important;
        border-radius: 8px !important;
        padding: 0.75rem !important;
    }

    .stTextInput input:focus {
        border-color: #00d9ff !important;
        box-shadow: 0 0 0 2px rgba(0, 217, 255, 0.2) !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: #383a40 !important;
        color: #ffffff !important;
        border-radius: 8px 8px 0 0;
        padding: 0.75rem 1.5rem;
    }

    .stTabs [aria-selected="true"] {
        background-color: #00d9ff !important;
        color: #2b2d31 !important;
    }

    /* Form submit buttons */
    [data-testid="stForm"] button[kind="primary"] {
        background-color: #00d9ff !important;
        color: #2b2d31 !important;
    }

    [data-testid="stForm"] button[kind="secondary"] {
        background-color: #383a40 !important;
        color: #ffffff !important;
        border: 1px solid #4a4d57 !important;
    }

    /* Captions */
    .stCaption {
        color: #b0b3b8 !important;
    }
</style>
""",
    unsafe_allow_html=True,
)


def init_session_state():
    """Initialize session state variables."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = None


def render_signin_page():
    """Render the sign-in page."""

    # Logo and title
    st.markdown(
        """
    <div class="signin-container">
        <div class="app-title"> AI Studio</div>
        <div class="app-subtitle">Visual Content Generation Platform</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Sign-in section
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("### Welcome")
        st.markdown("Choose your preferred sign-in method")

        st.markdown("<br>", unsafe_allow_html=True)

        # Create tabs for different sign-in methods
        tab1, tab2 = st.tabs(["📧 Email & Password", "🔐 Google Sign-In"])

        # Tab 1: Email/Password Sign-In
        with tab1:
            st.markdown("<br>", unsafe_allow_html=True)
            try:
                db = SessionLocal()
                user_repo = UserRepository(db)
                user_service = UserService(user_repo)
                google_client_id = os.getenv("GOOGLE_CLIENT_ID", "")
                auth_service = AuthService(user_service, google_client_id)

                # Render email/password sign-in
                render_email_password_signin(user_service, auth_service)

                db.close()

            except Exception as e:
                st.error(f"Sign-in error: {e}")
                logger.error(f"Email/password sign-in failed: {e}")

            st.markdown("<br>", unsafe_allow_html=True)
            st.caption("Change pass in Settings after signing in)")

        # Tab 2: Google Sign-In
        with tab2:
            st.markdown("<br>", unsafe_allow_html=True)

            google_client_id = os.getenv("GOOGLE_CLIENT_ID")

            if (
                google_client_id
                and google_client_id
                != "your_google_client_id_here.apps.googleusercontent.com"
            ):
                st.markdown("#### Sign in with Google")
                token = render_google_signin(google_client_id)

                if token:
                    # Verify token and authenticate
                    try:
                        db = SessionLocal()
                        user_repo = UserRepository(db)
                        user_service = UserService(user_repo)
                        auth_service = AuthService(user_service, google_client_id)

                        # Authenticate user
                        auth_result = auth_service.authenticate_user(token)

                        if auth_result:
                            # Set session state
                            st.session_state.authenticated = True
                            st.session_state.user = auth_result["user"]
                            st.session_state.session_token = auth_result[
                                "session_token"
                            ]

                            logger.info(
                                f"User authenticated: {auth_result['user']['email']}"
                            )
                            st.success(f"✅ Welcome, {auth_result['user']['name']}!")
                            st.rerun()
                        else:
                            st.error(
                                "❌ Authentication failed. You are not authorized to access this system."
                            )
                            st.info(
                                "Only registered team members can sign in. Contact an administrator if you need access."
                            )

                        db.close()

                    except Exception as e:
                        st.error(f"Authentication error: {e}")
                        logger.error(f"Authentication failed: {e}")

            else:
                st.info(
                    "🔐 **Google Sign-In Not Configured**\n\nTo enable Google Sign-In:\n1. Get OAuth credentials from [Google Cloud Console](https://console.cloud.google.com/)\n2. Add `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` to your `.env` file"
                )

        st.markdown("<br>", unsafe_allow_html=True)

        # Development mode bypass (temporary)
        with st.expander("🔧 Development Mode"):
            st.markdown("**Temporary bypass for testing:**")

            # Get list of users from database
            try:
                db = SessionLocal()
                user_repo = UserRepository(db)
                user_service = UserService(user_repo)
                users = user_service.get_all_users()
                db.close()

                if users:
                    user_emails = [u.email for u in users]
                    selected_email = st.selectbox("Select a test user:", user_emails)

                    if st.button(
                        "🚀 Quick Sign In (Dev Only)", use_container_width=True
                    ):
                        with st.spinner("🔐 Signing in..."):
                            # Find selected user
                            selected_user = next(
                                u for u in users if u.email == selected_email
                            )

                            # Clear old Redis sessions before signing in
                            try:
                                from config.redis import get_redis
                                from src.services.session_manager import SessionManager

                                redis_client = get_redis()
                                session_manager = SessionManager(redis_client)

                                # Clean up old sessions (older than 24 hours)
                                session_manager.cleanup_old_sessions(max_age_hours=24)

                                # Clear any existing session for this user
                                session_manager.cleanup_all_user_data(selected_user.email)
                            except Exception as e:
                                logger.warning(f"Redis cleanup failed: {e}")
                                # Continue with login even if cleanup fails

                            # Set session state
                            st.session_state.authenticated = True
                            st.session_state.user = {
                                "id": str(selected_user.id),
                                "email": selected_user.email,
                                "name": selected_user.name,
                                "role": selected_user.role,
                                "team": selected_user.team,
                            }

                            logger.info(f"Dev mode sign-in: {selected_user.email}")
                            st.success(f"✅ Signed in as {selected_user.name}")
                            st.rerun()
                else:
                    st.warning(
                        "No users found. Run `python scripts/seed_users.py` first."
                    )

            except Exception as e:
                st.error(f"Database error: {e}")
                logger.error(f"Failed to load users: {e}")


def main():
    """Main application entry point."""
    init_session_state()

    if st.session_state.authenticated:
        # Redirect to Home page after successful authentication
        st.switch_page("pages/Home.py")
    else:
        render_signin_page()


if __name__ == "__main__":
    main()
