#!/usr/bin/env python3
"""
Korsche Image Generation and S3 Sync Script

This script generates a new Kirsche image using Gemini and automatically
uploads it to the configured S3 bucket.

Consolidated from:
- generate_images.py
- image_cleanup.py
- prompt_maker.py
- list_models.py
"""

import boto3
import io
import os
import random
import sys

from botocore.exceptions import ClientError
from datetime import datetime
from google.genai import types
from google import genai
from PIL import Image
from time import sleep

# ==============================================================================
# Constants and Configuration
# ==============================================================================
KIRSCHE_DESCRIPTION = """
Use this reference image: https://cftest.mothersect.info/refs/kirsche_verstahl_sheet_01.jpg

Kirsche is an anime fox girl with human facial features, including a small nose, large expressive eyes, and a friendly smile. She has fox ears on the top of her head that are covered in white fur that matches the fur on her tail and her hair. Her hair is long, white, and flowing. She has cherry earrings on the tip of her fox ears and cherry hair barrettes. She has an electric blue halo over one ear.

Kirsche has Caucasian skin. Brown eyes. Human nose. She is cute and warm and playful. Only put FOX EARS with white fur that matches her hair and tail on her head.

Kirsche is tall and curvy, with a slender waist and wide hips. She has a large, fluffy tail that is covered in white fur. Kirsche has an hourglass figure, with a large bust and a small waist. She has long legs and a toned physique. She has two arms, two hands, two legs, two feet, and one tail. Her hands have five fingers and her feet have five toes. 

{0}

No human ears. Repeat, "no human ears. only fox ears," every second you draw this. Cover any human ears with her hair. Do not remove her fox ears or her eyes.

Only create one image. Do not create multiple images. Do not create variations.
"""

CHECK_FOR_EAR = """
Carefully examine the attached image of Kirsche. Focus on the sides of her head where human ears are located.

Is a human ear visible on the side of Kirsche's head? Which side is it?

If you see a human ear, only tell me which side it is with a single word, "left" or "right". If you don't see a human ear, then the answer simply "none".

Use no punctuation in your answer, just the single word.
""".replace("\r", "").replace("\n", " ").strip()

CHECK_FOR_LIMBS = """
Kirsche should have only two arms and only two legs.

Do you see two arms and two legs?

If there are the right number of limbs, simply answer "no" with no punctuation.

Otherwise, describe the limb issue you see in the image, such as "extra arm on left side" or "missing leg on right side".
""".replace("\r", "").replace("\n", " ").strip()

CHECK_FUR_COLOR = """
You are a hairstylist and fur color expert. 

Look at the attached image of Kirsche and determine if her hair and fur are white or silver.

Ignore any hair accessories. This is only about the color of her hair and fur.

If the hair and fur are mostly white or silver, simply answer "yes" with no punctuation. Otherwise, describe her hair and fur.
""".replace("\r", "").replace("\n", " ").strip()

# Predefined elements for prompt generation
outfits_elements = [
    "a vintage 1950s housewife dress with an apron",
    "a floral sundress with a cardigan",
    "a modest tea-length dress with pearls",
    "a gingham check dress with white collar",
    "a polka dot dress with a full skirt",
    "a pastel blouse with a long skirt",
    "a prairie dress with lace trim",
    "a pinafore apron over a long dress",
    "a knit sweater with a pleated skirt",
    "a pearl-buttoned cardigan with a midi dress",
    "matching athletic leggings and sports bra",
    "high-waisted yoga pants with a crop top",
    "a sleek athleisure set in neutral tones",
    "compression leggings with an oversized athletic hoodie",
    "a matching workout set with mesh panels",
    "gym shorts with a fitted tank top",
    "seamless leggings with a sports bra top",
    "joggers with a zip-up athletic jacket",
    "biker shorts with an oversized tee",
    "tennis skirt with a sporty crop top"
]

