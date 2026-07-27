import random

from pathlib import Path


REFS_DIR = Path("refs")

PROMPT_BY_FILE_NAME = {
        "trad_wife": "homemaker",
        "workout": "fitness enthusiast",
        "snoop": "snoop",
        "sexy_spy": "damsel in distress",
        "star_trek": "star trek fan",
        "army": "army",
        "dance_club": "party girl",
        "maid": "maid",
    }


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

