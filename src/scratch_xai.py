"""
Scratch app for testing Kirsche image generation with Gemini.

This is a prototype app for testing new ideas. It is not intended for 
production use and may be deleted or refactored in the future.
"""

import base64
import os
import random
import requests
import sys
import uuid
import xai_sdk

from pathlib import Path
from time import sleep
from xai_sdk.chat import user

from prompt_maker import PROMPT_DATA, random_sample

REFS_DIR = Path("refs")
GROK_TEXT_MODEL = "grok-4.5-latest"
GROK_IMAGE_MODEL = "grok-imagine-image-quality"


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


def expand_prompt(client, setting, pose):
    """
    Expand the prompt with additional details.
    
    Args:
        client (xai_sdk.Client): The initialized XAI client.
        setting (str): The setting to include in the prompt.
        pose (str): The pose to include in the prompt.
    
    Returns:
        str: The expanded prompt.
    """
    prompt = (f"Give me a three sentence description of Kirsche {setting} {pose}."
              " Include details about her setting, background, pose, and posture."
              " Do not include any descriptions about Kirsche or her clothing."
              " Stay PG and family-friendly.")    
    chat = client.chat.create(GROK_TEXT_MODEL)
    chat.append(user(prompt))
    return chat.sample().content
    

def generate_kirsche_image_xai(client, reference_image_path, description):
    """
    Generate an image of Kirsche using Gemini AI.
    
    Args:
        client (xai_sdk.Client): The initialized XAI client.
        reference_image_path (Path): Path to the reference image file.
        description (str): Description of Kirsche to guide image generation.
    
    Returns:
        str: Path to the generated image file.
    """
    
    # Read the reference image
    print(f"Reading reference image from: {reference_image_path}")
    # Load image from file and encode as base64
    with open(reference_image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")
    
    # Create the prompt
    prompt = (f"Create an image of Kirsche based on this: \"{description}\"."
              " Use the reference image for style and character design cues for Kirsche."
              " Keep the style to a 2D cartoon like One Piece, Bleach, or Naruto."
              " Stay PG and family-friendly. Kirsche is an adult woman.")
    ext = reference_image_path.suffix.lower().lstrip(".")
    response = client.image.sample(
        prompt=prompt,
        model=GROK_IMAGE_MODEL,
        image_url=f"data:image/{ext};base64,{image_data}",
    )

    # Create images directory if it doesn't exist
    images_dir = Path("images")
    images_dir.mkdir(exist_ok=True)
    # Generate unique filename
    filename = f"xai_{uuid.uuid4()}.jpg"
    output_path = images_dir / filename
    # Save the generated image
    with open(output_path, "wb") as f:
        f.write(requests.get(response.url).content)

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
        # Initialize the client
        client = xai_sdk.Client(api_key=os.getenv("XAI_API_KEY"))

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

        image_prompt = expand_prompt(client, setting, pose)
        print(f"Expanded prompt: {image_prompt}")

        for _ in range(3):
            print("Generating image...")
            try:
                output_path = generate_kirsche_image_xai(client, reference_image, image_prompt)
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