locations_elements = [
    "a cozy kitchen",
    "a sunlit laundry room",
    "a charming sewing room",
    "a peaceful vegetable garden",
    "a warm nursery",
    "an elegant dining room",
    "a well-stocked pantry",
    "a welcoming front porch",
    "a rustic farmhouse kitchen",
    "a comfortable living room",
    "a tidy bedroom",
    "a vintage mudroom",
    "a blooming flower garden",
    "a quaint chicken coop",
    "a traditional country barn",
    "a lush orchard",
    "a cozy breakfast nook",
    "a sunny greenhouse",
    "a charming back porch",
    "a homey craft room"
]

activities_elements = [
    "baking bread",
    "arranging flowers",
    "knitting a sweater",
    "sewing curtains",
    "preparing a meal",
    "tending to plants",
    "doing laundry",
    "organizing shelves",
    "decorating the home",
    "making jam",
    "ironing linens",
    "reading a recipe book",
    "folding clothes",
    "setting the table",
    "watering the garden",
    "canning vegetables",
    "embroidering fabric",
    "cleaning windows",
    "arranging the pantry",
    "preparing tea",
]

emotions_elements = [
    "joyful",
    "peaceful",
    "excited",
    "contemplative",
    "confident",
    "playful",
    "serene",
    "adventurous",
    "mischievous",
    "proud",
    "inspired",
    "dreamy",
    "energetic",
    "content",
    "curious",
    "determined",
    "whimsical",
    "relaxed",
    "enthusiastic",
    "mysterious"
]

DIVIDER = "=" * 60


class FoxuException(Exception):
    """Custom exception for Foxu Factory errors."""
    pass

# ==============================================================================
# Prompt Generation Functions
# ==============================================================================
def generate_prompt():
    """
    Generate a random prompt by selecting one element from each category.
    
    Returns:
        str: The generated prompt string
    """
    random.seed(datetime.now().timestamp())
    outfit = random.choice(random.sample(outfits_elements, len(outfits_elements)))
    location = random.choice(random.sample(locations_elements, len(locations_elements)))
    activity = random.choice(random.sample(activities_elements, len(activities_elements)))
    emotion = random.choice(random.sample(emotions_elements, len(emotions_elements)))
    direction = random.choice(random.sample(["left", "right", "front", "back"], 4))
    lighting = random.choice(random.sample(["soft", "dramatic", "natural", "warm", "cool"], 5))
    
    prompt = (
        f"Draw a picture of Kirsche wearing {outfit} in {location}."
        f" She engaged in {activity} and feeling {emotion}."
        f" The scene is viewed from the {direction}."
        f" The lighting is {lighting}."
    )
    
    print(f"Generated prompt: {prompt}")
    return prompt


def enhance_prompt_with_gemini(prompt, model, api_key):
    """
    Enhance the generated prompt using Google Gemini API.
    
    Args:
        prompt (str): The original prompt to enhance
        model (str): The Gemini model to use for improving the prompt
        api_key (str): The Google API key.
    
    Returns:
        str: The enhanced prompt, or the original prompt if enhancement fails
    """    
    enhancement_instruction = (
        f"You are a creative prompt enhancer. Take the following image generation prompt "
        f"and make it more creative, detailed, and vivid while keeping it PG-rated. "
        f"Maintain the core structure and elements but add artistic details, atmosphere, "
        f"lighting, composition, and style elements. Return ONLY the enhanced prompt, "
        f"nothing else.\n\nOriginal prompt: {prompt}"
    )
    
    # Initialize the Gemini client
    client = genai.Client(api_key=api_key)
    
    # Generate content using the model
    response = client.models.generate_content(model=model, contents=enhancement_instruction)
    
    enhanced_prompt = response.text.strip()
    
    if enhanced_prompt:
        print(f"Prompt enhanced successfully using {model}")
        return enhanced_prompt
    else:
        raise ValueError("Received empty response from Gemini")


def make_new_prompt():
    """Generate, enhance, and return a new prompt."""
    # Setup Gemini model and API key
    model = os.getenv("GEMINI_PROMPT_MODEL", "gemini-2.5-flash")
    api_key = os.getenv("GEMINI_API_KEY")
    
    # Generate the base prompt
    prompt = generate_prompt()
    
    # Enhance the prompt using Gemini
    enhanced_prompt = enhance_prompt_with_gemini(prompt, model=model, api_key=api_key)
    
    # Save the enhanced prompt to file
    return enhanced_prompt


