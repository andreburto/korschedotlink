"""
Character sheet maker script.

This module generates new character sheets using the Gemini prompt model.
It creates a new profession, generates an outfit description, and creates
a character sheet image using a reference image as a baseline.
"""

import os
import uuid

from datetime import datetime
from pathlib import Path

from google import genai
from google.genai import types

from korsche_sync import DEFAULT_GEMINI_PROMPT_MODEL, DEFAULT_GEMINI_IMAGE_MODEL
from scratch import get_random_reference_image
from utils import get_random_reference_image


def generate_new_profession():
    """
    Generate a new profession that doesn't exist in PROMPT_DATA.
    
    Returns:
        str: A new profession name.
    
    Raises:
        ValueError: If GEMINI_API_KEY environment variable is not set.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    
    client = genai.Client(api_key=api_key)
    
    # Get existing professions from refs directory filenames
    ref_files = [f.stem.replace("_", " ") for f in REFS_DIR.iterdir() if f.is_file()]
    existing_professions = ", ".join(ref_files)
    prompt = (
        f"Generate a single profession name that is NOT in this list: {existing_professions}. "
        "Respond with only the profession name in lowercase, without any additional text, "
        "formatting, or punctuation."
    )
    
    print("Generating new profession...")
    response = client.models.generate_content(
        model=DEFAULT_GEMINI_PROMPT_MODEL,
        contents=prompt
    )
    
    profession = response.text.strip().lower()
    print(f"Generated profession: {profession}")
    return profession


def generate_outfit_description(profession):
    """
    Generate a standard outfit description for a given profession.
    
    Args:
        profession (str): The profession to generate an outfit for.
    
    Returns:
        str: A single sentence describing the outfit.
    
    Raises:
        ValueError: If GEMINI_API_KEY environment variable is not set.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    
    client = genai.Client(api_key=api_key)
    
    prompt = (
        f"Describe the standard outfit for a {profession} in one paragraph. "
        "List only the pieces of clothing, without any additional text or formatting."
    )
    
    print(f"Generating outfit description for {profession}...")
    response = client.models.generate_content(
        model=DEFAULT_GEMINI_PROMPT_MODEL,
        contents=prompt
    )
    
    outfit = response.text.strip()
    print(f"Generated outfit: {outfit}")
    return outfit


def generate_character_sheet_image(profession, outfit_description, reference_image_path):
    """
    Generate a character sheet image using Gemini AI.
    
    Args:
        profession (str): The profession for the character.
        outfit_description (str): Description of the outfit.
        reference_image_path (Path): Path to the reference image file.
    
    Returns:
        bytes: The generated image data.
    
    Raises:
        ValueError: If GEMINI_API_KEY environment variable is not set or image generation fails.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    
    client = genai.Client(api_key=api_key)
    
    # Read the reference image
    print(f"Reading reference image from: {reference_image_path}")
    with open(reference_image_path, "rb") as f:
        reference_image_data = f.read()
    
    # Create the prompt
    prompt = (
        f"Create a character sheet image of Kirsche as a {profession}. "
        f"The character is wearing: {outfit_description}. "
        "Use the reference image for style and character design cues. "
        "Keep the fox character design consistent with the reference image, and only adapt the outfit and profession accordingly. "
        "Keep the style consistent with the reference image. "
        "Stay PG and family-friendly. Create a full character sheet with front view."
    )
    
    print(f"Generating character sheet image for {profession}...")
    response = client.models.generate_content(
        model=DEFAULT_GEMINI_IMAGE_MODEL,
        contents=[
            types.Part.from_bytes(
                data=reference_image_data,
                mime_type=f"image/{reference_image_path.suffix[1:].lower()}"
            ),
            prompt
        ]
    )
    
    # Get the generated image from response
    try:
        generated_image = response.candidates[0].content.parts[0].inline_data.data
        print("Image generated successfully")
        return generated_image
    except (IndexError, AttributeError) as e:
        print(f"Error parsing response: {response}")
        raise ValueError("Failed to generate image") from e


def save_character_sheet(image_data, profession):
    """
    Save the generated character sheet image to the refs directory.
    
    Args:
        image_data (bytes): The image data to save.
        profession (str): The profession name to use in the filename.
    
    Returns:
        Path: Path to the saved image file.
    """
    # Create refs directory if it doesn't exist
    REFS_DIR.mkdir(exist_ok=True)
    
    # Generate filename with timestamp and unique ID
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    safe_profession = profession.replace(" ", "_")
    filename = f"{safe_profession}.png"
    
    output_path = REFS_DIR / filename
    
    print(f"Saving character sheet to: {output_path}")
    with open(output_path, "wb") as f:
        f.write(image_data)
    
    print(f"Character sheet saved successfully")
    return output_path


def main():
    """Main function to generate a new character sheet."""
    try:
        # Step 1: Generate a new profession
        profession = generate_new_profession()
        
        # Step 2: Generate outfit description
        outfit_description = generate_outfit_description(profession)
        
        # Step 3: Get a random reference image
        print("Selecting random reference image...")
        reference_image_path = get_random_reference_image()
        print(f"Using reference image: {reference_image_path}")
        
        # Step 4: Generate character sheet image
        image_data = generate_character_sheet_image(
            profession, 
            outfit_description, 
            reference_image_path
        )
        
        # Step 5: Save the image
        output_path = save_character_sheet(image_data, profession)
        
        print("\n" + "=" * 60)
        print("Character sheet generation complete!")
        print(f"Profession: {profession}")
        print(f"Outfit: {outfit_description}")
        print(f"Saved to: {output_path}")
        print("=" * 60)
        
    except ValueError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
