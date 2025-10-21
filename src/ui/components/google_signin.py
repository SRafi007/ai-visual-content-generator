# src/ui/components/google_signin.py
"""Google Sign-In component for Streamlit."""

import streamlit as st
import streamlit.components.v1 as components


def render_google_signin_button(client_id: str) -> str:
    """
    Render Google Sign-In button and return the ID token if authenticated.

    Args:
        client_id: Google OAuth Client ID

    Returns:
        ID token string if user signed in, None otherwise
    """

    # HTML/JavaScript for Google Sign-In
    google_signin_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="google-signin-client_id" content="{client_id}">
        <script src="https://accounts.google.com/gsi/client" async defer></script>
        <style>
            body {{
                margin: 0;
                padding: 20px;
                background-color: transparent;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 80px;
            }}
            #buttonDiv {{
                display: flex;
                justify-content: center;
            }}
        </style>
    </head>
    <body>
        <div id="buttonDiv"></div>

        <script>
            function handleCredentialResponse(response) {{
                // Send token back to Streamlit
                window.parent.postMessage({{
                    type: 'google_signin',
                    credential: response.credential
                }}, '*');
            }}

            window.onload = function() {{
                google.accounts.id.initialize({{
                    client_id: '{client_id}',
                    callback: handleCredentialResponse
                }});

                google.accounts.id.renderButton(
                    document.getElementById('buttonDiv'),
                    {{
                        theme: 'filled_blue',
                        size: 'large',
                        width: 300,
                        text: 'signin_with',
                        shape: 'rectangular'
                    }}
                );

                // Auto-prompt if not already signed in
                // google.accounts.id.prompt();
            }};
        </script>
    </body>
    </html>
    """

    # Render the component
    components.html(google_signin_html, height=100)

    # Check session state for received token
    if "google_credential" in st.session_state:
        credential = st.session_state.google_credential
        del st.session_state.google_credential  # Clear after reading
        return credential

    return None


def init_google_signin_listener():
    """
    Initialize JavaScript listener for Google Sign-In messages.
    Call this once at the start of your app.
    """

    listener_js = """
    <script>
    window.addEventListener('message', function(event) {
        if (event.data.type === 'google_signin') {
            // Store credential in Streamlit session
            window.parent.postMessage({
                type: 'streamlit:setComponentValue',
                value: {credential: event.data.credential}
            }, '*');
        }
    });
    </script>
    """

    components.html(listener_js, height=0)
