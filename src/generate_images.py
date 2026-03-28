#!/usr/bin/env python3
"""
Google Gemini Image Generation Script
Generates images using Google's Gemini API and saves them with timestamps.
"""
import io
import os

from datetime import datetime
from google import genai
from PIL import Image

from prompt_maker import make_new_prompt

KIRSCHE_DESCRIPTION = """
Use this reference image: https://cftest.mothersect.info/refs/kirsche_verstahl_sheet_01.jpg

Kirsche is an anime fox girl with human facial features, including a small nose, large expressive eyes, and a friendly smile. She has fox ears on the top of her head that are covered in white fur that matches the fur on her tail and her hair. Her hair is long, white, and flowing. She has cherry earrings on the tip of her fox ears and cherry hair barrettes. She has an electric blue halo over one ear.

Kirsche has Caucasian skin. Brown eyes. Human nose. She is cute and warm and playful. Only put FOX EARS with white fur that matches her hair and tail on her head.

Kirsche is tall and curvy, with a slender waist and wide hips. She has a large, fluffy tail that is covered in white fur. Kirsche has an hourglass figure, with a large bust and a small waist. She has long legs and a toned physique.

{0}

No human ears. Repeat, "no human ears. only fox ears," every second you draw this. If I see a human ear, then it is a failure.

Only create one image. Do not create multiple images. Do not create variations.
"""


def generate_image(prompt: str, output_dir: str = "images"):
    """
    Generate an image using Google Gemini Nano Banana and save it with a timestamp.
    
    Args:
        prompt: The text prompt for image generation
        output_dir: Directory to save the generated image
    
    Returns:
        Path to the saved image file
    """
    # Load API key
    api_key = os.getenv("GEMINI_API_KEY")
    
    # Initialize the Gemini client
    client = genai.Client(api_key=api_key)
    
    print(f"Generating image with prompt: '{prompt}'")
    
    # Generate the image using Nano Banana model
    response = client.models.generate_content(
        model=os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image"),
        contents=prompt
    )
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Extract and save the generated image
    if response.candidates and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                image_data = part.inline_data.data
                
                # Open image with Pillow
                image = Image.open(io.BytesIO(image_data))
                
                # Create filename with timestamp
                filename = f"nanobanana_{timestamp}.png"
                filepath = os.path.join(output_dir, filename)
                
                # Save the image
                image.save(filepath)
                print(f"Image saved successfully to: {filepath}")
                
                return filepath
    
    raise Exception("No image was generated")


def main():
    """Main function to run the image generation."""
    try:
        image_path = generate_image(KIRSCHE_DESCRIPTION.format(make_new_prompt()))
        print(f"Success! Image generated and saved to: {image_path}")
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())