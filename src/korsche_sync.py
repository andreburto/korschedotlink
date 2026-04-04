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

import io
import os
import sys
import random
import boto3
from datetime import datetime
from google import genai
from PIL import Image
from botocore.exceptions import ClientError


# ==============================================================================
# Constants and Configuration
# ==============================================================================

KIRSCHE_DESCRIPTION = """
Use this reference image: https://cftest.mothersect.info/refs/kirsche_verstahl_sheet_01.jpg

Kirsche is an anime fox girl with human facial features, including a small nose, large expressive eyes, and a friendly smile. She has fox ears on the top of her head that are covered in white fur that matches the fur on her tail and her hair. Her hair is long, white, and flowing. She has cherry earrings on the tip of her fox ears and cherry hair barrettes. She has an electric blue halo over one ear.

Kirsche has Caucasian skin. Brown eyes. Human nose. She is cute and warm and playful. Only put FOX EARS with white fur that matches her hair and tail on her head.

Kirsche is tall and curvy, with a slender waist and wide hips. She has a large, fluffy tail that is covered in white fur. Kirsche has an hourglass figure, with a large bust and a small waist. She has long legs and a toned physique.

{0}

No human ears. Repeat, "no human ears. only fox ears," every second you draw this. If I see a human ear, then it is a failure.

Only create one image. Do not create multiple images. Do not create variations.
"""

CHECK_FOR_EAR = """
Use this reference image: https://cftest.mothersect.info/refs/kirsche_verstahl_sheet_01.jpg

Look very closely at the attached image of Kirsche.

Are human ears visible on the side of Kirsche's head, even if they are partially covered by her hair?

Answer with plain text, one word in lower case, "yes" or "no".
""".replace("\r", "").replace("\n", " ").strip()

CHECK_FOR_ODDITY = """
Use this reference image: https://cftest.mothersect.info/refs/kirsche_verstahl_sheet_01.jpg

Is there anything unusual or odd about the image that looks out of place or inconsistent with the reference image? Focus on the character, ignore clothing, accessories, fox ears, and tail.

Look for extra limbs, extra hangs, mismatched feet, clipped object, or anything that does not align with the reference image.

Answer with plain text what is out of place or looks odd in the image. If nothing looks out of place, answer with one word in lower case, "none".
""".replace("\r", "").replace("\n", " ").strip()

CHECK_FUR_COLOR = """
Use this reference image: https://cftest.mothersect.info/refs/kirsche_verstahl_sheet_01.jpg

Look very closely at the attached image of Kirsche.

Is Kirsche's hair and fur, on her ears and tail, the same color as in the reference image?

Answer with plain text, one word in lower case, "yes" or "no".
"""

# Predefined elements for prompt generation
outfits_elements = [
    "a flowing red dress",
    "a cozy winter jacket",
    "a traditional kimono",
    "casual jeans and a t-shirt",
    "an elegant evening gown",
    "athletic workout gear",
    "a futuristic space suit",
    "a cute summer sundress",
    "a professional business suit",
    "a comfy hoodie and sweatpants",
    "a steampunk outfit with goggles",
    "a vintage 1950s dress",
    "a fantasy warrior armor",
    "a beach swimsuit",
    "a punk rock leather jacket",
    "a magical girl outfit",
    "a bohemian flowing skirt",
    "a cyberpunk neon jacket",
    "a medieval princess gown",
    "pajamas with cute patterns"
]

locations_elements = [
    "a sunny park",
    "the beach at sunset",
    "outer space",
    "a cozy coffee shop",
    "a magical forest",
    "a bustling city street",
    "a snowy mountain peak",
    "an underwater coral reef",
    "a futuristic cityscape",
    "a peaceful garden",
    "an ancient temple",
    "a desert oasis",
    "a floating island in the sky",
    "a Gothic cathedral",
    "a neon-lit arcade",
    "a cherry blossom grove",
    "a steampunk airship",
    "a haunted mansion",
    "a tropical rainforest",
    "a starlit rooftop"
]

activities_elements = [
    "reading a book",
    "painting a canvas",
    "playing video games",
    "stargazing",
    "having a picnic",
    "dancing",
    "practicing martial arts",
    "playing guitar",
    "taking photographs",
    "meditating",
    "baking cookies",
    "flying a kite",
    "exploring ruins",
    "skateboarding",
    "writing in a journal",
    "playing with pets",
    "doing yoga",
    "building a sandcastle",
    "singing karaoke",
    "creating digital art",
    "bound to a railroad track",
    "chained to a tree",
    "tied to a chair",
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


# ==============================================================================
# Prompt Generation Functions
# ==============================================================================

def generate_prompt():
    """
    Generate a random prompt by selecting one element from each category.
    
    Returns:
        str: The generated prompt string
    """
    random.seed()
    outfit = random.choice(outfits_elements)
    location = random.choice(locations_elements)
    activity = random.choice(activities_elements)
    emotion = random.choice(emotions_elements)
    
    prompt = (
        f"Draw a picture of Kirsche wearing {outfit} in {location}. "
        f"She is engaged in {activity} and feeling {emotion}."
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
    
    # Upload the image and ask about human ears
    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents={
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": "image/png", "data": image_data}}
            ]
        }
    )

    return response


