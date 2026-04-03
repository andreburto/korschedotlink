#!/usr/bin/env python3
"""
Ear Check Script for Kirsche Images

This script checks if a generated Kirsche image has human ears visible
and automatically fixes them by using Gemini to cover them with hair.
"""

import io
import os
import sys
from pathlib import Path
from google import genai
from PIL import Image

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


def send_to_gemini(image_path: str, api_key: str, prompt: str) -> bool:
    """
    Check if the image contains a human ear on the side of Kirsche's head.
    
    Args:
        image_path: Path to the image file
        api_key: Google Gemini API key
    
    Returns:
        bool: True if human ear is detected, False otherwise
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


def check_for_oddity(image_path: str, api_key: str, prompt: str) -> bool:
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
    Use Gemini to fix the image by covering human ears with hair.
    
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
    """Main function to check and fix human ears in an image."""
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


if __name__ == "__main__":
    sys.exit(clean_image())