#!/usr/bin/env python3
"""
Korsche Image Generation and S3 Sync Script

This script generates a new Kirsche image using Gemini and automatically
uploads it to the configured S3 bucket.
"""

import os
import sys
import boto3
from botocore.exceptions import ClientError

from image_cleanup import clean_image
from generate_images import generate_image, KIRSCHE_DESCRIPTION
from prompt_maker import make_new_prompt


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
        
        # Upload the file
        print(f"Uploading {local_file_path} to s3://{bucket_name}/{s3_key}")
        s3_client.upload_file(
            local_file_path,
            bucket_name,
            s3_key,
            ExtraArgs={
                'ContentType': 'image/png',
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


def main():
    """Main function to generate image and upload to S3."""
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
