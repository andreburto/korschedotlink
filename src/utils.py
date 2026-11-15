import boto3
import random

from botocore.exceptions import ClientError
from pathlib import Path


REFS_DIR = Path("refs")

PROMPT_BY_FILE_NAME = {
        "trad_wife": "homemaker",
        "workout": "fitness enthusiast",
        "aerobic": "fitness enthusiast",
        "snoop": "snoop",
        "casual": "snoop",
        "sexy_spy": "damsel in distress",
        "star_trek": "star trek fan",
        "army": "army",
        "dance_club": "party girl",
        "maid": "maid",
    }

# Model configurations
GROK_TEXT_MODEL = "grok-4.5-latest"
GROK_IMAGE_MODEL = "grok-imagine-image-quality"
GEMINI_TEXT_MODEL = "gemini-2.5-flash"
GEMINI_IMAGE_MODEL = "gemini-2.5-flash-image"

FRAME_STYLES = (
    "Marvel house 2000s",
    "DC comics 1980s",
    "Marvel comics 1960s",
    "DC comics 1990s",
    "American newspaper comics 1950s",
    "European adventure comics 1970s",
)

FRAME_SETTINGS = (
    "a rooftop garden overlooking a busy city at sunset",
    "a quiet seaside cafe with open windows and wooden tables",
    "a mountain observatory beneath a clear, star-filled sky",
    "a sunlit workshop filled with tools and unfinished projects",
    "a lantern-lit market square on a cool autumn evening",
    "a cozy library with tall bookshelves and a crackling fireplace",
    "a forest clearing beside a shallow, sparkling stream",
    "a bustling train station with a large clock above the platforms",
)


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


def random_sample(item_list):
    """
    Return a random sample from the given list.

    Args:
        item_list (list): A list of items to sample from.
    Returns:
        A random item from the list.
    """
    return random.choice(random.sample(item_list, len(item_list)))


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
        ext = local_file_path.split('.')[-1].lower()
        if ext == 'ico':
            content_type = 'image/x-icon'
        elif ext == 'json':
            content_type = 'application/json'
        elif ext in ['jpg', 'jpeg']:
            content_type = 'image/jpeg'
        elif ext == 'png':
            content_type = 'image/png'
        elif ext == 'gif':
            content_type = 'image/gif'
        elif ext == 'bmp':
            content_type = 'image/bmp'
        elif ext == 'webp':
            content_type = 'image/webp'
        else:
            content_type = 'application/octet-stream'
        
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
