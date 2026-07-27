"""
Base checker class for image analysis using AI providers (xAI, Gemini).

This module provides a base Checker class that can be overloaded to work with
different AI providers for simple yes/no image analysis tasks.
"""
import base64
import os
import sys

from abc import ABC, abstractmethod
from pathlib import Path
from time import sleep

import xai_sdk
from google import genai
from google.genai import types
from xai_sdk.chat import user

from korsche_sync import DEFAULT_GEMINI_PROMPT_MODEL
from scratch_xai import GROK_TEXT_MODEL


class Checker(ABC):
    """
    Base class for checking image properties using AI providers.
    
    This class should be subclassed to implement specific AI provider logic
    (e.g., xAI, Gemini). Subclasses must implement check_for_ears and 
    check_for_oddities methods.
    """
    
    def __init__(self, api_key):
        """
        Initialize the Checker with an API key.
        
        Args:
            api_key (str): API key for the AI provider.
        """
        self.api_key = api_key
    
    def has_ears(self, image_path):
        """
        Check if the subject in the image has visible ears.
        
        Args:
            image_path (Path or str): Path to the image file to check.
        
        Returns:
            bool: True if ears are visible, False otherwise.
        """
        image_path = Path(image_path)
        prompt = ("Fox-girls only have ears atop their head. Look carefully at the image."
                  " Does the subject in this image have visible human ears on the side of their head?"
                  " Answer with only 'yes' or 'no'.")
        response = self.check_for_ears(image_path, prompt)
        return self._parse_yes_no_response(response)
    
    def looks_odd(self, image_path):
        """
        Check if there are any odd or unusual elements in the image.
        
        Args:
            image_path (Path or str): Path to the image file to check.
        
        Returns:
            bool: True if something looks odd, False otherwise.
        """
        image_path = Path(image_path)
        prompt = ("Does this image contain any odd, unusual, or out-of-place elements? "
                  "This includes anatomical errors, distortions, or artifacts. "
                  "Answer with only 'yes' or 'no'.")
        response = self.check_for_oddities(image_path, prompt)
        return self._parse_yes_no_response(response)
    
    @abstractmethod
    def check_for_ears(self, image_path, prompt):
        """
        Send image and prompt to AI provider to check for ears.
        
        This method must be implemented by subclasses to handle the specific
        API call for the chosen AI provider.
        
        Args:
            image_path (Path): Path to the image file.
            prompt (str): Prompt asking about ears.
        
        Returns:
            str: Response from the AI provider.
        """
        pass
    
    @abstractmethod
    def check_for_oddities(self, image_path, prompt):
        """
        Send image and prompt to AI provider to check for oddities.
        
        This method must be implemented by subclasses to handle the specific
        API call for the chosen AI provider.
        
        Args:
            image_path (Path): Path to the image file.
            prompt (str): Prompt asking about oddities.
        
        Returns:
            str: Response from the AI provider.
        """
        pass
    
    def _parse_yes_no_response(self, response):
        """
        Parse a yes/no response from the AI provider.
        
        Args:
            response (str): Response text from the AI provider.
        
        Returns:
            bool: True if response contains 'yes', False otherwise.
        """
        response_lower = response.lower().strip()
        return 'yes' in response_lower


class CheckerXAI(Checker):
    """
    xAI (Grok) implementation of the Checker class.
    
    Uses the xAI SDK to analyze images with Grok vision models.
    """
    
    def __init__(self, api_key, model=GROK_TEXT_MODEL):
        """
        Initialize the xAI Checker.
        
        Args:
            api_key (str): xAI API key.
            model (str): Grok model to use for vision analysis.
        """
        super().__init__(api_key)
        self.model = model
        self.client = xai_sdk.Client(api_key=api_key)
    
    def check_for_ears(self, image_path, prompt):
        """
        Send image and prompt to xAI to check for ears.
        
        Args:
            image_path (Path): Path to the image file.
            prompt (str): Prompt asking about ears.
        
        Returns:
            str: Response from xAI.
        """
        return self._analyze_image(image_path, prompt)
    
    def check_for_oddities(self, image_path, prompt):
        """
        Send image and prompt to xAI to check for oddities.
        
        Args:
            image_path (Path): Path to the image file.
            prompt (str): Prompt asking about oddities.
        
        Returns:
            str: Response from xAI.
        """
        return self._analyze_image(image_path, prompt)
    
    def _analyze_image(self, image_path, prompt):
        """
        Analyze an image with xAI Grok vision model.
        
        Args:
            image_path (Path): Path to the image file.
            prompt (str): Analysis prompt.
        
        Returns:
            str: Response text from xAI.
        """
        # Load image and encode as base64
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        # Determine image extension
        ext = image_path.suffix.lower().lstrip(".")
        
        # Create chat with vision
        chat = self.client.chat.create(self.model)
        chat.append(user(prompt, image_url=f"data:image/{ext};base64,{image_data}"))
        
        response = chat.sample()
        return response.content


