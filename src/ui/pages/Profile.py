"""
Profile Page - User's Own Content

Shows user's generated content with visibility management.
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
from src.repositories.content_repository import ContentRepository
from src.services.content_service import ContentService
from src.utils.logger import get_logger
from uuid import UUID

logger = get_logger(__name__)

# Page configuration
st.set_page_config(
    page_title="Profile - Arbor AI Studio",
    page_icon="👤",
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
st.title(f"👤 {user['name']}'s Profile")
st.markdown(f"**{user['email']}** • {user.get('role', 'user').upper()}")
st.markdown("---")

# Fetch user's content
db = None
try:
    db = SessionLocal()
    content_repo = ContentRepository(db)
    content_service = ContentService(content_repo)

    # Get user's content
    user_id = UUID(user['id']) if isinstance(user['id'], str) else user['id']
    content_list = content_service.get_user_content(user_id)

    # Calculate statistics
    total = len(content_list)
    public = sum(1 for c in content_list if c.visibility == 'public')
    private = total - public
    # Note: Content doesn't have status, all items in content table are completed

    # Display stats
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Content", total)

    with col2:
        st.metric("Public", public)

    with col3:
        st.metric("Private", private)

    st.markdown("---")

    # Filter options
    st.subheader("My Content")

    col1, col2 = st.columns([2, 8])

    with col1:
        filter_visibility = st.selectbox(
            "Visibility",
            options=["all", "public", "private"]
        )

    with col2:
        columns = st.selectbox(
            "Columns",
            options=[2, 3, 4],
            index=1
        )

    st.markdown("---")

    # Apply filters
    filtered_content = content_list

    if filter_visibility != "all":
        filtered_content = [c for c in filtered_content if c.visibility == filter_visibility]

    # Display content
    if filtered_content:
        st.markdown(f"**{len(filtered_content)} items**")
        st.markdown("---")

        # Create grid layout
        cols = st.columns(columns)

        for idx, content in enumerate(filtered_content):
            col_idx = idx % columns

            with cols[col_idx]:
                # Display image
                image_path = content.generated_image_url
                thumbnail_path = content.thumbnail_url

                display_image = thumbnail_path if thumbnail_path and Path(thumbnail_path).exists() else image_path

                if display_image and Path(display_image).exists():
                    st.image(display_image, use_container_width=True)
                else:
                    st.warning("Image not found")

                # Title
                st.markdown(f"**{content.title or 'Untitled'}**")

                # Creation date
                try:
                    created_date = content.created_at.strftime("%b %d, %Y %I:%M %p")
                except:
                    created_date = "Unknown"

                st.caption(f"Created: {created_date}")

                # Visibility toggle
                current_visibility = content.visibility

                visibility_options = ["private", "public"]
                current_index = visibility_options.index(current_visibility)

                new_visibility = st.selectbox(
                    "Visibility",
                    options=visibility_options,
                    index=current_index,
                    key=f"visibility_{content.id}",
                    format_func=lambda x: f"{'🔒 Private' if x == 'private' else '🌐 Public'}"
                )

                # Update if changed
                if new_visibility != current_visibility:
                    try:
                        content_service.update_visibility(content.id, new_visibility, user_id)
                        st.success(f"Updated to {new_visibility}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed: {str(e)}")

                # Action buttons
                col_a, col_b, col_c = st.columns(3)

                with col_a:
                    with st.expander("🔍 Prompt"):
                        st.text_area(
                            "Prompt",
                            value=content.prompt or "No prompt",
                            height=100,
                            key=f"prompt_{content.id}",
                            disabled=True,
                            label_visibility="collapsed"
                        )

                with col_b:
                    if st.button("🖼️", key=f"view_{content.id}", use_container_width=True, help="View Full"):
                        st.session_state[f"show_full_{content.id}"] = True

                with col_c:
                    if st.button("🗑️", key=f"delete_{content.id}", use_container_width=True, help="Delete"):
                        st.session_state[f"confirm_delete_{content.id}"] = True

                # Delete confirmation
                if st.session_state.get(f"confirm_delete_{content.id}", False):
                    st.warning("⚠️ Delete this item?")
                    col_a, col_b = st.columns(2)

                    with col_a:
                        if st.button("✅ Yes", key=f"yes_{content.id}", use_container_width=True):
                            try:
                                content_service.delete_content(content.id, user_id)
                                st.success("Deleted")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")

                    with col_b:
                        if st.button("❌ No", key=f"no_{content.id}", use_container_width=True):
                            st.session_state[f"confirm_delete_{content.id}"] = False
                            st.rerun()

                # Full image modal
                if st.session_state.get(f"show_full_{content.id}", False):
                    with st.expander("Full Image", expanded=True):
                        if image_path and Path(image_path).exists():
                            st.image(image_path, use_container_width=True)

                            try:
                                with open(image_path, "rb") as f:
                                    st.download_button(
                                        label="💾 Download",
                                        data=f.read(),
                                        file_name=f"{content.title or 'image'}.png",
                                        mime="image/png",
                                        key=f"download_{content.id}"
                                    )
                            except Exception as e:
                                st.error(f"Download error: {e}")

                        if st.button("Close", key=f"close_{content.id}"):
                            st.session_state[f"show_full_{content.id}"] = False
                            st.rerun()

                st.markdown("---")

    else:
        st.info("No content matches your filters")

        if filter_status == "all" and filter_visibility == "all":
            st.markdown("Go to **Chat** page to create your first image!")

except Exception as e:
    st.error(f"⚠️ Failed to load profile: {str(e)}")
    logger.error(f"Error in profile page: {str(e)}")

    with st.expander("Error Details"):
        st.code(str(e))

finally:
    if db:
        db.close()
