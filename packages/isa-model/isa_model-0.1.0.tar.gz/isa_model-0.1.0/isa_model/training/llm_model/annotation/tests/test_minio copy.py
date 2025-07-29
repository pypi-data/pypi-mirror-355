#!/usr/bin/env python3

import os
from minio import Minio
import json
import logging
from io import BytesIO

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_minio():
    try:
        # Get MinIO host from environment variable or use default
        minio_host = os.getenv("MINIO_HOST", "localhost:9000")
        logger.info(f"Using MinIO host: {minio_host}")
        
        # 1. Create MinIO client
        logger.info("Creating MinIO client...")
        client = Minio(
            minio_host,
            access_key="minioadmin",
            secret_key="minioadmin",
            secure=False
        )
        
        # 2. Test bucket operations
        bucket_name = "knowledge-files"  # Changed to match the actual bucket name
        logger.info(f"Testing bucket operations with {bucket_name}...")
        
        # Create bucket if it doesn't exist
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            logger.info(f"Created new bucket: {bucket_name}")
        else:
            logger.info(f"Using existing bucket: {bucket_name}")
        
        # Set bucket policy - allow all operations
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": [
                        "s3:GetBucketLocation",
                        "s3:ListBucket",
                        "s3:ListBucketMultipartUploads"
                    ],
                    "Resource": [f"arn:aws:s3:::{bucket_name}"]
                },
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": [
                        "s3:AbortMultipartUpload",
                        "s3:DeleteObject",
                        "s3:GetObject",
                        "s3:ListMultipartUploadParts",
                        "s3:PutObject"
                    ],
                    "Resource": [f"arn:aws:s3:::{bucket_name}/*"]
                }
            ]
        }
        
        try:
            client.set_bucket_policy(bucket_name, json.dumps(policy))
            logger.info("Set bucket policy successfully")
        except Exception as e:
            logger.warning(f"Failed to set bucket policy: {e}")
        
        # 3. Test file upload
        source_file = "init-scripts/files/haley_system.txt"
        object_name = "haley_system.txt"
        
        if os.path.exists(source_file):
            # Get file size
            file_size = os.path.getsize(source_file)
            logger.info(f"Found source file: {source_file} (size: {file_size} bytes)")
            
            # Upload file
            with open(source_file, 'rb') as file_data:
                client.put_object(
                    bucket_name,
                    object_name,
                    file_data,
                    file_size,
                    content_type="text/plain"
                )
            logger.info(f"Uploaded file: {object_name}")
            
            # 4. Test file download
            data = client.get_object(bucket_name, object_name)
            content = data.read().decode('utf-8')
            logger.info(f"Successfully downloaded file. First 100 chars: {content[:100]}...")
            
            # 5. Verify file exists
            stat = client.stat_object(bucket_name, object_name)
            logger.info(f"File stats: {stat}")
            
            logger.info("Test completed successfully!")
        else:
            logger.error(f"Source file not found: {source_file}")
            raise FileNotFoundError(f"Source file not found: {source_file}")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    test_minio() 