# working test model
from google import genai
from google.genai import types
from io import BytesIO
from PIL import Image
import base64

client = genai.Client(api_key="AIzaSyDoRT_ttpqwSh4n2TZYaVTY1eWGr6lwwvo")

response = client.models.generate_content(
    model="gemini-2.0-flash-exp",
    contents=[
        "Generate a story about a cute baby turtle in a 3D digital art style. For each scene, generate an image."
    ],
    config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
)

for idx, candidate in enumerate(response.candidates):
    print(f"\nCandidate {idx + 1}:")
    for part_i, part in enumerate(candidate.content.parts):
        # Print story text
        if part.text:
            print("Text:", part.text[:300], "...")

        # Decode and save image
        if part.inline_data and part.inline_data.data:
            mime_type = part.inline_data.mime_type or "image/png"
            img_data = base64.b64decode(part.inline_data.data)  # ✅ decode base64
            img = Image.open(BytesIO(img_data))
            filename = f"turtle_scene_{idx + 1}_{part_i + 1}.png"
            img.save(filename)
            print(f"✅ Saved: {filename}")
