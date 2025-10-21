"""
Chat Page - Conversational Prompt Builder

This page provides an AI-powered conversational interface for building
image generation prompts. Users chat naturally with the AI, which guides
them through the process and builds a structured prompt.
"""

import streamlit as st
from pathlib import Path
import sys
import json
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.ui.components.navbar import render_navbar
from src.ui.components.chat_interface import (
    render_chat_messages,
    render_chat_input,
    render_prompt_preview,
    render_json_expander,
    render_action_buttons,
    render_welcome_message,
    render_error_message,
    render_success_message,
    render_missing_fields_warning,
    render_prompt_summary_card
)
from src.services.llm_service import LLMService
from src.services.prompt_builder_service import PromptBuilderService
from src.services.session_manager import SessionManager
from src.services.generation_service import GenerationService
from src.services.imagen_service import ImagenService
from src.services.storage_service import StorageService
from src.services.content_service import ContentService
from src.repositories.generation_repository import GenerationRepository
from src.repositories.content_repository import ContentRepository
from src.models.schemas.generation import GenerationCreate, GenerationUpdate, Message
from src.models.schemas.content import ContentCreate
from config.settings import get_settings
from config.redis import get_redis
from config.database import SessionLocal
from src.utils.logger import get_logger
from uuid import UUID

logger = get_logger(__name__)

