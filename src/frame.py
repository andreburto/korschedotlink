"""Generate a random frame prompt and a reference-based Grok image."""

import base64
import os
import random
import requests
import uuid

from datetime import datetime
from io import BytesIO
from pathlib import Path
from urllib.request import urlopen

import xai_sdk
from google import genai
from google.genai import types
from PIL import Image

from utils import FRAME_SETTINGS, FRAME_STYLES, GEMINI_TEXT_MODEL, GROK_IMAGE_MODEL

REFERENCE_IMAGE_FILE = "sexy_spy.jpg"


def get_reference_image() -> str:
    """Return a URL or file path to a reference image for Kirsche."""
    return os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "../refs", REFERENCE_IMAGE_FILE)


def generate_setting() -> str:
    """Return a short description of a randomly selected setting."""
    return random.choice(FRAME_SETTINGS)


def generate_text(client: genai.Client, prompt: str) -> str:
    """Request plain text from Gemini, rejecting empty responses."""
    response = client.models.generate_content(
        model=GEMINI_TEXT_MODEL,
        contents=prompt,
    )
    if not response.text or not response.text.strip():
        raise ValueError("Gemini returned no text for the frame prompt")
    return " ".join(response.text.split())


def generate_scene(client: genai.Client, setting: str) -> str:
    """Describe an activity one person could perform in the given setting."""
    return generate_text(
        client,
        "Describe one activity a person could perform in this setting: "
        f"{setting}. Return exactly one short, standalone sentence describing "
        "the person doing the activity. Keep it plausible and family-friendly. "
        "Return only the sentence, without labels or formatting. "
        "Always name the person performing the activity Kirsche."
    )


def generate_pov(client: genai.Client, scene: str) -> str:
    """Describe a viewpoint from which an observer could see the scene."""
    return generate_text(
        client,
        f"Scene: {scene}\n"
        "Write exactly one short sentence describing how an observer could "
        "see Kirsche performing this activity, including the viewing angle "
        "or the observer's position. Preserve the scene and activity; do not "
        "invent a different activity. Return only the sentence, without "
        "labels or formatting.",
    )


def generate_prompt(client: genai.Client) -> str:
    """Build the four labeled sections, passing setting to scene to POV."""
    style = random.choice(FRAME_STYLES)
    setting = generate_setting()
    scene = generate_scene(client, setting)
    pov = generate_pov(client, scene)
    return (
        f"style: {style}\n\n"
        f"setting: {setting}\n\n"
        f"scene: {scene}\n\n"
        f"pov: {pov}"
    )


def generate_image(client: xai_sdk.Client, prompt: str, orientation: str) -> Path:
    """Send the prompt and reference to Grok and save a genuine PNG image."""
    reference_image_path = get_reference_image()
    ext = reference_image_path.split(".")[-1].lower()    # Load image from file and encode as base64

    with open(reference_image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    response = client.image.sample(
        model=GROK_IMAGE_MODEL,
        prompt=(
            "Create a picture of Kirsche using the following frame prompt. "
            f"The orientation of the image should be {orientation}, with a 4:3 aspect ratio. "
            "Use the attached reference image for Kirsche's character design, "
            "and follow the style, setting, scene, and POV in the prompt. "
            "Kirsche is an adult woman with fox ears and a fox tail, but a human face. "
            "Keep the picture family-friendly.\n\n"
            f"{prompt}"
        ),
        image_url=f"data:image/{ext};base64,{image_data}",
    )

    image_content = requests.get(response.url).content

    images_dir = Path(__file__).resolve().parent.parent / "images"
    timestamp = datetime.now().strftime("%y%m%d%H%M%S")
    output_path = images_dir / f"frame_{timestamp}_{uuid.uuid4()}.png"
    with Image.open(BytesIO(image_content)) as generated_image:
        generated_image.load()
        images_dir.mkdir(parents=True, exist_ok=True)
        generated_image.save(output_path, format="PNG")
    return output_path


def check_trimmable_sides(client: genai.Client, image_path: Path) -> str:
    """Upload the image to Gemini and ask which two perpendicular sides could
    be cut without risk of trimming the head."""
    with open(image_path, "rb") as f:
        image_data = f.read()
    response = client.models.generate_content(
        model=GEMINI_TEXT_MODEL,
        contents=[
            "If the image needed to be trimmed, which two perpendicular sides "
            "could be cut without risk of trimming the head? Respond with "
            "exactly two words, chosen only from: left, right, top, bottom.",
            types.Part.from_bytes(data=image_data, mime_type="image/png"),
        ],
    )
    if not response.text or not response.text.strip():
        raise ValueError("Gemini returned no response for the trim check")
    return " ".join(response.text.split())


def resize_image(
    image_path: Path, trimmable_sides: str, width: int = 1200, height: int = 800
) -> Path:
    """Scale the image to the larger of width/height, keeping its aspect
    ratio, then fit it to the exact width and height: trimming any excess
    off the sides named in trimmable_sides, or padding with black borders
    if it falls short."""
    sides = trimmable_sides.lower().split()
    horizontal_side = next((side for side in sides if side in ("left", "right")), "right")
    vertical_side = next((side for side in sides if side in ("top", "bottom")), "bottom")

    with Image.open(image_path) as source_image:
        image = source_image.convert("RGB")

    orig_width, orig_height = image.size
    if width > orig_width and height > orig_height:
        # Both targets exceed the image already; just border it, no resizing.
        new_width, new_height = orig_width, orig_height
        resized = image
    else:
        if width >= height:
            scale = width / orig_width
        else:
            scale = height / orig_height
        new_width = max(1, round(orig_width * scale))
        new_height = max(1, round(orig_height * scale))
        resized = image.resize((new_width, new_height), Image.LANCZOS)

    if new_width > width:
        overflow = new_width - width
        src_x0 = overflow if horizontal_side == "left" else 0
        dst_x = 0
    else:
        src_x0 = 0
        dst_x = (width - new_width) // 2
    src_x1 = src_x0 + min(new_width, width)

    if new_height > height:
        overflow = new_height - height
        src_y0 = overflow if vertical_side == "top" else 0
        dst_y = 0
    else:
        src_y0 = 0
        dst_y = (height - new_height) // 2
    src_y1 = src_y0 + min(new_height, height)

    cropped = resized.crop((src_x0, src_y0, src_x1, src_y1))
    final_image = Image.new("RGB", (width, height), (0, 0, 0))
    final_image.paste(cropped, (dst_x, dst_y))
    final_image.save(image_path, format="PNG")
    return image_path


def main() -> None:
    """Print a Gemini frame prompt, generate its Grok image, print its path,
    and ask Gemini which sides could be trimmed without cutting off the head."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    xai_api_key = os.getenv("XAI_API_KEY")
    if not xai_api_key:
        raise ValueError("XAI_API_KEY environment variable not set")
    with genai.Client(api_key=api_key) as client:
        prompt = generate_prompt(client)
        print(prompt)
        grok_client = xai_sdk.Client(api_key=xai_api_key)
        output_path = generate_image(grok_client, prompt, orientation="portrait")
        print(f"\nSaved image: {output_path}")
        trimmable_sides = check_trimmable_sides(client, output_path)
        print(f"Trimmable sides: {trimmable_sides}")
        resize_image(output_path, trimmable_sides)
        print(f"Resized image: {output_path}")


if __name__ == "__main__":
    main()
