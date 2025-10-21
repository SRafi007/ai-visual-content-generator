# src/ui/components/google_auth_button.py
"""Simple Google Sign-In button component."""

import streamlit as st
import streamlit.components.v1 as components


def render_google_signin(client_id: str, redirect_uri: str = "http://localhost:8501"):
    """
    Render Google Sign-In button using Google Identity Services.

    Args:
        client_id: Your Google OAuth Client ID
        redirect_uri: Redirect URI after authentication
    """

    # HTML with Google Identity Services
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://accounts.google.com/gsi/client" async defer></script>
        <style>
            body {{
                margin: 0;
                padding: 0;
                background: transparent;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 60px;
            }}
        </style>
    </head>
    <body>
        <div id="g_id_onload"
             data-client_id="{client_id}"
             data-callback="handleCredentialResponse">
        </div>
        <div class="g_id_signin"
             data-type="standard"
             data-size="large"
             data-theme="filled_blue"
             data-text="signin_with"
             data-shape="rectangular"
             data-width="300">
        </div>

        <script>
            function handleCredentialResponse(response) {{
                // Store token in parent window
                if (window.Streamlit) {{
                    window.Streamlit.setComponentValue(response.credential);
                }} else {{
                    // Fallback: use localStorage
                    localStorage.setItem('google_token', response.credential);
                    // Reload parent
                    window.parent.location.reload();
                }}
            }}
        </script>
    </body>
    </html>
    """

    # Render component and return token if available
    result = components.html(html_code, height=60)

    return result
