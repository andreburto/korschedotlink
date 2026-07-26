"""
Dual AI Image Generation Script

This script combines Gemini and Grok image generation capabilities to produce
two images from the same prompt for comparison. It takes a key from 
PROMPT_BY_FILE_NAME, generates random parameters, expands them using both
AI text models, and generates images from each.
"""

import asyncio
import base64
import logging
import os
import requests
import sys
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

# Set up logging
script_dir = Path(__file__).parent
log_filename = f"dual_{datetime.now().strftime('%Y%m%d')}.log"
log_path = script_dir / log_filename

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_path, mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def expand_prompt_grok(client, setting, pose):
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
    loop = asyncio.get_event_loop()
    chat = await loop.run_in_executor(None, client.chat.create, GROK_TEXT_MODEL)
    chat.append(user(prompt))
    result = await loop.run_in_executor(None, chat.sample)
    return result.content


async def expand_prompt_gemini(api_key, setting, pose):
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
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None, enhance_prompt_with_gemini, base_prompt, GEMINI_TEXT_MODEL, api_key
    )
    return result


async def generate_image_grok(client, reference_image_path, description):
    """
    Generate an image of Kirsche using Grok (XAI).
    
    Args:
        client (xai_sdk.Client): The initialized XAI client.
        reference_image_path (Path): Path to the reference image file.
        description (str): Description of Kirsche to guide image generation.
    
    Returns:
        str: Path to the generated image file.
    """
    logger.info(f"[Grok] Reading reference image from: {reference_image_path}")
    
    # Load image from file and encode as base64
    with open(reference_image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")
    
    # Create the prompt
    prompt = (f"Create an image of Kirsche based on this: \"{description}\"."
              " Use the reference image for style and character design cues for Kirsche."
              " Keep the style to a 2D cartoon like One Piece, Bleach, or Naruto."
              " Stay PG and family-friendly. Kirsche is an adult woman.")
    
    ext = reference_image_path.suffix.lower().lstrip(".")
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: client.image.sample(
            prompt=prompt,
            model=GROK_IMAGE_MODEL,
            image_url=f"data:image/{ext};base64,{image_data}",
        )
    )

    # Create images directory if it doesn't exist
    images_dir = Path("images")
    images_dir.mkdir(exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{timestamp}_grok.jpg"
    output_path = images_dir / filename
    
    # Save the generated image
    image_content = await loop.run_in_executor(
        None, lambda: requests.get(response.url).content
    )
    with open(output_path, "wb") as f:
        f.write(image_content)

    return str(output_path)


async def generate_image_gemini(api_key, reference_image_path, description):
    """
    Generate an image of Kirsche using Gemini.
    
    Args:
        api_key (str): The Gemini API key.
        reference_image_path (Path): Path to the reference image file.
        description (str): Description of Kirsche to guide image generation.
    
    Returns:
        str: Path to the generated image file.
    """
    logger.info(f"[Gemini] Reading reference image from: {reference_image_path}")
    
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
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: client.models.generate_content(
            model=GEMINI_IMAGE_MODEL,
            contents=[
                types.Part.from_bytes(
                    data=reference_image_data,
                    mime_type=f"image/{str(reference_image_path).split('.')[-1].lower()}"
                ),
                prompt
            ]
        )
    )
    
    # Get the generated image from response
    generated_image = None
    try:
        generated_image = response.candidates[0].content.parts[0].inline_data.data
    except (IndexError, AttributeError) as e:
        logger.error(f"Error parsing response: {response}")
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


async def main():
    """
    Main function to run the dual image generation workflow.
    """
    # Check for required parameter
    if len(sys.argv) < 2:
        logger.error("Usage: python dual_generate.py <key>")
        logger.error(f"Available keys: {', '.join(PROMPT_BY_FILE_NAME.keys())}")
        sys.exit(1)
    
    key = sys.argv[1]
    
    # Validate the key
    if key not in PROMPT_BY_FILE_NAME:
        logger.error(f"Error: '{key}' is not a valid key.")
        logger.error(f"Available keys: {', '.join(PROMPT_BY_FILE_NAME.keys())}")
        sys.exit(1)
    
    try:
        # Get the category from the key
        category = PROMPT_BY_FILE_NAME[key]
        logger.info(f"Using category: {category} (from key: {key})")
        
        # Find the reference image that matches the key
        reference_image = None
        for f in REFS_DIR.iterdir():
            if f.is_file() and f.stem.lower() == key.lower():
                reference_image = f
                break
        
        if not reference_image:
            logger.warning(f"No reference image found for key '{key}', using random image")
            reference_image = get_random_reference_image()
        
        logger.info(f"Selected reference image: {reference_image}")
        
        # Get random parameters from the category
        category_data = PROMPT_DATA[category]
        setting = random_sample(category_data["setting"])
        pose = random_sample(category_data["pose"])
        logger.info(f"Using setting: {setting}")
        logger.info(f"Using pose: {pose}")
        
        # Initialize API clients
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        xai_api_key = os.getenv("XAI_API_KEY")
        
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        if not xai_api_key:
            raise ValueError("XAI_API_KEY environment variable not set")
        
        xai_client = xai_sdk.Client(api_key=xai_api_key)
        
        # Expand prompts using both AI text models in parallel
        logger.info("=== Expanding prompts with both Grok and Gemini ===")
        grok_prompt_task = expand_prompt_grok(xai_client, setting, pose)
        gemini_prompt_task = expand_prompt_gemini(gemini_api_key, setting, pose)
        
        grok_prompt, gemini_prompt = await asyncio.gather(grok_prompt_task, gemini_prompt_task)
        
        logger.info(f"Grok expanded prompt: {grok_prompt}")
        logger.info(f"Gemini expanded prompt: {gemini_prompt}")
        
        # Generate images using both AIs in parallel
        logger.info("=== Generating images with both Grok and Gemini ===")
        
        async def generate_with_retry(generate_func, *args, ai_name="AI", max_attempts=3):
            """Helper function to retry image generation."""
            for attempt in range(max_attempts):
                try:
                    result = await generate_func(*args)
                    logger.info(f"{ai_name} image saved to: {result}")
                    return result
                except Exception as e:
                    logger.error(f"{ai_name} generation attempt {attempt + 1} failed: {e}")
                    if attempt < max_attempts - 1:
                        logger.info(f"Retrying {ai_name}...")
                        await asyncio.sleep(2)
            return None
        
        grok_task = generate_with_retry(
            generate_image_grok, xai_client, reference_image, grok_prompt, ai_name="Grok"
        )
        gemini_task = generate_with_retry(
            generate_image_gemini, gemini_api_key, reference_image, gemini_prompt, ai_name="Gemini"
        )
        
        grok_output, gemini_output = await asyncio.gather(grok_task, gemini_task)
        
        # Summary
        logger.info("=== Summary ===")
        logger.info(f"Reference image: {reference_image}")
        logger.info(f"Category: {category}")
        logger.info(f"Setting: {setting}")
        logger.info(f"Pose: {pose}")
        if grok_output:
            logger.info(f"Grok output: {grok_output}")
        if gemini_output:
            logger.info(f"Gemini output: {gemini_output}")
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