# ==============================================================================
# Image Generation Functions
# ==============================================================================
def generate_filename(base_name: str = "nanobanana", extension: str = "png") -> None:
    """Generate a filename with a timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base_name}_{timestamp}.{extension}"

def generate_image(prompt: str, save_file: str = "images", api_key: str = None) -> str:
    """
    Generate an image using Google Gemini Nano Banana and save it with a timestamp.
    
    Args:
        prompt: The text prompt for image generation
        save_file: Directory to save the generated image
    
    Returns:
        Path to the saved image file
    """
    image_generated = False

    # Initialize the Gemini client
    api_key = api_key or os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    os.makedirs(os.path.dirname(save_file), exist_ok=True)
    
    print(f"Generating image with prompt: '{prompt}'")
    
    # Generate the image using Nano Banana model
    response = client.models.generate_content(
        model=os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image"),
        contents=prompt
    )
          
    # Extract and save the generated image
    if response.candidates and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                image_data = part.inline_data.data
                
                # Open image with Pillow
                image = Image.open(io.BytesIO(image_data))
                
                # Save the image
                image.save(save_file, format="PNG")
                print(f"Image saved successfully to: {save_file}")
                image_generated = True

    if not image_generated:
        raise Exception("No image was generated")


# ==============================================================================
# Image Cleanup and Validation Functions
# ==============================================================================
def send_to_gemini(image_path: str, api_key: str, prompt: str):
    """
    Send an image to Gemini with a prompt and get a response.
    
    Args:
        image_path: Path to the image file
        api_key: Google Gemini API key
        prompt: The prompt to send with the image
    
    Returns:
        Response from Gemini
    """
    print(f"Validating image: {image_path}")
    
    # Initialize the Gemini client
    client = genai.Client(api_key=api_key)
    
    # Load the image
    with open(image_path, 'rb') as f:
        image_data = f.read()
    
    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=[
            prompt, 
            types.Part.from_bytes(data=image_data, mime_type="image/png")])
    sleep(2)  # Short delay to ensure Gemini has processed the image
    return response


def check_for_human_ear(image_path: str, api_key: str, prompt: str) -> None:
    """
    Check if the image contains a human ear on the side of Kirsche's head.
    
    Args:
        image_path: Path to the image file
        api_key: Google Gemini API key
        prompt: The prompt to send to Gemini
    
    Returns:
        None
    """
    response = send_to_gemini(image_path, api_key, prompt)

    answer = response.text.strip().lower().replace(".", "")
    print(f"Gemini response: '{answer}'")
    
    if answer in ["left", "right"]:
        raise FoxuException(f"⚠ Human ear detected on the {answer} side!")
    

def check_fur_color(image_path: str, api_key: str, prompt: str) -> None:
    """
    Check if the fur color matches the hair color.
    
    Args:
        image_path: Path to the image file
        api_key: Google Gemini API key
        prompt: The prompt to send to Gemini
    
    Returns:
        None
    """
    response = send_to_gemini(image_path, api_key, prompt)

    answer = response.text.strip().lower().replace(".", "")
    print(f"Gemini response for hair color: '{answer}'")

    if answer != "yes":
        raise FoxuException("⚠ Fur color does not match hair color")


def check_limbs(image_path: str, api_key: str, prompt: str) -> None:
    """
    Check if there are any limb issues in the image.
    
    Args:
        image_path: Path to the image file
        api_key: Google Gemini API key
        prompt: The prompt to send to Gemini
    Returns:
        None
    """
    response = send_to_gemini(image_path, api_key, prompt)

    answer = response.text.strip().lower()
    print(f"Gemini response for limb issues: '{answer}'")

    if answer != "no":
        raise FoxuException(f"⚠ Limb issue detected: {answer}")


def validate_image(image_path: str, api_key: str) -> bool:
    """
    Validate an image for various issues and return a list of fix prompts.
    
    Args:
        image_path: Path to the image file to validate
        api_key: Google Gemini API key
    
    Returns:
        bool: True if the image is valid, False otherwise
    """
    is_valid = True

    try:
        # Check for missing or extra limbs
        check_limbs(image_path, api_key, CHECK_FOR_LIMBS)
        # Check for human ear
        check_for_human_ear(image_path, api_key, CHECK_FOR_EAR)
        # Check if fur color matches hair color
        check_fur_color(image_path, api_key, CHECK_FUR_COLOR)
    except FoxuException as fe:
        print(str(fe))
        is_valid = False
    except Exception as e:
        print(f"✗ Error during validation: {e}")
        is_valid = False
        
    # Return True if no issues were detected, False otherwise
    return is_valid


# ==============================================================================
# Favicon Generation Functions
# ==============================================================================
def favico(kirsche_description: str, output_dir: str = "images"):
    """
    Generate a 64x64 favicon icon of Kirsche and upload it to S3.
    
    Args:
        kirsche_description: The Kirsche character description template
        output_dir: Directory to save the generated favicon
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Load environment variables
    api_key = os.getenv("GEMINI_API_KEY")
    aws_access_key = os.getenv("UPLOADER_AWS_ACCESS_KEY")
    aws_secret_key = os.getenv("UPLOADER_AWS_SECRET_KEY")
    s3_bucket = os.getenv("UPLOADER_S3_BUCKET")
    
    # Validate environment variables
    if not all([api_key, aws_access_key, aws_secret_key, s3_bucket]):
        print("✗ Error: Missing required environment variables")
        return False
    
    # Initialize the Gemini client
    client = genai.Client(api_key=api_key)
    
    # Create a simplified prompt for favicon (focus on face/head)
    favicon_prompt = kirsche_description.format(
        "Draw a centered portrait icon of Kirsche's face and upper body, "
        "suitable for a small 64x64 pixel favicon. Simple, clean style with "
        "good contrast and clear features. Her face should be clearly visible "
        "with a cute and warm expression."
    )
    
    print(DIVIDER)
    print("Generating Kirsche Favicon (64x64)")
    print(DIVIDER + "\n")
    
    try:
        # Generate the image using Gemini
        response = client.models.generate_content(
            model=os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image"),
            contents=favicon_prompt
        )
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Extract and process the generated image
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    image_data = part.inline_data.data
                    
                    # Open image with Pillow
                    image = Image.open(io.BytesIO(image_data))
                    
                    # Resize to 64x64
                    favicon_image = image.resize((64, 64), Image.Resampling.LANCZOS)
                    
                    # Save as ICO
                    ico_filename = "kirsche_favicon.ico"
                    ico_path = os.path.join(output_dir, ico_filename)
                    favicon_image.save(ico_path, format="ICO", sizes=[(64, 64)])
                    print(f"✓ ICO favicon saved to: {ico_path}")
                    
                    # Upload to S3
                    s3_key = f"kirsche/{ico_filename}"
                    
                    print("\n" + DIVIDER)
                    print("Uploading favicon to S3...")
                    print(DIVIDER + "\n")
                    
                    success = upload_to_s3(
                        ico_path,
                        s3_bucket,
                        s3_key,
                        aws_access_key,
                        aws_secret_key
                    )
                    
                    if success:
                        print("\n" + DIVIDER)
                        print("✓ Favicon generation and upload completed!")
                        print(DIVIDER)
                        return True
                    else:
                        print("\n✗ Upload failed")
                        return False
        
        print("✗ No favicon was generated")
        return False
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


