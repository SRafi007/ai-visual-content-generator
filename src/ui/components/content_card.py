"""
Content Card Component

Displays generated images in a card format with hidden prompts.
"""

import streamlit as st
from pathlib import Path
from typing import Optional
from datetime import datetime


def render_content_card(
    generation_id: str,
    image_path: str,
    project_name: str,
    creator_name: str,
    created_at: str,
    prompt: str,
    thumbnail_path: Optional[str] = None,
    show_prompt: bool = False
):
    """
    Render a single content card.

    Args:
        generation_id: Unique ID of the generation
        image_path: Path to the full image
        project_name: Name of the project
        creator_name: Name of the creator
        created_at: Creation timestamp
        prompt: The generation prompt (hidden by default)
        thumbnail_path: Path to thumbnail (optional)
        show_prompt: Whether to show prompt initially
    """

    # Use thumbnail if available, otherwise full image
    display_image = thumbnail_path if thumbnail_path and Path(thumbnail_path).exists() else image_path

    # Card container
    with st.container():
        # Display image
        if Path(display_image).exists():
            st.image(display_image, use_container_width=True)
        else:
            st.warning("Image not found")

        # Project name
        st.markdown(f"**{project_name}**")

        # Creator and date
        try:
            created_date = datetime.fromisoformat(created_at).strftime("%b %d, %Y")
        except:
            created_date = "Unknown date"

        st.caption(f"By {creator_name} • {created_date}")

        # Action buttons
        col1, col2 = st.columns(2)

        with col1:
            # View prompt button with expander
            with st.expander("🔍 View Prompt"):
                st.text_area(
                    "Prompt",
                    value=prompt,
                    height=100,
                    key=f"prompt_{generation_id}",
                    disabled=True,
                    label_visibility="collapsed"
                )

        with col2:
            # View full image button
            if st.button("🖼️ View Full", key=f"view_{generation_id}", use_container_width=True):
                st.session_state[f"show_full_{generation_id}"] = True

        # Show full image in modal/expander if button clicked
        if st.session_state.get(f"show_full_{generation_id}", False):
            with st.expander("Full Image", expanded=True):
                if Path(image_path).exists():
                    st.image(image_path, use_container_width=True)

                    # Download button
                    with open(image_path, "rb") as f:
                        st.download_button(
                            label="💾 Download",
                            data=f.read(),
                            file_name=f"{project_name}.png",
                            mime="image/png",
                            key=f"download_{generation_id}"
                        )

                if st.button("Close", key=f"close_{generation_id}"):
                    st.session_state[f"show_full_{generation_id}"] = False
                    st.rerun()

        st.markdown("---")


def render_content_grid(generations: list, columns: int = 3):
    """
    Render multiple content cards in a grid layout.

    Args:
        generations: List of generation objects
        columns: Number of columns in grid
    """

    if not generations:
        st.info("No content to display yet. Start creating in the Chat page!")
        return

    # Create columns for grid
    cols = st.columns(columns)

    for idx, generation in enumerate(generations):
        col_idx = idx % columns

        with cols[col_idx]:
            render_content_card(
                generation_id=str(generation.id),
                image_path=generation.generated_image_url or "",
                project_name=generation.project_name or "Untitled",
                creator_name=generation.user.name if hasattr(generation, 'user') else "Unknown",
                created_at=generation.created_at.isoformat() if generation.created_at else "",
                prompt=generation.final_prompt or "No prompt available",
                thumbnail_path=generation.thumbnail_url
            )


def render_empty_state(message: str = "No content available"):
    """
    Render an empty state when there's no content.

    Args:
        message: Message to display
    """
    st.markdown(f"""
    <div style="text-align: center; padding: 4rem 2rem; color: #b0b3b8;">
        <h3>📭 {message}</h3>
        <p>Start creating amazing content with AI!</p>
    </div>
    """, unsafe_allow_html=True)
