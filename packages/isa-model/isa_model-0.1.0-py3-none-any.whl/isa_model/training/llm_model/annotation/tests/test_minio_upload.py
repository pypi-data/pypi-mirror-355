#!/usr/bin/env python3
import os
from minio import Minio
import io

# MinIO client setup
client = Minio(
    "localhost:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)

# Test bucket name
bucket_name = "test-bucket"

# Create bucket if not exists
if not client.bucket_exists(bucket_name):
    client.make_bucket(bucket_name)
    print(f"Created bucket: {bucket_name}")
else:
    print(f"Bucket already exists: {bucket_name}")

# Upload test file
source_file = "init-scripts/files/haley_system.txt"
if os.path.exists(source_file):
    with open(source_file, 'rb') as file_data:
        content = file_data.read()
        # Upload file
        client.put_object(
            bucket_name,
            "haley_system.txt",
            io.BytesIO(content),
            len(content),
            content_type="text/plain"
        )
        print(f"Successfully uploaded {source_file}")
        
        # Verify upload
        stat = client.stat_object(bucket_name, "haley_system.txt")
        print(f"File stats: {stat}")
else:
    print(f"Source file not found: {source_file}") 