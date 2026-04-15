#!/usr/bin/env python3
"""Upload raw Kaggle CSV to MinIO."""
import os
import sys

import boto3
from botocore.client import Config


def main() -> None:
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "/data/events.csv"

    s3 = boto3.client(
        "s3",
        endpoint_url=os.environ["MINIO_ENDPOINT"],
        aws_access_key_id=os.environ["MINIO_ROOT_USER"],
        aws_secret_access_key=os.environ["MINIO_ROOT_PASSWORD"],
        config=Config(signature_version="s3v4"),
    )

    bucket = os.environ["MINIO_BUCKET"]

    existing = [b["Name"] for b in s3.list_buckets()["Buckets"]]
    if bucket not in existing:
        s3.create_bucket(Bucket=bucket)
        print(f"Created bucket: {bucket}")

    print(f"Uploading {csv_path} to s3://{bucket}/raw/events.csv ...")
    s3.upload_file(csv_path, bucket, "raw/events.csv", ExtraArgs={"ContentType": "text/csv"})
    print("Upload complete.")


if __name__ == "__main__":
    main()
