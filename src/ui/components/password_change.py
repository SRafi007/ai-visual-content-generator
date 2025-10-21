"""Password change component for user settings."""

import streamlit as st
from typing import Optional
from src.services.user_service import UserService
from src.utils.logger import get_logger

logger = get_logger(__name__)


def render_password_change_form(user_service: UserService, user_email: str) -> None:
    """
    Render password change form for logged-in users.

    Args:
        user_service: UserService instance
        user_email: Email of the logged-in user
    """
    st.subheader("Change Password")
    st.markdown("---")

    with st.form("password_change_form", clear_on_submit=True):
        st.markdown("### Update Your Password")
        st.caption("Password must be at least 6 characters long")

        # Password fields
        current_password = st.text_input(
            "Current Password",
            type="password",
            placeholder="Enter your current password",
            help="Your current password for verification"
        )

        new_password = st.text_input(
            "New Password",
            type="password",
            placeholder="Enter your new password",
            help="Must be at least 6 characters"
        )

        confirm_password = st.text_input(
            "Confirm New Password",
            type="password",
            placeholder="Re-enter your new password",
            help="Must match the new password"
        )

        # Submit button
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            submit_button = st.form_submit_button(
                "Change Password",
                use_container_width=True,
                type="primary"
            )

        if submit_button:
            # Validate inputs
            if not current_password or not new_password or not confirm_password:
                st.error("All fields are required")
                return

            if new_password != confirm_password:
                st.error("New passwords do not match")
                return

            if len(new_password) < 6:
                st.error("New password must be at least 6 characters long")
                return

            if new_password == current_password:
                st.error("New password must be different from current password")
                return

            # Attempt to change password
            try:
                success = user_service.change_password(
                    user_email=user_email,
                    current_password=current_password,
                    new_password=new_password
                )

                if success:
                    st.success("Password changed successfully!")
                    logger.info(f"Password changed via UI for user: {user_email}")
                else:
                    st.error("Failed to change password. Please try again.")

            except ValueError as e:
                st.error(f"Error: {str(e)}")
                logger.warning(f"Password change validation error for {user_email}: {e}")

            except Exception as e:
                st.error("An unexpected error occurred. Please try again.")
                logger.error(f"Password change error for {user_email}: {e}")


def render_admin_password_reset(
    user_service: UserService,
    admin_email: str,
    target_user_email: Optional[str] = None
) -> None:
    """
    Render admin password reset form.

    Args:
        user_service: UserService instance
        admin_email: Email of the admin user
        target_user_email: Optional pre-selected user email
    """
    st.subheader("Reset User Password (Admin)")
    st.markdown("---")

    with st.form("admin_password_reset_form", clear_on_submit=True):
        st.markdown("### Reset Password for User")
        st.warning("⚠️ Admin Only: Reset password for any user")

        # User selection
        user_email_input = st.text_input(
            "User Email",
            value=target_user_email or "",
            placeholder="user@example.com",
            help="Email of the user whose password to reset"
        )

        new_password = st.text_input(
            "New Password",
            type="password",
            placeholder="Enter new password for user",
            help="Must be at least 6 characters"
        )

        confirm_password = st.text_input(
            "Confirm New Password",
            type="password",
            placeholder="Re-enter new password",
            help="Must match the new password"
        )

        # Submit button
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            submit_button = st.form_submit_button(
                "Reset Password",
                use_container_width=True,
                type="primary"
            )

        if submit_button:
            # Validate inputs
            if not user_email_input or not new_password or not confirm_password:
                st.error("All fields are required")
                return

            if new_password != confirm_password:
                st.error("Passwords do not match")
                return

            if len(new_password) < 6:
                st.error("Password must be at least 6 characters long")
                return

            # Attempt to reset password
            try:
                success = user_service.reset_password(
                    user_email=user_email_input,
                    new_password=new_password,
                    admin_email=admin_email
                )

                if success:
                    st.success(f"Password reset successfully for {user_email_input}!")
                    logger.info(f"Admin {admin_email} reset password for {user_email_input}")
                else:
                    st.error("Failed to reset password. Please try again.")

            except PermissionError as e:
                st.error(f"Permission denied: {str(e)}")
                logger.warning(f"Unauthorized password reset attempt by {admin_email}")

            except ValueError as e:
                st.error(f"Error: {str(e)}")
                logger.warning(f"Password reset validation error: {e}")

            except Exception as e:
                st.error("An unexpected error occurred. Please try again.")
                logger.error(f"Password reset error: {e}")


def render_password_strength_indicator(password: str) -> None:
    """
    Render a simple password strength indicator.

    Args:
        password: The password to evaluate
    """
    if not password:
        return

    strength = 0
    feedback = []

    # Length check
    if len(password) >= 6:
        strength += 1
    else:
        feedback.append("At least 6 characters")

    if len(password) >= 10:
        strength += 1

    # Complexity checks
    if any(c.isupper() for c in password):
        strength += 1
    else:
        feedback.append("Include uppercase letters")

    if any(c.isdigit() for c in password):
        strength += 1
    else:
        feedback.append("Include numbers")

    if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        strength += 1
    else:
        feedback.append("Include special characters")

    # Display strength
    if strength <= 1:
        st.markdown("🔴 **Weak password**")
    elif strength <= 3:
        st.markdown("🟡 **Moderate password**")
    else:
        st.markdown("🟢 **Strong password**")

    if feedback:
        st.caption("Suggestions: " + ", ".join(feedback))