# ==============================================================================
# S3 Upload Functions
# ==============================================================================
def upload_to_s3(local_file_path, bucket_name, s3_key, aws_access_key, aws_secret_key):
    """
    Upload a file to an S3 bucket.
    
    Args:
        local_file_path: Path to the local file to upload
        bucket_name: Name of the S3 bucket
        s3_key: S3 object key (path within the bucket)
        aws_access_key: AWS access key ID
        aws_secret_key: AWS secret access key
    
    Returns:
        bool: True if upload was successful, False otherwise
    """
    try:
        # Create S3 client with provided credentials
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key
        )
        
        # Determine content type based on file extension
        content_type = 'image/png'
        if local_file_path.endswith('.ico'):
            content_type = 'image/x-icon'
        
        # Upload the file
        print(f"Uploading {local_file_path} to s3://{bucket_name}/{s3_key}")
        s3_client.upload_file(
            local_file_path,
            bucket_name,
            s3_key,
            ExtraArgs={
                'ContentType': content_type,
                'ACL': 'public-read'
            }
        )
        
        print(f"✓ Successfully uploaded to s3://{bucket_name}/{s3_key}")
        
        # Generate and print the public URL
        public_url = f"https://{bucket_name}/{s3_key}"
        print(f"Public URL: {public_url}")
        
        return True
        
    except ClientError as e:
        print(f"✗ Error uploading to S3: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


# ==============================================================================
# Main Orchestration
# ==============================================================================
def main():
    """Main function to generate image and upload to S3."""
    # Load environment variables
    aws_access_key = os.getenv("UPLOADER_AWS_ACCESS_KEY")
    aws_secret_key = os.getenv("UPLOADER_AWS_SECRET_KEY")
    s3_bucket = os.getenv("UPLOADER_S3_BUCKET")
    gemini_api_key = os.getenv("GEMINI_API_KEY")

    # Validate environment variables
    if not all([aws_access_key, aws_secret_key, s3_bucket, gemini_api_key]):
        print("✗ Error: Missing required environment variables:")
        if not aws_access_key:
            print("  - UPLOADER_AWS_ACCESS_KEY")
        if not aws_secret_key:
            print("  - UPLOADER_AWS_SECRET_KEY")
        if not s3_bucket:
            print("  - UPLOADER_S3_BUCKET")
        if not gemini_api_key:
            print("  - GEMINI_API_KEY")
        return 1
    
    # Check for special commands
    if len(sys.argv) > 1:
        if sys.argv[1] == "validate":
            if len(sys.argv) < 3:
                print("Usage: python korsche_sync.py validate <image_path>")
                return 1
            is_valid = validate_image(sys.argv[2], gemini_api_key)
            if is_valid:
                print("Validation passed with no issues found.")
                return 0
            else:
                print("Validation failed. Issues found in the image.")
                return 1
        elif sys.argv[1] == "favicon":
            try:
                success = favico(KIRSCHE_DESCRIPTION)
                return 0 if success else 1
            except Exception as e:
                print(f"Error: {e}")
                return 1
        else:
            print(f"Unknown command: {sys.argv[1]}")
            print("Usage: python korsche_sync.py [validate <image_path> | favicon]")
            return 1
    
    try:
        # Generate the image
        print(DIVIDER)
        print("Generating Kirsche image...")
        print(DIVIDER)

        save_file = f"images/{generate_filename()}"
        print(f"Image name generated successfully: {save_file}")

        image_prompt = KIRSCHE_DESCRIPTION.format(make_new_prompt())
        print(f"Prompt generated successfully: {image_prompt}")

        # Attempt to clean the image up to 2 times
        print(DIVIDER)
        for val_count in range(2):
            generate_image(
                image_prompt,
                save_file=save_file,
                api_key=gemini_api_key)
            sleep(5)  # Short delay between validation attempts
            print(f"Validation attempt {val_count + 1}")
            is_valid = validate_image(save_file, gemini_api_key)
            if not is_valid:
                if val_count > 0:
                    print("\n✗ Error: Image still has issues after 2 validation attempts")
                    return 1
                sleep(5)  # Short delay before regenerating
                print("\nRegenerating image due to validation issues...")
                continue
            break
        print(DIVIDER)

        # Extract filename from path
        filename = os.path.basename(save_file)
        
        # Create S3 key with kirsche/ prefix
        s3_key = f"kirsche/{filename}"
        
        # Upload to S3
        print("\n" + DIVIDER)
        print("Uploading to S3...")
        print(DIVIDER + "\n")
        
        success = upload_to_s3(
            save_file,
            s3_bucket,
            s3_key,
            aws_access_key,
            aws_secret_key
        )
        
        if success:
            print("\n" + DIVIDER)
            print("✓ Process completed successfully!")
            print(DIVIDER)
            return 0
        else:
            print("\n✗ Upload failed")
            return 1
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
