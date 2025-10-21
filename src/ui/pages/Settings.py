"""
Settings Page - User Settings and Admin Panel

Regular users can update their own info and password.
Admins can manage all users (add, remove, promote to admin).
"""

import streamlit as st
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.ui.components.navbar import render_navbar
from config.database import SessionLocal
from src.repositories.user_repository import UserRepository
from src.services.user_service import UserService
from src.services.auth_service import AuthService
from src.utils.logger import get_logger
from uuid import UUID
import os

logger = get_logger(__name__)

# Page configuration
st.set_page_config(
    page_title="Settings - Arbor AI Studio",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Render navbar
render_navbar()

# Check authentication
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.error("⚠️ Please sign in first")
    st.stop()

user = st.session_state.user

# Page header
st.title("⚙️ Settings")
st.markdown("---")

# User Settings Section
st.subheader("👤 Your Profile")

db = None
try:
    db = SessionLocal()
    user_repo = UserRepository(db)
    user_service = UserService(user_repo)
    google_client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    auth_service = AuthService(user_service, google_client_id)

    col1, col2 = st.columns(2)

    with col1:
        st.text_input("Name", value=user.get('name', ''), disabled=True)
        st.text_input("Email", value=user.get('email', ''), disabled=True)

    with col2:
        st.text_input("Role", value=user.get('role', 'user').upper(), disabled=True)
        st.text_input("Team", value=user.get('team', 'N/A'), disabled=True)

    st.markdown("---")

    # Change Password Section
    st.subheader("🔒 Change Password")

    with st.form("change_password_form"):
        current_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")

        submit_password = st.form_submit_button("Update Password")

        if submit_password:
            if not current_password or not new_password or not confirm_password:
                st.error("All fields are required")
            elif new_password != confirm_password:
                st.error("New passwords don't match")
            elif len(new_password) < 6:
                st.error("Password must be at least 6 characters")
            else:
                try:
                    # Verify current password
                    verified_user = user_service.authenticate_user(user['email'], current_password)

                    if verified_user:
                        # Update password
                        user_service.update_password(user['email'], new_password)
                        st.success("✅ Password updated successfully!")
                    else:
                        st.error("❌ Current password is incorrect")

                except Exception as e:
                    st.error(f"Failed to update password: {str(e)}")
                    logger.error(f"Password update error: {str(e)}")

    st.markdown("---")

    # Admin Panel - Only for admins
    if user.get('role') == 'admin':
        st.subheader("🔧 Admin Panel")

        tab1, tab2, tab3 = st.tabs(["👥 All Users", "➕ Add User", "��️ Remove User"])

        # Tab 1: View All Users
        with tab1:
            st.markdown("### All Users")

            users = user_service.get_all_users()

            if users:
                # Create a table display
                for usr in users:
                    col1, col2, col3, col4, col5 = st.columns([3, 3, 2, 2, 2])

                    with col1:
                        st.text(usr.name)

                    with col2:
                        st.text(usr.email)

                    with col3:
                        st.text(usr.role.upper())

                    with col4:
                        # Promote/Demote button
                        if usr.email != user['email']:  # Can't modify own role
                            if usr.role == 'admin':
                                if st.button("⬇️ Demote", key=f"demote_{usr.id}", help="Remove admin privileges"):
                                    try:
                                        user_service.update_user_role(usr.email, 'user')
                                        st.success(f"Demoted {usr.name} to user")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {e}")
                            else:
                                if st.button("⬆️ Promote", key=f"promote_{usr.id}", help="Make admin"):
                                    try:
                                        user_service.update_user_role(usr.email, 'admin')
                                        st.success(f"Promoted {usr.name} to admin")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {e}")

                    with col5:
                        # Can't delete own account
                        if usr.email != user['email']:
                            if st.button("🗑️", key=f"del_{usr.id}", help="Delete user"):
                                st.session_state[f"confirm_del_{usr.id}"] = True

                    # Delete confirmation
                    if st.session_state.get(f"confirm_del_{usr.id}", False):
                        col_a, col_b, col_c = st.columns([4, 1, 1])

                        with col_a:
                            st.warning(f"⚠️ Delete {usr.name}? This will also delete their content!")

                        with col_b:
                            if st.button("✅ Yes", key=f"yes_del_{usr.id}"):
                                try:
                                    user_service.delete_user(usr.email)
                                    st.success(f"Deleted {usr.name}")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")

                        with col_c:
                            if st.button("❌ No", key=f"no_del_{usr.id}"):
                                st.session_state[f"confirm_del_{usr.id}"] = False
                                st.rerun()

                    st.markdown("---")

        # Tab 2: Add New User
        with tab2:
            st.markdown("### Add New User")

            with st.form("add_user_form"):
                new_name = st.text_input("Full Name")
                new_email = st.text_input("Email")
                new_password = st.text_input("Initial Password", type="password", value="arbor2024")
                new_role = st.selectbox("Role", options=["user", "admin"])
                new_team = st.text_input("Team", value="General")

                submit_user = st.form_submit_button("Add User")

                if submit_user:
                    if not new_name or not new_email:
                        st.error("Name and Email are required")
                    else:
                        try:
                            # Check if user already exists
                            existing = user_service.get_user_by_email(new_email)

                            if existing:
                                st.error(f"User with email {new_email} already exists")
                            else:
                                # Create new user
                                user_service.create_user(
                                    email=new_email,
                                    name=new_name,
                                    password=new_password,
                                    role=new_role,
                                    team=new_team
                                )
                                st.success(f"✅ User {new_name} created successfully!")
                                st.info(f"Initial password: {new_password}")
                                st.rerun()

                        except Exception as e:
                            st.error(f"Failed to create user: {str(e)}")
                            logger.error(f"User creation error: {str(e)}")

        # Tab 3: Remove User
        with tab3:
            st.markdown("### Remove User")

            users_to_remove = [u for u in user_service.get_all_users() if u.email != user['email']]

            if users_to_remove:
                user_emails = [u.email for u in users_to_remove]

                selected_email = st.selectbox("Select user to remove", options=user_emails)

                selected_user = next((u for u in users_to_remove if u.email == selected_email), None)

                if selected_user:
                    st.warning(f"**Name:** {selected_user.name}")
                    st.warning(f"**Email:** {selected_user.email}")
                    st.warning(f"**Role:** {selected_user.role}")

                    st.error("⚠️ This will permanently delete the user and all their generated content!")

                    if st.button("🗑️ Confirm Delete User", type="primary"):
                        try:
                            user_service.delete_user(selected_email)
                            st.success(f"✅ User {selected_user.name} has been deleted")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to delete user: {str(e)}")
                            logger.error(f"User deletion error: {str(e)}")
            else:
                st.info("No other users to remove")

except Exception as e:
    st.error(f"⚠️ Settings error: {str(e)}")
    logger.error(f"Settings page error: {str(e)}")

    with st.expander("Error Details"):
        st.code(str(e))

finally:
    if db:
        db.close()
