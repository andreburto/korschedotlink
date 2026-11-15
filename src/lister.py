"""List S3 objects under a prefix and write them to a local index.json file."""

import json
import os
import sys

import boto3


def list_keys(bucket_name, prefix, aws_access_key, aws_secret_key):
    """
    List all object keys in an S3 bucket matching a prefix.

    Args:
        bucket_name (str): Name of the S3 bucket.
        prefix (str): Prefix to filter objects by.
        aws_access_key (str): AWS access key ID.
        aws_secret_key (str): AWS secret access key.

    Returns:
        list: Sorted list of S3 object keys matching the prefix.
    """
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
    )

    keys = []
    paginator = s3_client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
        for obj in page.get("Contents", []):
            keys.append(obj["Key"])

    return sorted(keys)


def main():
    """Parse CLI args, list matching S3 objects, and write them to index.json."""
    if len(sys.argv) != 4:
        print("Usage: python src/lister.py <bucket> <key> <prefix>")
        sys.exit(1)

    bucket, key, prefix = sys.argv[1], sys.argv[2], sys.argv[3]

    aws_access_key = os.getenv("UPLOADER_AWS_ACCESS_KEY")
    aws_secret_key = os.getenv("UPLOADER_AWS_SECRET_KEY")
    if not all([aws_access_key, aws_secret_key]):
        raise ValueError("One or more required environment variables are not set")

    keys = list_keys(bucket, f"{key}/{prefix}", aws_access_key, aws_secret_key)

    save_file = f"{os.path.curdir}/index.json"
    with open(save_file, "w") as f:
        json.dump(keys, f, indent=2)

    print(f"Wrote {len(keys)} keys with prefix '{prefix}' from bucket '{bucket}' to {save_file}")


if __name__ == "__main__":
    main()
