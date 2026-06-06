"""
Scratch app for testing Kirsche image generation with Gemini.

This is a prototype app for testing new ideas. It is not intended for 
production use and may be deleted or refactored in the future.
"""

import os
import random
import sys
import uuid

from pathlib import Path
from time import sleep

from google import genai
from google.genai import types

from korsche_sync import DEFAULT_GEMINI_IMAGE_MODEL, DEFAULT_GEMINI_PROMPT_MODEL, enhance_prompt_with_gemini
from prompt_maker import PROMPT_DATA, random_sample

REFS_DIR = Path("refs")


def get_random_reference_image():
    """
    Pick a random image from the refs directory.
    
    Returns:
        Path: Path to a random reference image file.
    
    Raises:
        ValueError: If no images are found in the refs directory.
    """
    # refs_dir is already defined globally
    image_extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]
    
    image_files = [
        f for f in REFS_DIR.iterdir() 
        if f.is_file() and f.suffix.lower() in image_extensions
    ]
    
    if not image_files:
        raise ValueError("No images found in refs directory")
    
    return random.choice(image_files)


def generate_kirsche_image(reference_image_path, setting, pose):
    """
    Generate an image of Kirsche using Gemini AI.
    
    Args:
        reference_image_path (Path): Path to the reference image file.
        setting (str): The setting to include in the prompt (e.g. "in a kitchen").
        pose (str): The pose to include in the prompt (e.g. "cooking
    
    Returns:
        str: Path to the generated image file.
    """
    # Get API key from environment
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    
    # Initialize the client
    client = genai.Client(api_key=api_key)
    
    # Read the reference image
    print(f"Reading reference image from: {reference_image_path}")
    with open(reference_image_path, "rb") as f:
        reference_image_data = f.read()
    
    # Create the prompt
    prompt = (f"Create an image of Kirsche {setting} {pose}."
              " Use the reference image for style and character design cues for Kirsche."
              " Keep the style to a 2D cartoon like One Piece, Bleach, or Sailor Moon."
              " Stay PG and family-friendly. Kirsche is an adult woman.")
    
    # Generate the image
    response = client.models.generate_content(
        model=DEFAULT_GEMINI_IMAGE_MODEL,
        contents=[
            types.Part.from_bytes(
                data=reference_image_data,
                mime_type=f"image/{str(reference_image_path).split('.')[-1].lower()}"
            ),
            enhance_prompt_with_gemini(
                prompt, DEFAULT_GEMINI_PROMPT_MODEL, api_key)
        ]
    )
    
    # Get the generated image from response
    generated_image = None

    try:
      generated_image = response.candidates[0].content.parts[0].inline_data.data
    except (IndexError, AttributeError) as e:
        print(f"Error parsing response: {response}")
        raise ValueError("Failed to generate image") from e
    
    # Create images directory if it doesn't exist
    images_dir = Path("images")
    images_dir.mkdir(exist_ok=True)
    
    # Generate unique filename
    filename = f"{uuid.uuid4()}.png"
    output_path = images_dir / filename
    
    # Save the generated image
    with open(output_path, "wb") as f:
        f.write(generated_image)
    
    return str(output_path)


def main():
    """
    Main function to run the scratch app workflow.
    """
    prompt_by_file_name = {
        "trad_wife": "homemaker",
        "workout": "fitness enthusiast",
        "snoop": "snoop",
        "sexy_spy": "damsel in distress",
        "star_trek": "star trek fan",
        "army": "army",
        "dance_club": "party girl",
        "maid": "maid",
    }

    try:
        if sys.argv and len(sys.argv) > 1:
            reference_image = [
                f for f in REFS_DIR.iterdir()
                if f.is_file() and f.name.lower().startswith(str(sys.argv[1]).lower())][0]
            # reference_image = str(reference_image).replace('\\', path_sep)  # Normalize path separator for Windows
            print(f"Using reference image from command line argument: {reference_image}")
        else:
            # Step 1: Pick a random reference image
            reference_image = get_random_reference_image()
            print(f"Selected reference image: {reference_image}")

        file_name = str(reference_image).split(os.path.sep)[-1].split(".")[0]
        print(f"Reference image file name (without extension): {file_name}")
        
        setting = random_sample(PROMPT_DATA[prompt_by_file_name[file_name]]["setting"])
        pose = random_sample(PROMPT_DATA[prompt_by_file_name[file_name]]["pose"])
        print(f"Using setting: {setting} and pose: {pose} for prompt.")
        
        for _ in range(3):
            print("Generating image...")
            try:
                output_path = generate_kirsche_image(reference_image, setting, pose)
                print(f"Generated image saved to: {output_path}")
                break
            except Exception as e:
                print(f"Error during image generation: {e}")
                print("Retrying...")
                sleep(2)  # Wait before retrying
        
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
