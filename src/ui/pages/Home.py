"""
Home Page - Public Content Feed

Shows public content from all users in a simple grid layout with pagination.
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
from src.repositories.user_repository import UserRepository
from src.services.content_service import ContentService
from src.services.user_service import UserService
from src.utils.logger import get_logger
from datetime import datetime

logger = get_logger(__name__)

# Page configuration
st.set_page_config(
    page_title="Home - Arbor AI Studio",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Render navbar
render_navbar()

# Check authentication
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.error("⚠️ Please sign in first")
    st.stop()

# Initialize session state for pagination
if "home_page_number" not in st.session_state:
    st.session_state.home_page_number = 1

# Page header
st.title("🏠 Home - Public Gallery")
st.markdown("Explore AI-generated content from the community")
st.markdown("---")

# Fetch public content
db = None
try:
    db = SessionLocal()
    content_repo = ContentRepository(db)
    content_service = ContentService(content_repo)
    user_repo = UserRepository(db)
    user_service = UserService(user_repo)

    # Get total count of public content
    total_public = content_repo.count_public()

    # Pagination settings
    items_per_page = 20
    total_pages = max(1, (total_public + items_per_page - 1) // items_per_page)  # Ceiling division
    current_page = st.session_state.home_page_number

    # Ensure current page is valid
    if current_page > total_pages:
        current_page = total_pages
        st.session_state.home_page_number = total_pages

    # Calculate offset for pagination
    offset = (current_page - 1) * items_per_page

    # Get paginated public content
    all_public_content = content_service.get_public_content(limit=None)
    paginated_content = all_public_content[offset:offset + items_per_page]

    if total_public > 0:
        # Top controls - Filter options and pagination info
        col1, col2, col3 = st.columns([2, 6, 2])

        with col1:
            st.markdown(f"**{total_public} items**")

        with col2:
            # Pagination controls
            pagination_col1, pagination_col2, pagination_col3, pagination_col4, pagination_col5 = st.columns([1, 1, 2, 1, 1])

            with pagination_col1:
                if st.button("⏮️ First", disabled=(current_page == 1), use_container_width=True):
                    st.session_state.home_page_number = 1
                    st.rerun()

            with pagination_col2:
                if st.button("◀️ Prev", disabled=(current_page == 1), use_container_width=True):
                    st.session_state.home_page_number = max(1, current_page - 1)
                    st.rerun()

            with pagination_col3:
                st.markdown(f"<div style='text-align: center; padding-top: 8px;'>Page {current_page} of {total_pages}</div>", unsafe_allow_html=True)

            with pagination_col4:
                if st.button("Next ▶️", disabled=(current_page == total_pages), use_container_width=True):
                    st.session_state.home_page_number = min(total_pages, current_page + 1)
                    st.rerun()

            with pagination_col5:
                if st.button("Last ⏭️", disabled=(current_page == total_pages), use_container_width=True):
                    st.session_state.home_page_number = total_pages
                    st.rerun()

        with col3:
            columns = st.selectbox(
                "Columns",
                options=[2, 3, 4],
                index=1,
                label_visibility="collapsed"
            )

        st.markdown("---")

        # Create grid layout
        if paginated_content:
            cols = st.columns(columns)

            for idx, content in enumerate(paginated_content):
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

                    # Content title
                    st.markdown(f"**{content.title}**")

                    # Creator and date
                    try:
                        # Get creator name from user
                        creator = user_service.get_user_by_id(content.user_id)
                        creator_name = creator.name if creator else "Unknown"
                        created_date = content.created_at.strftime("%b %d, %Y")
                    except Exception as e:
                        creator_name = "Unknown"
                        created_date = "Unknown"
                        logger.error(f"Error fetching user info: {e}")

                    st.caption(f"By {creator_name} • {created_date}")

                    # View prompt button
                    with st.expander("🔍 View Prompt"):
                        st.text_area(
                            "Prompt",
                            value=content.prompt or "No prompt available",
                            height=100,
                            key=f"prompt_{content.id}_{current_page}",
                            disabled=True,
                            label_visibility="collapsed"
                        )

                    # View full image
                    if st.button("🖼️ View Full", key=f"view_{content.id}_{current_page}", use_container_width=True):
                        st.session_state[f"show_modal_{content.id}"] = True

                    # Modal for full image
                    if st.session_state.get(f"show_modal_{content.id}", False):
                        with st.expander("Full Image", expanded=True):
                            if image_path and Path(image_path).exists():
                                st.image(image_path, use_container_width=True)

                                # Download button
                                try:
                                    with open(image_path, "rb") as f:
                                        st.download_button(
                                            label="💾 Download",
                                            data=f.read(),
                                            file_name=f"{content.title}.png",
                                            mime="image/png",
                                            key=f"download_{content.id}_{current_page}"
                                        )
                                except Exception as e:
                                    st.error(f"Download error: {e}")
                                    logger.error(f"Download error for content {content.id}: {e}")

                            if st.button("Close", key=f"close_{content.id}_{current_page}"):
                                st.session_state[f"show_modal_{content.id}"] = False
                                st.rerun()

                    st.markdown("---")

            # Bottom pagination controls
            st.markdown("---")
            pagination_bottom = st.columns([1, 1, 2, 1, 1])

            with pagination_bottom[0]:
                if st.button("⏮️", disabled=(current_page == 1), use_container_width=True, key="first_bottom"):
                    st.session_state.home_page_number = 1
                    st.rerun()

            with pagination_bottom[1]:
                if st.button("◀️", disabled=(current_page == 1), use_container_width=True, key="prev_bottom"):
                    st.session_state.home_page_number = max(1, current_page - 1)
                    st.rerun()

            with pagination_bottom[2]:
                st.markdown(f"<div style='text-align: center; padding-top: 8px;'>Page {current_page} of {total_pages}</div>", unsafe_allow_html=True)

            with pagination_bottom[3]:
                if st.button("▶️", disabled=(current_page == total_pages), use_container_width=True, key="next_bottom"):
                    st.session_state.home_page_number = min(total_pages, current_page + 1)
                    st.rerun()

            with pagination_bottom[4]:
                if st.button("⏭️", disabled=(current_page == total_pages), use_container_width=True, key="last_bottom"):
                    st.session_state.home_page_number = total_pages
                    st.rerun()
        else:
            st.info("No content on this page")

    else:
        st.info("📭 No public content yet")
        st.markdown("Be the first to create and share content!")
        st.markdown("Go to **Chat** page to start creating.")

except Exception as e:
    st.error(f"⚠️ Failed to load content: {str(e)}")
    logger.error(f"Error loading public content: {str(e)}")

    with st.expander("Error Details"):
        st.code(str(e))
        st.markdown("**Troubleshooting:**")
        st.markdown("- Check if the database is accessible")
        st.markdown("- Verify the Content table exists in your database")
        st.markdown("- Check the logs for more details")

finally:
    if db:
        db.close()
