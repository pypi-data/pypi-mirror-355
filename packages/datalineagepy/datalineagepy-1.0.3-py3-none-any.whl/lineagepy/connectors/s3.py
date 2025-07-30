"""
AWS S3 connector for cloud storage operations with lineage tracking.
"""

import logging
import os
import tempfile
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False

from .cloud_base import CloudStorageConnector

logger = logging.getLogger(__name__)


class S3Connector(CloudStorageConnector):
    """
    AWS S3 connector with comprehensive cloud storage operations.

    Features:
    - Full S3 API integration with boto3
    - Automatic credential discovery (IAM, profiles, environment)
    - Multi-region support with automatic region detection
    - Presigned URL generation for secure access
    - Bucket lifecycle and versioning support
    """

    def __init__(self,
                 bucket_name: str,
                 region: str = None,
                 credentials: Dict[str, Any] = None,
                 endpoint_url: str = None,
                 profile_name: str = None,
                 use_ssl: bool = True,
                 **kwargs):
        """
        Initialize S3 connector.

        Args:
            bucket_name: S3 bucket name
            region: AWS region (auto-detected if not provided)
            credentials: AWS credentials dict with access_key_id, secret_access_key, session_token
            endpoint_url: Custom S3 endpoint URL (for S3-compatible services)
            profile_name: AWS profile name from ~/.aws/credentials
            use_ssl: Whether to use SSL/TLS for connections
            **kwargs: Additional connector options
        """
        if not S3_AVAILABLE:
            raise ImportError(
                "boto3 is required for S3 connector. Install with: pip install boto3")

        super().__init__(bucket_name, region, credentials, endpoint_url, **kwargs)

        self.profile_name = profile_name
        self.use_ssl = use_ssl
        self.s3_client = None
        self.s3_resource = None
        self.session = None

        # S3-specific configuration
        self.transfer_config = kwargs.get('transfer_config', {})
        self.use_accelerate = kwargs.get('use_accelerate', False)
        self.addressing_style = kwargs.get('addressing_style', 'auto')

    def connect(self) -> None:
        """Establish connection to AWS S3."""
        try:
            # Create boto3 session
            session_kwargs = {}

            if self.profile_name:
                session_kwargs['profile_name'] = self.profile_name
            elif self.credentials:
                session_kwargs.update({
                    'aws_access_key_id': self.credentials.get('access_key_id'),
                    'aws_secret_access_key': self.credentials.get('secret_access_key'),
                    'aws_session_token': self.credentials.get('session_token')
                })

            self.session = boto3.Session(**session_kwargs)

            # Set region - try to detect if not provided
            region = self.region
            if not region:
                region = self._detect_bucket_region()

            # Create S3 client
            client_kwargs = {
                'service_name': 's3',
                'region_name': region
            }

            if self.endpoint_url:
                client_kwargs['endpoint_url'] = self.endpoint_url

            self.s3_client = self.session.client(**client_kwargs)

            # Test connection by checking bucket access
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            self.connection = True

            logger.info(
                f"Connected to S3 bucket: {self.bucket_name} in region: {region}")

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucket':
                raise ValueError(
                    f"S3 bucket '{self.bucket_name}' does not exist")
            elif error_code == 'AccessDenied':
                raise PermissionError(
                    f"Access denied to S3 bucket '{self.bucket_name}'")
            else:
                raise ConnectionError(f"Failed to connect to S3: {e}")
        except NoCredentialsError:
            raise ConnectionError("AWS credentials not found")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to S3: {str(e)}")

    def _detect_bucket_region(self) -> str:
        """Detect the region of the S3 bucket."""
        try:
            temp_client = self.session.client('s3')
            response = temp_client.get_bucket_location(Bucket=self.bucket_name)
            region = response.get('LocationConstraint')
            return region if region else 'us-east-1'
        except:
            return 'us-east-1'

    def list_objects(self, prefix: str = "", max_objects: int = 1000) -> List[Dict[str, Any]]:
        """List objects in S3 bucket."""
        if not self.connection:
            self.connect()

        try:
            objects = []
            paginator = self.s3_client.get_paginator('list_objects_v2')

            page_iterator = paginator.paginate(
                Bucket=self.bucket_name,
                Prefix=prefix,
                PaginationConfig={'MaxItems': max_objects}
            )

            for page in page_iterator:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        objects.append({
                            'key': obj['Key'],
                            'size': obj['Size'],
                            'last_modified': obj['LastModified'],
                            'etag': obj['ETag'].strip('"'),
                            'storage_class': obj.get('StorageClass', 'STANDARD')
                        })

            logger.info(
                f"Listed {len(objects)} objects with prefix '{prefix}'")
            return objects

        except ClientError as e:
            logger.error(f"Failed to list S3 objects: {e}")
            raise

    def object_exists(self, key: str) -> bool:
        """Check if object exists in S3 bucket."""
        if not self.connection:
            self.connect()

        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise

    def get_object_metadata(self, key: str) -> Dict[str, Any]:
        """Get S3 object metadata."""
        if not self.connection:
            self.connect()

        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name, Key=key)

            metadata = {
                'size': response['ContentLength'],
                'last_modified': response['LastModified'],
                'etag': response['ETag'].strip('"'),
                'content_type': response.get('ContentType'),
                'storage_class': response.get('StorageClass', 'STANDARD'),
                'metadata': response.get('Metadata', {})
            }

            return metadata

        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                raise FileNotFoundError(f"S3 object not found: {key}")
            raise

    def download_object(self, key: str, local_path: str = None) -> str:
        """Download object from S3."""
        if not self.connection:
            self.connect()

        if local_path is None:
            suffix = Path(key).suffix or '.tmp'
            temp_file = tempfile.NamedTemporaryFile(
                delete=False, suffix=suffix)
            local_path = temp_file.name
            temp_file.close()

        try:
            self.s3_client.download_file(self.bucket_name, key, local_path)
            logger.info(f"Downloaded S3 object {key} to {local_path}")
            return local_path

        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                raise FileNotFoundError(f"S3 object not found: {key}")
            logger.error(f"Failed to download S3 object: {e}")
            raise

    def upload_object(self, local_path: str, key: str, metadata: Dict[str, Any] = None) -> bool:
        """Upload object to S3."""
        if not self.connection:
            self.connect()

        if not Path(local_path).exists():
            raise FileNotFoundError(f"Local file not found: {local_path}")

        try:
            extra_args = {}

            if metadata:
                extra_args['Metadata'] = metadata

            # Auto-detect content type
            import mimetypes
            content_type, _ = mimetypes.guess_type(local_path)
            if content_type:
                extra_args['ContentType'] = content_type

            self.s3_client.upload_file(
                local_path, self.bucket_name, key, ExtraArgs=extra_args
            )

            logger.info(f"Uploaded {local_path} to S3 object {key}")
            return True

        except Exception as e:
            logger.error(f"Failed to upload to S3: {e}")
            return False

    def generate_presigned_url(self, key: str, expiration: int = 3600) -> str:
        """Generate presigned URL for S3 object access."""
        if not self.connection:
            self.connect()

        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': key},
                ExpiresIn=expiration
            )

            logger.info(f"Generated presigned URL for {key}")
            return url

        except Exception as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise

    def __str__(self) -> str:
        return f"S3Connector(bucket='{self.bucket_name}', region='{self.region}')"
