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
Look very closely at the attached image of Kirsche.

Zoom in on the side of Kirsche's head that is not covered by her hair or her fox ears and look very closely for any human ears. Do not look at the top of her head where the fox ears are. Only look at the side of her head that is not covered by hair or fox ears.

Is there any flesh visible on the side of Kirsche's head that is not covered by her hair ears?

Answer with plain text, one word in lower case, "yes" or "no".
""".replace("\r", "").replace("\n", " ").strip()


def check_for_human_ear(image_path: str, api_key: str) -> bool:
    """
    Check if the image contains a human ear on the side of Kirsche's head.
    
    Args:
        image_path: Path to the image file
        api_key: Google Gemini API key
    
    Returns:
        bool: True if human ear is detected, False otherwise
    """
    print(f"Checking for human ears in: {image_path}")
    
    try:
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
                    {"text": CHECK_FOR_EAR},
                    {"inline_data": {"mime_type": "image/png", "data": image_data}}
                ]
            }
        )
        
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
        
    except Exception as e:
        print(f"✗ Error checking for human ear: {e}")
        return False


def fix_human_ear(image_path: str, api_key: str) -> bool:
    """
    Use Gemini to fix the image by covering human ears with hair.
    
    Args:
        image_path: Path to the image file to fix
        api_key: Google Gemini API key
    
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
                    {"text": "Cover the side of Kirsche's head with her hair. Do not change the fox ears atop her head."},
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


def main():
    """Main function to check and fix human ears in an image."""
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
    
    # Check for human ear
    has_human_ear = check_for_human_ear(image_path, api_key)
    
    if has_human_ear:
        print("\n" + "=" * 60)
        print("Fixing Image")
        print("=" * 60 + "\n")
        
        success = fix_human_ear(image_path, api_key)
        
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
    sys.exit(main())
