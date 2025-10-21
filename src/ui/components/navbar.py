"""
Navbar Component - Fixed Full-Width Island Design

Displays a fixed top navigation bar with modern island design.
"""

import streamlit as st


def render_navbar():
    """Render the fixed full-width island navbar."""

    # Check if user is authenticated
    if "authenticated" not in st.session_state or not st.session_state.authenticated:
        return

    user = st.session_state.get("user", {})
    user_name = user.get("name", "User")

    # Custom CSS for fixed island navbar
    st.markdown("""
    <style>
        /* Hide default Streamlit elements */
        [data-testid="stSidebar"] {
            display: none;
        }

        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}

        /* Navbar island container - fixed at top */
        .navbar-island {
            position: fixed;
            top: 12px;
            left: 50%;
            transform: translateX(-50%);
            width: calc(100% - 4rem);
            max-width: 1400px;
            height: 60px;
            background: linear-gradient(135deg, #2b2d31 0%, #1e1f23 100%);
            border: 1px solid rgba(0, 217, 255, 0.3);
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4),
                        0 0 0 1px rgba(0, 217, 255, 0.1) inset;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 2rem;
            z-index: 9999;
            backdrop-filter: blur(10px);
        }

        /* Navbar brand */
        .navbar-brand {
            font-size: 1.4rem;
            font-weight: 700;
            background: linear-gradient(135deg, #00d9ff 0%, #00b8d4 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: -0.5px;
        }

        /* Navigation links container */
        .navbar-nav {
            display: flex;
            gap: 0.5rem;
            align-items: center;
            flex: 1;
            justify-content: center;
        }

        /* User section */
        .navbar-user {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .navbar-user-name {
            color: #ffffff;
            font-size: 0.9rem;
            font-weight: 500;
            padding: 0.5rem 1rem;
            background: rgba(0, 217, 255, 0.1);
            border-radius: 8px;
            border: 1px solid rgba(0, 217, 255, 0.2);
        }

        /* Add top padding to main content to account for fixed navbar */
        .main .block-container {
            padding-top: 100px !important;
        }

        /* Override Streamlit's default button styling for navbar buttons */
        div[data-testid="column"] > div > div > div > button {
            background-color: rgba(255, 255, 255, 0.05) !important;
            color: #ffffff !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 10px !important;
            padding: 0.6rem 1.2rem !important;
            font-weight: 500 !important;
            transition: all 0.3s ease !important;
            height: 38px !important;
            font-size: 0.9rem !important;
        }

        div[data-testid="column"] > div > div > div > button:hover {
            background-color: rgba(0, 217, 255, 0.15) !important;
            border-color: rgba(0, 217, 255, 0.4) !important;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 217, 255, 0.2);
        }

        /* Active page button highlight */
        div[data-testid="column"] > div > div > div > button[kind="primary"] {
            background-color: rgba(0, 217, 255, 0.2) !important;
            border-color: #00d9ff !important;
            color: #00d9ff !important;
        }

        /* Sign out button special styling */
        button[data-testid*="signout"] {
            background-color: rgba(255, 68, 68, 0.1) !important;
            border-color: rgba(255, 68, 68, 0.3) !important;
        }

        button[data-testid*="signout"]:hover {
            background-color: rgba(255, 68, 68, 0.2) !important;
            border-color: rgba(255, 68, 68, 0.5) !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # Create navbar structure using Streamlit columns
    # The actual navbar styling is done via CSS above

    st.markdown('<div class="navbar-island-spacer"></div>', unsafe_allow_html=True)

    # Brand, Navigation, and User sections
    brand_col, nav_col1, nav_col2, nav_col3, nav_col4, user_col, signout_col = st.columns([2, 1, 1, 1, 1, 2, 1])

    with brand_col:
        st.markdown('<div class="navbar-brand">🌳 Arbor AI</div>', unsafe_allow_html=True)

    # Get current page to highlight active button
    try:
        import os
        current_file = os.path.basename(__file__)
        current_page = st.session_state.get("current_page", "home")
    except:
        current_page = "home"

    with nav_col1:
        if st.button("🏠 Home", key="nav_home", use_container_width=True):
            try:
                st.switch_page("pages/Home.py")
            except Exception as e:
                st.error(f"Navigation error: {e}")

    with nav_col2:
        if st.button("💬 Chat", key="nav_chat", use_container_width=True):
            try:
                st.switch_page("pages/1_Chat.py")
            except Exception as e:
                st.error(f"Navigation error: {e}")

    with nav_col3:
        if st.button("👤 Profile", key="nav_profile", use_container_width=True):
            try:
                st.switch_page("pages/Profile.py")
            except Exception as e:
                st.error(f"Navigation error: {e}")

    with nav_col4:
        if st.button("⚙️ Settings", key="nav_settings", use_container_width=True):
            try:
                st.switch_page("pages/Settings.py")
            except Exception as e:
                st.error(f"Navigation error: {e}")

    with user_col:
        st.markdown(f'<div class="navbar-user-name">👋 {user_name}</div>', unsafe_allow_html=True)

    with signout_col:
        if st.button("🚪", key="nav_signout", help="Sign Out", use_container_width=True):
            # Clear Redis cache for user
            try:
                from config.redis import get_redis
                from src.services.session_manager import SessionManager

                user_email = user.get("email")
                if user_email:
                    redis_client = get_redis()
                    session_manager = SessionManager(redis_client)

                    # Complete cleanup of all user data from Redis
                    session_manager.cleanup_all_user_data(user_email)
            except Exception as e:
                # Log but don't fail logout
                pass

            # Clear all session state
            keys_to_clear = list(st.session_state.keys())
            for key in keys_to_clear:
                del st.session_state[key]

            # Reinitialize only essential state
            st.session_state.authenticated = False
            st.session_state.user = None

            # Navigate to home/sign-in page
            try:
                st.switch_page("app.py")
            except:
                st.rerun()

    # Separator line below navbar
    st.markdown("---")
