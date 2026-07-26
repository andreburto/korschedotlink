"""
Dual AI Image Generation Script

This script combines Gemini and Grok image generation capabilities to produce
two images from the same prompt for comparison. It takes a key from 
PROMPT_BY_FILE_NAME, generates random parameters, expands them using both
AI text models, and generates images from each.
"""

import base64
import os
import requests
import sys
import uuid
import xai_sdk

from datetime import datetime
from pathlib import Path
from time import sleep
from xai_sdk.chat import user

from google import genai
from google.genai import types

from korsche_sync import enhance_prompt_with_gemini
from prompt_maker import PROMPT_DATA, random_sample
from utils import REFS_DIR, PROMPT_BY_FILE_NAME, get_random_reference_image

# Model configurations
GROK_TEXT_MODEL = "grok-4.5-latest"
GROK_IMAGE_MODEL = "grok-imagine-image-quality"
GEMINI_TEXT_MODEL = "gemini-2.5-flash"
GEMINI_IMAGE_MODEL = "gemini-2.5-flash-image"


def expand_prompt_grok(client, setting, pose):
    """
    Expand the prompt with additional details using Grok.
    
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


def expand_prompt_gemini(api_key, setting, pose):
    """
    Expand the prompt with additional details using Gemini.
    
    Args:
        api_key (str): The Gemini API key.
        setting (str): The setting to include in the prompt.
        pose (str): The pose to include in the prompt.
    
    Returns:
        str: The expanded prompt.
    """
    base_prompt = f"Kirsche is {setting} {pose}."
    return enhance_prompt_with_gemini(base_prompt, GEMINI_TEXT_MODEL, api_key)


def generate_image_grok(client, reference_image_path, description):
    """
    Generate an image of Kirsche using Grok (XAI).
    
    Args:
        client (xai_sdk.Client): The initialized XAI client.
        reference_image_path (Path): Path to the reference image file.
        description (str): Description of Kirsche to guide image generation.
    
    Returns:
        str: Path to the generated image file.
    """
    print(f"[Grok] Reading reference image from: {reference_image_path}")
    
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
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{timestamp}_grok.jpg"
    output_path = images_dir / filename
    
    # Save the generated image
    with open(output_path, "wb") as f:
        f.write(requests.get(response.url).content)

    return str(output_path)


def generate_image_gemini(api_key, reference_image_path, description):
    """
    Generate an image of Kirsche using Gemini.
    
    Args:
        api_key (str): The Gemini API key.
        reference_image_path (Path): Path to the reference image file.
        description (str): Description of Kirsche to guide image generation.
    
    Returns:
        str: Path to the generated image file.
    """
    print(f"[Gemini] Reading reference image from: {reference_image_path}")
    
    # Initialize the client
    client = genai.Client(api_key=api_key)
    
    # Read the reference image
    with open(reference_image_path, "rb") as f:
        reference_image_data = f.read()
    
    # Create the prompt
    prompt = (f"Create an image of Kirsche based on this: \"{description}\"."
              " Use the reference image for style and character design cues for Kirsche."
              " Keep the style to a 2D cartoon like One Piece, Bleach, or Sailor Moon."
              " Stay PG and family-friendly. Kirsche is an adult woman.")
    
    # Generate the image
    response = client.models.generate_content(
        model=GEMINI_IMAGE_MODEL,
        contents=[
            types.Part.from_bytes(
                data=reference_image_data,
                mime_type=f"image/{str(reference_image_path).split('.')[-1].lower()}"
            ),
            prompt
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
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{timestamp}_gemini.png"
    output_path = images_dir / filename
    
    # Save the generated image
    with open(output_path, "wb") as f:
        f.write(generated_image)
    
    return str(output_path)


def main():
    """
    Main function to run the dual image generation workflow.
    """
    # Check for required parameter
    if len(sys.argv) < 2:
        print("Usage: python dual_generate.py <key>")
        print(f"Available keys: {', '.join(PROMPT_BY_FILE_NAME.keys())}")
        sys.exit(1)
    
    key = sys.argv[1]
    
    # Validate the key
    if key not in PROMPT_BY_FILE_NAME:
        print(f"Error: '{key}' is not a valid key.")
        print(f"Available keys: {', '.join(PROMPT_BY_FILE_NAME.keys())}")
        sys.exit(1)
    
    try:
        # Get the category from the key
        category = PROMPT_BY_FILE_NAME[key]
        print(f"Using category: {category} (from key: {key})")
        
        # Find the reference image that matches the key
        reference_image = None
        for f in REFS_DIR.iterdir():
            if f.is_file() and f.stem.lower() == key.lower():
                reference_image = f
                break
        
        if not reference_image:
            print(f"Warning: No reference image found for key '{key}', using random image")
            reference_image = get_random_reference_image()
        
        print(f"Selected reference image: {reference_image}")
        
        # Get random parameters from the category
        category_data = PROMPT_DATA[category]
        setting = random_sample(category_data["setting"])
        pose = random_sample(category_data["pose"])
        print(f"Using setting: {setting}")
        print(f"Using pose: {pose}")
        
        # Initialize API clients
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        xai_api_key = os.getenv("XAI_API_KEY")
        
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        if not xai_api_key:
            raise ValueError("XAI_API_KEY environment variable not set")
        
        xai_client = xai_sdk.Client(api_key=xai_api_key)
        
        # Expand prompts using both AI text models
        print("\n=== Expanding prompt with Grok ===")
        grok_prompt = expand_prompt_grok(xai_client, setting, pose)
        print(f"Grok expanded prompt: {grok_prompt}")
        
        print("\n=== Expanding prompt with Gemini ===")
        gemini_prompt = expand_prompt_gemini(gemini_api_key, setting, pose)
        print(f"Gemini expanded prompt: {gemini_prompt}")
        
        # Generate images using both AIs
        print("\n=== Generating image with Grok ===")
        grok_output = None
        for attempt in range(3):
            try:
                grok_output = generate_image_grok(xai_client, reference_image, grok_prompt)
                print(f"Grok image saved to: {grok_output}")
                break
            except Exception as e:
                print(f"Grok generation attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    print("Retrying...")
                    sleep(2)
        
        print("\n=== Generating image with Gemini ===")
        gemini_output = None
        for attempt in range(3):
            try:
                gemini_output = generate_image_gemini(gemini_api_key, reference_image, gemini_prompt)
                print(f"Gemini image saved to: {gemini_output}")
                break
            except Exception as e:
                print(f"Gemini generation attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    print("Retrying...")
                    sleep(2)
        
        # Summary
        print("\n=== Summary ===")
        print(f"Reference image: {reference_image}")
        print(f"Category: {category}")
        print(f"Setting: {setting}")
        print(f"Pose: {pose}")
        if grok_output:
            print(f"Grok output: {grok_output}")
        if gemini_output:
            print(f"Gemini output: {gemini_output}")
        
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