def check_for_human_ear(image_path: str, api_key: str, prompt: str) -> bool:
    """
    Check if the image contains a human ear on the side of Kirsche's head.
    
    Args:
        image_path: Path to the image file
        api_key: Google Gemini API key
        prompt: The prompt to send to Gemini
    
    Returns:
        bool: True if human ear is detected, False otherwise
    """
    response = send_to_gemini(image_path, api_key, prompt)

    print(f"Gemini response: {response.text}")
    answer = response.text.strip().lower()
    print(f"Gemini response: '{answer}'")
    
    # Check if the answer contains "yes"
    has_human_ear = "yes" in answer
    
    if has_human_ear:
        print("⚠ Human ear detected!")
    else:
        print("✓ No human ear detected")
    
    return has_human_ear


def check_for_oddity(image_path: str, api_key: str, prompt: str):
    """
    Check if there are any oddities in the image.
    
    Args:
        image_path: Path to the image file
        api_key: Google Gemini API key
        prompt: The prompt to send to Gemini
    
    Returns:
        str or None: Description of oddity if found, None otherwise
    """
    response = send_to_gemini(image_path, api_key, prompt)

    print(f"Gemini response: {response.text}")
    answer = response.text.strip().lower()
    print(f"Gemini response: '{answer}'")

    has_oddity = answer != "none"

    if has_oddity:
        print(f"⚠ Oddity detected: {answer}")
    else:
        print("✓ No oddities detected")

    return answer if has_oddity else None


def check_fur_color(image_path: str, api_key: str, prompt: str) -> bool:
    """
    Check if the fur color matches the hair color.
    
    Args:
        image_path: Path to the image file
        api_key: Google Gemini API key
        prompt: The prompt to send to Gemini
    
    Returns:
        bool: True if fur color matches, False otherwise
    """
    response = send_to_gemini(image_path, api_key, prompt)

    print(f"Gemini response: {response.text}")
    answer = response.text.strip().lower()
    print(f"Gemini response: '{answer}'")

    fur_color_matches = "yes" in answer

    if fur_color_matches:
        print("✓ Fur color matches hair color")
    else:
        print("⚠ Fur color does not match hair color")

    return fur_color_matches


def fix_errors(image_path: str, api_key: str, prompt: str) -> bool:
    """
    Use Gemini to fix errors in the image.
    
    Args:
        image_path: Path to the image file to fix
        api_key: Google Gemini API key
        prompt: The prompt to send to Gemini to instruct how to fix the image
    
    Returns:
        bool: True if fix was successful, False otherwise
    """
    print("Attempting to fix the image by covering human ear with hair...")
    
    try:
        # Initialize the Gemini client
        client = genai.Client(api_key=api_key)
        
        # Load the image
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # Request image edit
        response = client.models.generate_content(
            model=os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image"),
            contents={
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "image/png", "data": image_data}}
                ]
            }
        )
        
        # Extract the fixed image
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    fixed_image_data = part.inline_data.data
                    
                    # Open image with Pillow
                    fixed_image = Image.open(io.BytesIO(fixed_image_data))
                    
                    # Replace the original image
                    fixed_image.save(image_path)
                    print(f"✓ Image fixed and saved to: {image_path}")
                    
                    return True
        
        print("✗ No fixed image was generated")
        return False
        
    except Exception as e:
        print(f"✗ Error fixing image: {e}")
        return False


