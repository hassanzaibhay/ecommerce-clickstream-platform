#!/usr/bin/env python3
"""Load a random 1% sample of raw CSV into MinIO for development."""
import os
import random
import sys
import tempfile

import boto3
from botocore.client import Config


def main() -> None:
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "/data/events.csv"
    sample_rate = float(sys.argv[2]) if len(sys.argv) > 2 else 0.01

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

    print(f"Sampling {sample_rate*100:.1f}% of {csv_path} ...")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as tmp:
        tmp_path = tmp.name
        with open(csv_path, "r") as f:
            header = f.readline()
            tmp.write(header)
            count = 0
            for line in f:
                if random.random() < sample_rate:
                    tmp.write(line)
                    count += 1

    print(f"Sampled {count} rows.")
    print(f"Uploading to s3://{bucket}/raw/events_sample.csv ...")
    s3.upload_file(tmp_path, bucket, "raw/events_sample.csv", ExtraArgs={"ContentType": "text/csv"})
    os.unlink(tmp_path)
    print("Sample upload complete.")


if __name__ == "__main__":
    main()
