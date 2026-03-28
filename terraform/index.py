import boto3
import logging
import os
import sys

# Configure logger
logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))


def list_s3_files(bucket_name, prefix):
    s3 = boto3.client('s3')
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    files = []
    if 'Contents' in response:
        files = [f"/{obj['Key']}" for obj in response['Contents'] if obj['Key'] != prefix]
    return files


def lambda_handler(event, context):
    bucket_name = os.getenv("BUCKET_NAME")
    prefix = os.getenv("PREFIX")
    image_paths = list_s3_files(bucket_name, f"{prefix}/")
    logger.info(f"Found {len(image_paths)} images in bucket {bucket_name} with prefix {prefix}")
    return {"files": image_paths}
