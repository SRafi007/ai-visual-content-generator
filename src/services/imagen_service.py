# src\services\imagen_service.py
from typing import Dict, Optional
import time
import base64
from io import BytesIO
from PIL import Image
from google import genai
from google.genai import types

from config.settings import get_settings
from src.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


class ImagenService:
    """Imagen API service for image generation using Gemini 2.0 Flash."""

    def __init__(self):
        self.model_name = settings.IMAGEN_MODEL
        self.client = genai.Client(api_key=settings.IMAGEN_API_KEY)
        logger.info(f"Initialized ImagenService with model: {self.model_name}")

    def generate_image(self, prompt: str, parameters: Optional[Dict] = None) -> bytes:
        """Generate image from prompt using Gemini 2.0 Flash."""
        params = parameters or {}

        logger.info(f"Generating image with prompt: {prompt[:100]}...")

        try:
            # Build the full prompt with style if provided
            full_prompt = prompt
            if params.get("style"):
                full_prompt = f"{prompt}, {params['style']} style"

            # Generate image using the client - following exact working implementation
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[full_prompt],
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"]
                ),
            )

            # Extract image data from response
            for candidate in response.candidates:
                for part in candidate.content.parts:
                    # Return image data directly (already in bytes format)
                    if part.inline_data and part.inline_data.data:
                        img_data = part.inline_data.data
                        # Data is already bytes, no need to decode
                        if isinstance(img_data, str):
                            # Fallback: decode if it's base64 string
                            img_data = base64.b64decode(img_data)
                        logger.info("[OK] Image generated successfully")
                        return img_data

            raise Exception("No image data found in response")

        except Exception as e:
            logger.error(f"[ERROR] Image generation failed: {e}")
            raise

    def generate_with_retry(
        self, prompt: str, parameters: Optional[Dict] = None, max_retries: int = 3
    ) -> bytes:
        """Generate image with retry logic."""
        last_error = None

        for attempt in range(max_retries):
            try:
                logger.info(f"Generation attempt {attempt + 1}/{max_retries}")
                return self.generate_image(prompt, parameters)

            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed: {e}")

                if attempt < max_retries - 1:
                    wait_time = 2**attempt  # Exponential backoff
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)

        logger.error(f"All {max_retries} attempts failed")
        raise last_error


if __name__ == "__main__":
    """Test the ImagenService"""
    print("=" * 60)
    print("Testing ImagenService")
    print("=" * 60)

    try:
        # Initialize service
        print("\n[1/3] Initializing service...")
        service = ImagenService()
        print(f"✓ Service initialized with model: {service.model_name}")

        # Test prompt
        test_prompt = "a beautiful sunset over mountains in digital art style"
        print(f"\n[2/3] Generating test image...")
        print(f"Prompt: '{test_prompt}'")

        # Generate image
        img_data = service.generate_with_retry(test_prompt)

        # Save test image using PIL (following working implementation)
        print(f"\n[3/3] Saving test image...")
        img = Image.open(BytesIO(img_data))
        output_path = "test_generated_image.png"
        img.save(output_path)

        print("\n" + "=" * 60)
        print("✓ TEST PASSED!")
        print("=" * 60)
        print(f"✓ Image saved to: {output_path}")
        print(f"✓ Image size: {len(img_data):,} bytes")
        print(f"✓ Image dimensions: {img.size}")
        print("=" * 60)

    except Exception as e:
        print("\n" + "=" * 60)
        print("✗ TEST FAILED!")
        print("=" * 60)
        print(f"Error: {e}")
        print("=" * 60)
        import traceback

        traceback.print_exc()
