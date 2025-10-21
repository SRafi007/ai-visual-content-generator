"""Debug script to inspect Imagen service response format."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from google import genai
from google.genai import types
from config.settings import get_settings
import base64

settings = get_settings()

def debug_imagen_response():
    """Debug the actual response from Imagen service."""
    print("=" * 70)
    print("Debugging Imagen Service Response")
    print("=" * 70)

    # Initialize client
    client = genai.Client(api_key=settings.IMAGEN_API_KEY)
    model_name = settings.IMAGEN_MODEL

    print(f"\nModel: {model_name}")
    print(f"API Key: {settings.IMAGEN_API_KEY[:10]}..." if settings.IMAGEN_API_KEY else "NOT SET")

    # Simple test prompt
    test_prompt = "a red apple on a white background"
    print(f"\nTest Prompt: '{test_prompt}'")

    print("\n" + "-" * 70)
    print("Sending request...")
    print("-" * 70)

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=[test_prompt],
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"]
            ),
        )

        print(f"\n[OK] Response received!")
        print(f"  Type: {type(response)}")
        print(f"  Candidates: {len(response.candidates)}")

        for idx, candidate in enumerate(response.candidates):
            print(f"\n--- Candidate {idx} ---")
            print(f"  Finish reason: {candidate.finish_reason}")
            print(f"  Parts: {len(candidate.content.parts)}")

            for part_idx, part in enumerate(candidate.content.parts):
                print(f"\n  --- Part {part_idx} ---")
                print(f"    Type: {type(part)}")
                print(f"    Has text: {hasattr(part, 'text') and part.text is not None}")
                print(f"    Has inline_data: {hasattr(part, 'inline_data') and part.inline_data is not None}")

                if hasattr(part, 'text') and part.text:
                    print(f"    Text content: {part.text[:100]}...")

                if hasattr(part, 'inline_data') and part.inline_data:
                    print(f"    Inline data found!")
                    print(f"    MIME type: {part.inline_data.mime_type if hasattr(part.inline_data, 'mime_type') else 'N/A'}")

                    # Check if data is present
                    if hasattr(part.inline_data, 'data') and part.inline_data.data:
                        data = part.inline_data.data
                        print(f"    Data type: {type(data)}")
                        print(f"    Data length: {len(data) if isinstance(data, (str, bytes)) else 'N/A'}")

                        # Try to decode
                        try:
                            if isinstance(data, str):
                                decoded = base64.b64decode(data)
                                print(f"    [OK] Base64 decoded successfully!")
                                print(f"    Decoded length: {len(decoded)} bytes")

                                # Check if it's a valid image by looking at magic bytes
                                magic = decoded[:8].hex()
                                print(f"    Magic bytes (hex): {magic}")

                                # Common image format signatures
                                if magic.startswith('89504e47'):  # PNG
                                    print(f"    [OK] Detected format: PNG")
                                elif magic.startswith('ffd8ff'):  # JPEG
                                    print(f"    [OK] Detected format: JPEG")
                                elif magic.startswith('474946'):  # GIF
                                    print(f"    [OK] Detected format: GIF")
                                else:
                                    print(f"    [WARN] Unknown image format")
                                    print(f"    First 50 bytes: {decoded[:50]}")
                            elif isinstance(data, bytes):
                                print(f"    Data is already bytes")
                                magic = data[:8].hex()
                                print(f"    Magic bytes (hex): {magic}")
                        except Exception as decode_error:
                            print(f"    [ERROR] Decode error: {decode_error}")
                    else:
                        print(f"    [WARN] No data found in inline_data")

        print("\n" + "=" * 70)
        print("Debug completed successfully")
        print("=" * 70)

    except Exception as e:
        print(f"\n[ERROR] Error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_imagen_response()