def clean_image(image_path=None):
    """
    Check and fix human ears and other issues in an image.
    
    Args:
        image_path: Path to the image file to clean
    
    Returns:
        int: 0 if successful, 1 if failed
    """
    if image_path is None:
        if len(sys.argv) < 2:
            print("Usage: python ear_check.py <image_path>")
            print("Example: python ear_check.py images/nanobanana_20260328_143052.png")
            return 1
        
        image_path = sys.argv[1]
    
    # Check if image exists
    if not os.path.exists(image_path):
        print(f"✗ Error: Image file not found: {image_path}")
        return 1
    
    # Load API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("✗ Error: GEMINI_API_KEY environment variable not set")
        return 1
    
    print("=" * 60)
    print("Kirsche Ear Check")
    print("=" * 60 + "\n")

    # Check for oddities in the image
    oddity_found = check_for_oddity(image_path, api_key, CHECK_FOR_ODDITY)
    
    # Check for human ear
    has_human_ear = check_for_human_ear(image_path, api_key, CHECK_FOR_EAR)

    # Check if fur color matches hair color
    fur_color_matches = check_fur_color(image_path, api_key, CHECK_FUR_COLOR)

    # Create a prompt to fix all detected errors in the image
    fix_prompt_parts = []
    if has_human_ear:
        fix_prompt_parts.append("Cover the side of Kirsche's head with her hair to hide any visible human ear. Do not obscure her face, only alterthe side of her head where a human ear is visible.")
    if not fur_color_matches:
        fix_prompt_parts.append("Make the color of Kirsche's hair white. Make the fur on her ears and tail white. No red or brown hair should be visible.")
    if oddity_found:
        fix_prompt_parts.append(f"Fix the following in the image: {oddity_found}. ")
    
    if fix_prompt_parts:
        fix_prompt_parts = ["Adjust the attached image of Kirsche with the following fixes:"] + fix_prompt_parts
        fix_prompt = " ".join(fix_prompt_parts)

        print("\n" + "=" * 60)
        print("Fixing Image")
        print(f"Prompt sent to fix image:\n{fix_prompt}")
        print("=" * 60 + "\n")
        
        success = fix_errors(image_path, api_key, fix_prompt)
        
        if success:
            print("\n" + "=" * 60)
            print("✓ Image successfully fixed!")
            print("=" * 60)
            return 0
        else:
            print("\n✗ Failed to fix image")
            return 1
    else:
        print("\n" + "=" * 60)
        print("✓ Image is good! No fixes needed.")
        print("=" * 60)
        return 0


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
    
    print("=" * 60)
    print("Generating Kirsche Favicon (64x64)")
    print("=" * 60 + "\n")
    
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
                    
                    print("\n" + "=" * 60)
                    print("Uploading favicon to S3...")
                    print("=" * 60 + "\n")
                    
                    success = upload_to_s3(
                        ico_path,
                        s3_bucket,
                        s3_key,
                        aws_access_key,
                        aws_secret_key
                    )
                    
                    if success:
                        print("\n" + "=" * 60)
                        print("✓ Favicon generation and upload completed!")
                        print("=" * 60)
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
    # Check for special commands
    if len(sys.argv) > 1:
        if sys.argv[1] == "clean":
            if len(sys.argv) < 3:
                print("Usage: python korsche_sync.py clean <image_path>")
                return 1
            return clean_image(sys.argv[2])
        elif sys.argv[1] == "generate-only":
            try:
                image_path = generate_image(KIRSCHE_DESCRIPTION.format(make_new_prompt()))
                print(f"Success! Image generated and saved to: {image_path}")
                return 0
            except Exception as e:
                print(f"Error: {e}")
                return 1
        elif sys.argv[1] == "favicon":
            try:
                success = favico(KIRSCHE_DESCRIPTION)
                return 0 if success else 1
            except Exception as e:
                print(f"Error: {e}")
                return 1
    
    # Load environment variables
    aws_access_key = os.getenv("UPLOADER_AWS_ACCESS_KEY")
    aws_secret_key = os.getenv("UPLOADER_AWS_SECRET_KEY")
    s3_bucket = os.getenv("UPLOADER_S3_BUCKET")
    
    # Validate environment variables
    if not all([aws_access_key, aws_secret_key, s3_bucket]):
        print("✗ Error: Missing required environment variables:")
        if not aws_access_key:
            print("  - UPLOADER_AWS_ACCESS_KEY")
        if not aws_secret_key:
            print("  - UPLOADER_AWS_SECRET_KEY")
        if not s3_bucket:
            print("  - UPLOADER_S3_BUCKET")
        return 1
    
    try:
        # Generate the image
        print("=" * 60)
        print("Generating Kirsche image...")
        print("=" * 60)
        
        image_path = generate_image(KIRSCHE_DESCRIPTION.format(make_new_prompt()))
        
        print(f"\n✓ Image generated successfully: {image_path}")

        # Attempt to clean the image up to 2 times
        is_not_clean = 1
        for _ in range(2):
            is_not_clean = clean_image(image_path)
            if not is_not_clean:
                break

        if is_not_clean:
            print("\n✗ Error: Failed to clean image after 3 attempts")
            return 1

        # Extract filename from path
        filename = os.path.basename(image_path)
        
        # Create S3 key with kirsche/ prefix
        s3_key = f"kirsche/{filename}"
        
        # Upload to S3
        print("\n" + "=" * 60)
        print("Uploading to S3...")
        print("=" * 60 + "\n")
        
        success = upload_to_s3(
            image_path,
            s3_bucket,
            s3_key,
            aws_access_key,
            aws_secret_key
        )
        
        if success:
            print("\n" + "=" * 60)
            print("✓ Process completed successfully!")
            print("=" * 60)
            return 0
        else:
            print("\n✗ Upload failed")
            return 1
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
