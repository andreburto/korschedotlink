import os
import sys

from korsche_sync import upload_to_s3


def main():
    # Get environment variables
    api_key = os.getenv("GEMINI_API_KEY")
    aws_access_key = os.getenv("UPLOADER_AWS_ACCESS_KEY")
    aws_secret_key = os.getenv("UPLOADER_AWS_SECRET_KEY")
    s3_bucket = os.getenv("UPLOADER_S3_BUCKET")

    if not all([api_key, aws_access_key, aws_secret_key, s3_bucket]):
        raise ValueError("One or more required environment variables are not set")
    
    print(sys.argv)
    
    if len(sys.argv) != 2:
        print("Usage: python src/upload.py <file_path>")
        sys.exit(1)

    # Example usage of upload_file_to_s3
    file_path = os.path.join(
        os.path.dirname(os.path.abspath(os.path.curdir)), 
        sys.argv[1])  # Path to the file you want to upload

    if upload_to_s3(file_path, s3_bucket, sys.argv[1], aws_access_key, aws_secret_key):
        print(f"File {file_path} uploaded to S3 bucket https://{s3_bucket}/{sys.argv[1]}")
    else:
        print("File upload failed")
        sys.exit(1)


if __name__ == "__main__":
    main()