# Page configuration
st.set_page_config(
    page_title="Chat - Arbor AI Studio",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Render navbar
render_navbar()


def init_services():
    """Initialize all required services."""
    settings = get_settings()

    # Check for user in session
    if "user" not in st.session_state:
        st.error("⚠️ Please select a user from the home page first.")
        st.stop()

    # Initialize database session and repository
    db = SessionLocal()
    gen_repo = GenerationRepository(db)

    # Initialize services
    redis_client = get_redis()
    session_manager = SessionManager(redis_client)
    llm_service = LLMService(api_key=settings.GEMINI_API_KEY)
    prompt_builder = PromptBuilderService()
    generation_service = GenerationService(gen_repo)
    imagen_service = ImagenService()  # No parameters - reads from settings
    storage_service = StorageService()

    return {
        "db": db,
        "session_manager": session_manager,
        "llm_service": llm_service,
        "prompt_builder": prompt_builder,
        "generation_service": generation_service,
        "imagen_service": imagen_service,
        "storage_service": storage_service
    }


def init_chat_state(services):
    """Initialize or load chat state from Redis."""
    user_email = st.session_state["user"]["email"]
    session_manager = services["session_manager"]
    prompt_builder = services["prompt_builder"]

    # Check if this is a fresh login (no chat_initialized flag)
    if "chat_initialized" not in st.session_state:
        # Clear old messages from Redis on fresh page load
        try:
            # Try to use the new method if available
            if hasattr(session_manager, 'clear_all_messages'):
                session_manager.clear_all_messages(user_email)
            else:
                # Fallback: clear session completely
                session_manager.clear_session(user_email)
        except Exception as e:
            logger.warning(f"Failed to clear old messages: {e}")
            # Continue anyway - just start fresh in Streamlit

        st.session_state.chat_initialized = True
        st.session_state.messages = []
        st.session_state.current_prompt = prompt_builder.create_new_prompt(user_email)

        try:
            session_manager.update_prompt_state(user_email, st.session_state.current_prompt)
        except Exception as e:
            logger.warning(f"Failed to save prompt state to Redis: {e}")
    else:
        # Get or create session
        session = session_manager.get_or_create_session(user_email)

        # Load messages
        if "messages" not in st.session_state:
            messages = session.get("messages", [])
            st.session_state.messages = messages

        # Load or create prompt state
        if "current_prompt" not in st.session_state:
            prompt_state = session_manager.get_prompt_state(user_email)
            if prompt_state:
                st.session_state.current_prompt = prompt_state
            else:
                # Create new prompt
                st.session_state.current_prompt = prompt_builder.create_new_prompt(user_email)
                try:
                    session_manager.update_prompt_state(user_email, st.session_state.current_prompt)
                except Exception as e:
                    logger.warning(f"Failed to save prompt state: {e}")


def save_chat_state(services):
    """Save chat state to Redis."""
    user_email = st.session_state["user"]["email"]
    session_manager = services["session_manager"]

    # Save messages
    session_manager.update_messages(user_email, st.session_state.messages)

    # Save prompt state
    session_manager.update_prompt_state(user_email, st.session_state.current_prompt)


def add_message(role: str, content: str):
    """Add a message to the conversation."""
    message = {"role": role, "content": content}
    st.session_state.messages.append(message)


def process_user_input(user_input: str, services):
    """Process user input and generate response."""
    try:
        llm_service = services["llm_service"]
        prompt_builder = services["prompt_builder"]

        # Add user message
        add_message("user", user_input)

        # Analyze input and extract fields
        with st.spinner("Analyzing your input..."):
            extracted_fields = llm_service.analyze_input(
                user_message=user_input,
                conversation_history=st.session_state.messages,
                current_prompt=st.session_state.current_prompt
            )

        # Update prompt with extracted fields
        if extracted_fields:
            st.session_state.current_prompt = prompt_builder.update_prompt_from_extraction(
                st.session_state.current_prompt,
                extracted_fields
            )

        # Generate next question or completion message
        with st.spinner("Thinking..."):
            next_question = llm_service.generate_next_question(
                current_prompt=st.session_state.current_prompt,
                conversation_history=st.session_state.messages
            )

        # Add assistant response
        add_message("assistant", next_question)

        # Save state
        save_chat_state(services)

        # Rerun to show new messages
        st.rerun()

    except Exception as e:
        logger.error(f"Error processing user input: {str(e)}")
        render_error_message(f"Failed to process your message: {str(e)}")


def handle_autofill(services):
    """Auto-fill missing fields using LLM."""
    try:
        llm_service = services["llm_service"]

        with st.spinner("Auto-filling missing fields..."):
            # Get user's overall intent from conversation
            user_intent = ""
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    user_intent += msg["content"] + " "

            # Auto-fill
            completed_prompt = llm_service.autofill_missing_fields(
                current_prompt=st.session_state.current_prompt,
                user_intent=user_intent.strip()
            )

            st.session_state.current_prompt = completed_prompt

            # Save state
            save_chat_state(services)

            # Add system message
            add_message("assistant", "I've auto-filled the missing fields based on our conversation. Please review and let me know if you'd like to change anything!")

            render_success_message("Prompt auto-completed!")
            st.rerun()

    except Exception as e:
        logger.error(f"Error auto-filling: {str(e)}")
        render_error_message(f"Failed to auto-fill: {str(e)}")


def handle_reset(services):
    """Reset the prompt and conversation."""
    try:
        prompt_builder = services["prompt_builder"]
        user_email = st.session_state["user"]["email"]

        # Create new prompt
        st.session_state.current_prompt = prompt_builder.create_new_prompt(user_email)

        # Clear messages
        st.session_state.messages = []

        # Save state
        save_chat_state(services)

        render_success_message("Started a new conversation!")
        st.rerun()

    except Exception as e:
        logger.error(f"Error resetting: {str(e)}")
        render_error_message(f"Failed to reset: {str(e)}")


def handle_export():
    """Export the prompt as JSON."""
    try:
        json_str = json.dumps(st.session_state.current_prompt, indent=2)
        st.download_button(
            label="Download JSON",
            data=json_str,
            file_name="image_prompt.json",
            mime="application/json"
        )
        render_success_message("Click the button above to download your prompt!")

    except Exception as e:
        logger.error(f"Error exporting: {str(e)}")
        render_error_message(f"Failed to export: {str(e)}")


def handle_generate(services):
    """Generate the image using the completed prompt."""
    try:
        prompt_builder = services["prompt_builder"]
        generation_service = services["generation_service"]
        imagen_service = services["imagen_service"]
        storage_service = services["storage_service"]

        user = st.session_state["user"]

        # Compile final prompt
        final_prompt = prompt_builder.compile_prompt_for_generation(st.session_state.current_prompt)

        # Show the final prompt
        st.markdown("### Final Prompt")
        st.info(final_prompt)

        # Ask for visibility
        visibility = st.radio(
            "Visibility",
            options=["private", "public"],
            format_func=lambda x: "🔒 Private (only you can see)" if x == "private" else "🌐 Public (visible on home feed)",
            horizontal=True,
            help="Choose who can see this generation"
        )

        # Create generation record
        with st.spinner("Creating generation record..."):
            raw_user_input = " ".join([msg["content"] for msg in st.session_state.messages if msg["role"] == "user"])

            # Convert messages to Message schema
            conversation_messages = [Message(**msg) for msg in st.session_state.messages]

            # Create generation using schema
            generation_create = GenerationCreate(
                user_id=UUID(user["id"]),
                conversation_messages=conversation_messages,
                final_prompt=final_prompt,
                raw_user_input=raw_user_input,
                selected_parameters=st.session_state.current_prompt.get("prompt", {}).get("output_preferences", {}),
                visibility=visibility
            )

            generation = generation_service.create_generation(generation_create)

            st.success(f"Project: **{generation.project_name}**")

        # Update status to generating
        generation_update = GenerationUpdate(status="generating")
        generation_service.update_generation(generation.id, generation_update)

        # Generate image
        with st.spinner("Generating your image... This may take a minute."):
            try:
                # Prepare generation parameters
                output_preferences = st.session_state.current_prompt.get("prompt", {}).get("output_preferences", {})
                generation_params = {
                    "aspect_ratio": output_preferences.get("aspect_ratio", "1:1"),
                    "style": output_preferences.get("style")
                }

                image_bytes = imagen_service.generate_image(
                    prompt=final_prompt,
                    parameters=generation_params
                )

                # Save image and thumbnail
                image_path, thumbnail_path = storage_service.save_image_with_thumbnail(
                    image_data=image_bytes,
                    generation_id=generation.id
                )

                # Update generation with paths and completed status
                update_data = GenerationUpdate(
                    status="completed",
                    generated_image_url=str(image_path),
                    thumbnail_url=str(thumbnail_path)
                )
                generation_service.update_generation(generation.id, update_data)

                # Create Content record for gallery display
                try:
                    content_repo = ContentRepository(services["db"])
                    content_service = ContentService(content_repo)

                    content_create = ContentCreate(
                        user_id=UUID(user["id"]),
                        generation_id=generation.id,
                        title=generation.project_name or "Untitled",
                        prompt=final_prompt,
                        generated_image_url=str(image_path),
                        thumbnail_url=str(thumbnail_path),
                        visibility=visibility
                    )

                    content_service.create_content(content_create)
                    logger.info(f"Content record created for generation {generation.id}")
                except Exception as content_error:
                    logger.error(f"Failed to create content record: {content_error}")
                    # Don't fail the whole process if content creation fails

                # Display image
                st.success("Image generated successfully!")
                st.image(image_bytes, caption=generation.project_name, use_container_width=True)

                # Show visibility status
                if visibility == "public":
                    st.info("✅ This image is now visible on the public home feed!")
                else:
                    st.info("🔒 This image is private. You can change visibility in your Profile page.")

                # Option to generate another
                if st.button("Create Another Image"):
                    handle_reset(services)

            except Exception as img_error:
                logger.error(f"Image generation failed: {str(img_error)}")
                update_data = GenerationUpdate(
                    status="failed",
                    generation_metadata={"error": str(img_error)}
                )
                generation_service.update_generation(generation.id, update_data)
                render_error_message(f"Image generation failed: {str(img_error)}")

    except Exception as e:
        logger.error(f"Error in generate workflow: {str(e)}")
        render_error_message(f"Failed to generate image: {str(e)}")


def main():
    """Main chat page logic."""
    # Inject CSS first
    from src.ui.components.chat_interface import inject_messenger_css, render_compact_sidebar
    inject_messenger_css()

    services = None
    try:
        # Initialize services
        services = init_services()

        # Initialize chat state
        init_chat_state(services)

        # Get current state
        prompt_builder = services["prompt_builder"]
        summary = prompt_builder.get_prompt_summary(st.session_state.current_prompt)

        # Main layout: Focus on chat with compact floating sidebar
        chat_col, sidebar_col = st.columns([5, 1], gap="medium")

        with chat_col:
            # Messages container - using st.container with height control
            with st.container(height=600, border=True):
                # Show welcome message if no messages
                if not st.session_state.messages:
                    render_welcome_message()
                else:
                    # Render existing messages
                    render_chat_messages(st.session_state.messages)

            # Chat input at bottom (outside chat window)
            st.markdown("<div style='margin-top: 16px;'>", unsafe_allow_html=True)
            user_input = render_chat_input()
            st.markdown("</div>", unsafe_allow_html=True)

            if user_input:
                process_user_input(user_input, services)

            # Action buttons below chat input
            st.markdown("<div style='margin-top: 15px;'>", unsafe_allow_html=True)
            buttons = render_action_buttons(summary["is_complete"], summary["missing_fields"])
            st.markdown("</div>", unsafe_allow_html=True)

            # Handle button clicks
            if buttons.get("generate"):
                handle_generate(services)

            if buttons.get("autofill"):
                handle_autofill(services)

            if buttons.get("reset"):
                handle_reset(services)

            if buttons.get("export"):
                handle_export()

        with sidebar_col:
            # Compact sidebar with collapsible sections
            render_compact_sidebar(summary, st.session_state.current_prompt)

    except Exception as e:
        logger.error(f"Error in chat page: {str(e)}")
        st.error(f"⚠️ An error occurred: {str(e)}")

        with st.expander("Error Details"):
            st.code(str(e))

    finally:
        # Close database session
        if services and "db" in services:
            services["db"].close()


if __name__ == "__main__":
    main()