class CheckerGemini(Checker):
    """
    Google Gemini implementation of the Checker class.
    
    Uses the Google Gemini API to analyze images with vision models.
    """
    
    def __init__(self, api_key, model=DEFAULT_GEMINI_PROMPT_MODEL):
        """
        Initialize the Gemini Checker.
        
        Args:
            api_key (str): Google Gemini API key.
            model (str): Gemini model to use for vision analysis.
        """
        super().__init__(api_key)
        self.model = model
        self.client = genai.Client(api_key=api_key)
    
    def check_for_ears(self, image_path, prompt):
        """
        Send image and prompt to Gemini to check for ears.
        
        Args:
            image_path (Path): Path to the image file.
            prompt (str): Prompt asking about ears.
        
        Returns:
            str: Response from Gemini.
        """
        return self._analyze_image(image_path, prompt)
    
    def check_for_oddities(self, image_path, prompt):
        """
        Send image and prompt to Gemini to check for oddities.
        
        Args:
            image_path (Path): Path to the image file.
            prompt (str): Prompt asking about oddities.
        
        Returns:
            str: Response from Gemini.
        """
        return self._analyze_image(image_path, prompt)
    
    def _analyze_image(self, image_path, prompt):
        """
        Analyze an image with Google Gemini vision model.
        
        Args:
            image_path (Path): Path to the image file.
            prompt (str): Analysis prompt.
        
        Returns:
            str: Response text from Gemini.
        """
        # Load the image
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # Determine MIME type based on extension
        ext = image_path.suffix.lower().lstrip(".")
        mime_type = f"image/{ext}" if ext != "jpg" else "image/jpeg"
        
        # Send to Gemini
        response = self.client.models.generate_content(
            model=self.model,
            contents=[
                prompt,
                types.Part.from_bytes(data=image_data, mime_type=mime_type)
            ]
        )
        
        # Short delay to ensure Gemini has processed
        sleep(0.5)
        
        return response.text


def main():
    """
    Main function to test both CheckerXAI and CheckerGemini.
    
    Usage:
        python checker.py <image_path>
    """
    # Check if image path is provided
    if len(sys.argv) < 2:
        print("Usage: python checker.py <image_path>")
        print("Example: python checker.py images/test_image.jpg")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    # Verify image exists
    if not Path(image_path).exists():
        print(f"Error: Image file not found: {image_path}")
        sys.exit(1)
    
    print("=" * 60)
    print(f"Checking image: {image_path}")
    print("=" * 60)
    print()
    
    # Get API keys from environment variables
    xai_api_key = None #os.getenv("XAI_API_KEY")
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    
    # Check xAI
    if xai_api_key:
        print("Checking with xAI (Grok)...")
        print("-" * 60)
        try:
            checker_xai = CheckerXAI(api_key=xai_api_key)
            
            print("  Checking for ears...", end=" ")
            has_ears = checker_xai.has_ears(image_path)
            print(f"{'✓ YES' if has_ears else '✗ NO'}")
            
            print("  Checking for oddities...", end=" ")
            looks_odd = checker_xai.looks_odd(image_path)
            print(f"{'✓ YES' if looks_odd else '✗ NO'}")
            
            print()
        except Exception as e:
            print(f"  Error with xAI: {e}")
            print()
    else:
        print("Skipping xAI check (XAI_API_KEY not set)")
        print()
    
    # Check Gemini
    if gemini_api_key:
        print("Checking with Google Gemini...")
        print("-" * 60)
        try:
            checker_gemini = CheckerGemini(api_key=gemini_api_key)
            
            print("  Checking for ears...", end=" ")
            has_ears = checker_gemini.has_ears(image_path)
            print(f"{'✓ YES' if has_ears else '✗ NO'}")
            
            print("  Checking for oddities...", end=" ")
            looks_odd = checker_gemini.looks_odd(image_path)
            print(f"{'✓ YES' if looks_odd else '✗ NO'}")
            
            print()
        except Exception as e:
            print(f"  Error with Gemini: {e}")
            print()
    else:
        print("Skipping Gemini check (GEMINI_API_KEY not set)")
        print()
    
    # Warning if no API keys
    if not xai_api_key and not gemini_api_key:
        print("Warning: No API keys found!")
        print("Please set XAI_API_KEY and/or GEMINI_API_KEY in your .env file")
        print()
    
    print("=" * 60)
    print("Check complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

