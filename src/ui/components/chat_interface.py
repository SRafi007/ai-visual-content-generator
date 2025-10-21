"""
Chat Interface Component

Renders the conversational chat interface for prompt building.
"""

import streamlit as st
from typing import List, Dict, Any, Optional
from datetime import datetime
from src.utils.logger import get_logger

logger = get_logger(__name__)


def inject_messenger_css():
    """Inject custom CSS for minimalistic chat interface."""
    st.markdown("""
    <style>
    /* Hide default Streamlit chat styling */
    .stChatMessage {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
    }

    /* Messages container - simple and clean */
    .messages-container {
        height: 600px;
        overflow-y: auto;
        overflow-x: hidden;
        padding: 20px;
        background: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        margin-bottom: 16px;
    }

    /* Simple scrollbar */
    .messages-container::-webkit-scrollbar {
        width: 6px;
    }

    .messages-container::-webkit-scrollbar-track {
        background: #f5f5f5;
    }

    .messages-container::-webkit-scrollbar-thumb {
        background: #ccc;
        border-radius: 3px;
    }

    .messages-container::-webkit-scrollbar-thumb:hover {
        background: #999;
    }

    /* Message bubble - minimalistic */
    .message-bubble {
        display: flex;
        margin-bottom: 16px;
        align-items: flex-start;
    }

    /* Assistant message (left side) */
    .message-bubble.assistant {
        justify-content: flex-start;
    }

    .message-bubble.assistant .message-content {
        background: #f5f5f5;
        color: #333;
        border-radius: 18px 18px 18px 4px;
        max-width: 70%;
    }

    /* User message (right side) */
    .message-bubble.user {
        justify-content: flex-end;
    }

    .message-bubble.user .message-content {
        background: #667eea;
        color: white;
        border-radius: 18px 18px 4px 18px;
        max-width: 70%;
    }

    /* Message content */
    .message-content {
        padding: 12px 16px;
        font-size: 14px;
        line-height: 1.5;
        word-wrap: break-word;
    }

    /* Action buttons */
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
    }

    /* Compact sidebar */
    .compact-sidebar {
        position: sticky;
        top: 80px;
        background: white;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        padding: 16px;
    }

    .compact-sidebar h4 {
        margin: 0 0 12px 0;
        font-size: 13px;
        color: #667eea;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .progress-circle {
        width: 70px;
        height: 70px;
        border-radius: 50%;
        background: conic-gradient(#667eea 0deg, #667eea var(--progress), #e0e0e0 var(--progress), #e0e0e0 360deg);
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 10px auto;
        position: relative;
    }

    .progress-circle::before {
        content: '';
        position: absolute;
        width: 56px;
        height: 56px;
        border-radius: 50%;
        background: white;
    }

    .progress-text {
        position: relative;
        z-index: 1;
        font-size: 16px;
        font-weight: bold;
        color: #667eea;
    }

    .status-badge {
        display: inline-block;
        padding: 6px 12px;
        border-radius: 16px;
        font-size: 11px;
        font-weight: 600;
        text-align: center;
        width: 100%;
    }

    .status-ready {
        background: #38ef7d;
        color: white;
    }

    .status-building {
        background: #f5576c;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)


def render_chat_messages(messages: List[Dict[str, str]]):
    """
    Render chat messages in minimalistic style.

    Args:
        messages: List of message dicts with 'role' and 'content'
    """
    inject_messenger_css()

    for idx, message in enumerate(messages):
        role = message.get("role", "user")
        content = message.get("content", "")

        # Create message bubble - no avatars, just clean bubbles
        bubble_class = f"message-bubble {role}"

        # HTML for message bubble
        message_html = f"""
        <div class="{bubble_class}">
            <div class="message-content">
                {content}
            </div>
        </div>
        """

        st.markdown(message_html, unsafe_allow_html=True)

    # Auto-scroll to bottom after rendering messages
    scroll_script = """
    <script>
    const container = document.getElementById('messages-container');
    if (container) {
        container.scrollTop = container.scrollHeight;
    }
    // Fallback for streamlit containers
    setTimeout(() => {
        const containers = document.querySelectorAll('.messages-container');
        containers.forEach(c => {
            c.scrollTop = c.scrollHeight;
        });
    }, 100);
    </script>
    """
    st.markdown(scroll_script, unsafe_allow_html=True)


def render_chat_input(key: str = "chat_input") -> Optional[str]:
    """
    Render the chat input field.

    Args:
        key: Unique key for the input widget

    Returns:
        User input text or None
    """
    return st.chat_input("Tell me about the image you want to create...", key=key)


def render_prompt_preview(prompt: Dict[str, Any], completion_percentage: int):
    """
    Render a live preview of the prompt being built.

    Args:
        prompt: Current prompt state
        completion_percentage: Percentage of completion (0-100)
    """
    inject_messenger_css()

    st.markdown('<div class="prompt-preview-card">', unsafe_allow_html=True)
    st.markdown("### 📝 Current Prompt")

    # Progress bar
    st.progress(completion_percentage / 100, text=f"{completion_percentage}% Complete")

    st.markdown("<br>", unsafe_allow_html=True)

    p = prompt.get("prompt", {})
    elements = p.get("elements", {})
    style = p.get("style", {})

    # Display key fields with better styling
    def render_field(label: str, value: Any):
        display_value = value if value and value != "Not set" else "—"
        if isinstance(display_value, list):
            display_value = ", ".join(display_value) if display_value else "—"

        field_html = f"""
        <div style="margin-bottom: 12px;">
            <div style="font-size: 12px; color: #667eea; font-weight: 600; margin-bottom: 4px;">{label}</div>
            <div style="font-size: 14px; color: #202124;">{display_value}</div>
        </div>
        """
        st.markdown(field_html, unsafe_allow_html=True)

    # Display fields
    render_field("📌 Title", p.get("title", "Not set"))
    render_field("🎯 Subject", elements.get("subject", "Not set"))
    render_field("😊 Mood", elements.get("mood", "Not set"))
    render_field("🎨 Colors", elements.get("color_palette", []))
    render_field("🖼️ Style", style.get("genre", []))
    render_field("✨ Art Form", style.get("art_form", []))
    render_field("🌍 Environment", elements.get("environment", "Not set"))
    render_field("📐 Composition", elements.get("composition", "Not set"))

    st.markdown('</div>', unsafe_allow_html=True)


def render_json_expander(prompt: Dict[str, Any]):
    """
    Render an expandable section showing the raw JSON.

    Args:
        prompt: Current prompt state
    """
    with st.expander("View Full JSON"):
        st.json(prompt)


def render_action_buttons(is_complete: bool, missing_fields: List[str]) -> Dict[str, bool]:
    """
    Render action buttons for the chat interface.

    Args:
        is_complete: Whether the prompt is complete
        missing_fields: List of missing field names

    Returns:
        Dictionary of button states {button_name: was_clicked}
    """
    col1, col2, col3, col4 = st.columns(4)

    buttons = {}

    with col1:
        if is_complete:
            buttons["generate"] = st.button("🎨 Generate Image", type="primary", use_container_width=True)
        else:
            st.button(
                "🎨 Generate Image",
                disabled=True,
                help=f"Complete these fields first: {', '.join(missing_fields)}",
                use_container_width=True
            )
            buttons["generate"] = False

    with col2:
        buttons["autofill"] = st.button("✨ Auto-fill Missing", use_container_width=True)

    with col3:
        buttons["reset"] = st.button("🔄 Start Over", use_container_width=True)

    with col4:
        buttons["export"] = st.button("💾 Export JSON", use_container_width=True)

    return buttons


def render_welcome_message():
    """Render the initial welcome message inside chat - minimalistic placeholder."""
    inject_messenger_css()

    welcome_html = """
    <div style="display: flex; align-items: center; justify-content: center; height: 100%; color: #999; font-size: 14px;">
        Type a message to start...
    </div>
    """
    st.markdown(welcome_html, unsafe_allow_html=True)


def render_typing_indicator():
    """Show a typing indicator while processing."""
    typing_html = """
    <div style="display: flex; align-items: center; margin-bottom: 16px;">
        <div class="message-avatar" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 18px; margin: 0 8px;">🤖</div>
        <div class="typing-indicator">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
    </div>
    """
    st.markdown(typing_html, unsafe_allow_html=True)


def render_error_message(error: str):
    """
    Render an error message in the chat.

    Args:
        error: Error message to display
    """
    st.error(f"⚠️ {error}")


def render_success_message(message: str):
    """
    Render a success message.

    Args:
        message: Success message to display
    """
    st.success(f"✅ {message}")


def render_info_message(message: str):
    """
    Render an info message.

    Args:
        message: Info message to display
    """
    st.info(f"ℹ️ {message}")


def render_missing_fields_warning(missing_fields: List[str]):
    """
    Render a warning about missing fields.

    Args:
        missing_fields: List of missing field names
    """
    if missing_fields:
        st.warning(f"**Still needed:** {', '.join(missing_fields)}")


def render_prompt_summary_card(summary: Dict[str, Any]):
    """
    Render a summary card of the current prompt.

    Args:
        summary: Summary dictionary from PromptBuilderService
    """
    inject_messenger_css()

    st.markdown('<div class="prompt-preview-card">', unsafe_allow_html=True)
    st.markdown("### 📊 Quick Summary")

    # Metrics with custom styling
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Completion", f"{summary['completion_percentage']}%")

    with col2:
        status = "✅ Ready" if summary['is_complete'] else "⏳ Building"
        st.metric("Status", status)

    with col3:
        missing_count = len(summary['missing_fields'])
        st.metric("Missing", missing_count)

    st.markdown("<br>", unsafe_allow_html=True)

    # Display main info with styled labels
    if summary.get('title'):
        st.markdown(f"<div style='font-size: 14px; margin-bottom: 8px;'><strong style='color: #667eea;'>Title:</strong> {summary['title']}</div>", unsafe_allow_html=True)
    if summary.get('subject'):
        st.markdown(f"<div style='font-size: 14px; margin-bottom: 8px;'><strong style='color: #667eea;'>Subject:</strong> {summary['subject']}</div>", unsafe_allow_html=True)
    if summary.get('mood'):
        st.markdown(f"<div style='font-size: 14px; margin-bottom: 8px;'><strong style='color: #667eea;'>Mood:</strong> {summary['mood']}</div>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


def render_compact_sidebar(summary: Dict[str, Any], prompt: Dict[str, Any]):
    """
    Render a compact sidebar with minimal but important info.

    Args:
        summary: Summary dictionary from PromptBuilderService
        prompt: Current prompt state
    """
    inject_messenger_css()

    # Calculate progress degrees
    progress_pct = summary['completion_percentage']
    progress_deg = (progress_pct * 3.6)  # Convert to degrees

    is_complete = summary['is_complete']
    status_class = "status-ready" if is_complete else "status-building"
    status_text = "✓ Ready" if is_complete else "Building..."

    # Build missing fields text if needed
    missing_html = ""
    if not is_complete:
        missing_count = len(summary['missing_fields'])
        field_text = "fields" if missing_count != 1 else "field"
        missing_html = f'<div style="text-align: center; margin-top: 12px; font-size: 12px; color: #888;">{missing_count} {field_text} remaining</div>'

    # Build complete HTML in one go
    sidebar_html = f"""
    <div class="compact-sidebar">
        <h4>Progress</h4>
        <div class="progress-circle" style="--progress: {progress_deg}deg;">
            <div class="progress-text">{progress_pct}%</div>
        </div>
        <div class="status-badge {status_class}" style="margin-top: 12px;">
            {status_text}
        </div>
        {missing_html}
    </div>
    """

    st.markdown(sidebar_html, unsafe_allow_html=True)

    # Optional: Add collapsible details section
    with st.expander("📋 Details", expanded=False):
        p = prompt.get("prompt", {})
        elements = p.get("elements", {})

        if p.get("title"):
            st.caption(f"**Title:** {p.get('title')}")
        if elements.get("subject"):
            st.caption(f"**Subject:** {elements.get('subject')}")
        if elements.get("mood"):
            st.caption(f"**Mood:** {elements.get('mood')}")
