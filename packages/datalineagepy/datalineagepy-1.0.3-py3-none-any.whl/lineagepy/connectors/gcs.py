"""
Google Cloud Storage (GCS) connector for cloud storage operations with lineage tracking.
"""

import logging
import os
import tempfile
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

try:
    from google.cloud import storage
    from google.auth import default
    from google.auth.exceptions import DefaultCredentialsError
    from google.cloud.exceptions import NotFound, Forbidden
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False

from .cloud_base import CloudStorageConnector

logger = logging.getLogger(__name__)


class GCSConnector(CloudStorageConnector):
    """
    Google Cloud Storage connector with comprehensive cloud storage operations.

    Features:
    - Full GCS API integration with google-cloud-storage
    - Multiple authentication methods (service account, ADC, metadata server)
    - Multi-region and dual-region bucket support
    - IAM and access control integration
    - Lifecycle policy and versioning support
    - BigQuery integration for seamless data transfer
    """

    def __init__(self,
                 bucket_name: str,
                 project_id: str = None,
                 credentials_path: str = None,
                 credentials: Dict[str, Any] = None,
                 location: str = None,
                 storage_class: str = "STANDARD",
                 **kwargs):
        """
        Initialize GCS connector.

        Args:
            bucket_name: GCS bucket name
            project_id: Google Cloud Project ID
            credentials_path: Path to service account JSON file
            credentials: Credentials dictionary or object
            location: Bucket location/region (e.g., 'us-central1', 'eu')
            storage_class: Default storage class (STANDARD, COLDLINE, NEARLINE, ARCHIVE)
            **kwargs: Additional connector options
        """
        if not GCS_AVAILABLE:
            raise ImportError(
                "google-cloud-storage is required for GCS connector. "
                "Install with: pip install google-cloud-storage"
            )

        super().__init__(bucket_name, location, credentials, **kwargs)

        self.project_id = project_id
        self.credentials_path = credentials_path
        self.location = location or 'us-central1'
        self.storage_class = storage_class
        self.client = None
        self.bucket = None

        # GCS-specific configuration
        self.enable_versioning = kwargs.get('enable_versioning', False)
        self.lifecycle_rules = kwargs.get('lifecycle_rules', [])
        self.cors_rules = kwargs.get('cors_rules', [])

    def connect(self) -> None:
        """Establish connection to Google Cloud Storage."""
        try:
            # Initialize credentials
            credentials = None
            if self.credentials_path:
                # Use service account file
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.credentials_path
            elif self.credentials:
                # Use provided credentials object
                credentials = self.credentials

            # Create client
            if credentials:
                self.client = storage.Client(
                    project=self.project_id,
                    credentials=credentials
                )
            else:
                # Use Application Default Credentials (ADC)
                self.client = storage.Client(project=self.project_id)

            # Get or create bucket
            try:
                self.bucket = self.client.bucket(self.bucket_name)
                # Test bucket access
                self.bucket.reload()
                self.connection = True
                logger.info(f"Connected to GCS bucket: {self.bucket_name}")

            except NotFound:
                if kwargs.get('create_if_not_exists', False):
                    self._create_bucket()
                else:
                    raise ValueError(
                        f"GCS bucket '{self.bucket_name}' does not exist")

        except DefaultCredentialsError:
            raise ConnectionError(
                "GCS credentials not found. Set GOOGLE_APPLICATION_CREDENTIALS "
                "environment variable or provide credentials_path"
            )
        except Forbidden:
            raise PermissionError(
                f"Access denied to GCS bucket '{self.bucket_name}'"
            )
        except Exception as e:
            raise ConnectionError(f"Failed to connect to GCS: {str(e)}")

    def _create_bucket(self) -> None:
        """Create GCS bucket with specified configuration."""
        try:
            bucket = self.client.bucket(self.bucket_name)
            bucket.storage_class = self.storage_class
            bucket.location = self.location

            # Create bucket
            bucket = self.client.create_bucket(bucket, location=self.location)

            # Configure versioning
            if self.enable_versioning:
                bucket.versioning_enabled = True
                bucket.patch()

            # Set lifecycle rules
            if self.lifecycle_rules:
                bucket.lifecycle_rules = self.lifecycle_rules
                bucket.patch()

            self.bucket = bucket
            logger.info(
                f"Created GCS bucket: {self.bucket_name} in {self.location}")

        except Exception as e:
            raise ConnectionError(f"Failed to create GCS bucket: {str(e)}")

    def list_objects(self, prefix: str = "", max_objects: int = 1000) -> List[Dict[str, Any]]:
        """List objects in GCS bucket."""
        if not self.connection:
            self.connect()

        try:
            objects = []
            blobs = self.client.list_blobs(
                self.bucket,
                prefix=prefix,
                max_results=max_objects
            )

            for blob in blobs:
                objects.append({
                    'key': blob.name,
                    'size': blob.size or 0,
                    'last_modified': blob.updated,
                    'etag': blob.etag,
                    'storage_class': blob.storage_class,
                    'content_type': blob.content_type,
                    'generation': blob.generation,
                    'metageneration': blob.metageneration,
                    'md5_hash': blob.md5_hash,
                    'crc32c': blob.crc32c
                })

            logger.info(
                f"Listed {len(objects)} objects with prefix '{prefix}'")
            return objects

        except Exception as e:
            logger.error(f"Failed to list GCS objects: {e}")
            raise

    def object_exists(self, key: str) -> bool:
        """Check if object exists in GCS bucket."""
        if not self.connection:
            self.connect()

        try:
            blob = self.bucket.blob(key)
            return blob.exists()
        except Exception:
            return False

    def get_object_metadata(self, key: str) -> Dict[str, Any]:
        """Get GCS object metadata."""
        if not self.connection:
            self.connect()

        try:
            blob = self.bucket.blob(key)
            blob.reload()

            metadata = {
                'size': blob.size,
                'last_modified': blob.updated,
                'etag': blob.etag,
                'content_type': blob.content_type,
                'storage_class': blob.storage_class,
                'generation': blob.generation,
                'metageneration': blob.metageneration,
                'md5_hash': blob.md5_hash,
                'crc32c': blob.crc32c,
                'custom_metadata': blob.metadata or {}
            }

            return metadata

        except NotFound:
            raise FileNotFoundError(f"Object not found: {key}")
        except Exception as e:
            logger.error(f"Failed to get GCS object metadata: {e}")
            raise

    def download_object(self, key: str, local_path: str = None) -> str:
        """Download object from GCS."""
        if not self.connection:
            self.connect()

        try:
            blob = self.bucket.blob(key)

            if local_path is None:
                # Create temporary file
                temp_file = tempfile.NamedTemporaryFile(delete=False)
                local_path = temp_file.name
                temp_file.close()

            # Download blob
            blob.download_to_filename(local_path)

            logger.info(f"Downloaded GCS object {key} to {local_path}")
            return local_path

        except NotFound:
            raise FileNotFoundError(f"Object not found: {key}")
        except Exception as e:
            logger.error(f"Failed to download GCS object: {e}")
            raise

    def upload_object(self, local_path: str, key: str, metadata: Dict[str, Any] = None) -> bool:
        """Upload object to GCS."""
        if not self.connection:
            self.connect()

        try:
            blob = self.bucket.blob(key)

            # Set metadata
            if metadata:
                blob.metadata = metadata

            # Auto-detect content type
            if not blob.content_type:
                import mimetypes
                content_type, _ = mimetypes.guess_type(local_path)
                if content_type:
                    blob.content_type = content_type

            # Upload file
            blob.upload_from_filename(local_path)

            logger.info(f"Uploaded {local_path} to GCS object {key}")
            return True

        except Exception as e:
            logger.error(f"Failed to upload to GCS: {e}")
            raise

    def copy_object(self, source_key: str, destination_key: str,
                    source_bucket: str = None) -> bool:
        """Copy object within GCS or between buckets."""
        if not self.connection:
            self.connect()

        try:
            # Source blob
            if source_bucket:
                source_bucket_obj = self.client.bucket(source_bucket)
            else:
                source_bucket_obj = self.bucket

            source_blob = source_bucket_obj.blob(source_key)

            # Destination blob
            destination_blob = self.bucket.blob(destination_key)

            # Copy blob
            destination_blob.rewrite(source_blob)

            logger.info(f"Copied {source_key} to {destination_key}")
            return True

        except Exception as e:
            logger.error(f"Failed to copy GCS object: {e}")
            raise

    def delete_object(self, key: str) -> bool:
        """Delete object from GCS."""
        if not self.connection:
            self.connect()

        try:
            blob = self.bucket.blob(key)
            blob.delete()

            logger.info(f"Deleted GCS object: {key}")
            return True

        except NotFound:
            logger.warning(f"Object not found for deletion: {key}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete GCS object: {e}")
            raise

    def generate_signed_url(self, key: str, expiration: int = 3600,
                            method: str = 'GET') -> str:
        """Generate signed URL for secure access to GCS object."""
        if not self.connection:
            self.connect()

        try:
            blob = self.bucket.blob(key)

            from datetime import timedelta
            url = blob.generate_signed_url(
                expiration=timedelta(seconds=expiration),
                method=method
            )

            logger.info(
                f"Generated signed URL for {key} (expires in {expiration}s)")
            return url

        except Exception as e:
            logger.error(f"Failed to generate signed URL: {e}")
            raise

    def sync_to_bigquery(self, key: str, dataset_id: str, table_id: str,
                         job_config: Dict[str, Any] = None) -> bool:
        """Sync GCS object to BigQuery table with lineage tracking."""
        if not self.connection:
            self.connect()

        try:
            from google.cloud import bigquery

            # Initialize BigQuery client
            bq_client = bigquery.Client(project=self.project_id)

            # Construct URI
            uri = f"gs://{self.bucket_name}/{key}"

            # Default job config
            if job_config is None:
                job_config = {
                    'source_format': bigquery.SourceFormat.PARQUET,
                    'autodetect': True,
                    'write_disposition': bigquery.WriteDisposition.WRITE_TRUNCATE
                }

            # Create load job
            table_ref = bq_client.dataset(dataset_id).table(table_id)
            load_job = bq_client.load_table_from_uri(
                uri, table_ref, job_config=bigquery.LoadJobConfig(**job_config)
            )

            # Wait for job to complete
            load_job.result()

            # Track lineage from GCS to BigQuery
            if self.tracker:
                from ..core.nodes import CloudNode
                gcs_node = CloudNode(
                    node_id=f"gcs_{self.bucket_name}_{key}",
                    name=f"GCS: {key}",
                    bucket_name=self.bucket_name,
                    object_key=key,
                    cloud_provider="gcp"
                )

                bq_node = CloudNode(
                    node_id=f"bq_{dataset_id}_{table_id}",
                    name=f"BigQuery: {dataset_id}.{table_id}",
                    bucket_name=dataset_id,
                    object_key=table_id,
                    cloud_provider="gcp"
                )

                self.tracker.add_node(gcs_node)
                self.tracker.add_node(bq_node)
                self.tracker.add_edge(gcs_node.node_id, bq_node.node_id,
                                      "gcs_to_bigquery_sync")

            logger.info(
                f"Synced {key} to BigQuery table {dataset_id}.{table_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to sync to BigQuery: {e}")
            raise

    def get_bucket_info(self) -> Dict[str, Any]:
        """Get comprehensive bucket information."""
        if not self.connection:
            self.connect()

        try:
            self.bucket.reload()

            return {
                'name': self.bucket.name,
                'location': self.bucket.location,
                'storage_class': self.bucket.storage_class,
                'created': self.bucket.time_created,
                'updated': self.bucket.updated,
                'versioning_enabled': self.bucket.versioning_enabled,
                'lifecycle_rules': len(self.bucket.lifecycle_rules),
                'cors_rules': len(self.bucket.cors),
                'labels': self.bucket.labels,
                'iam_configuration': {
                    'uniform_bucket_level_access':
                        self.bucket.iam_configuration.uniform_bucket_level_access_enabled
                },
                'retention_policy': {
                    'retention_period': self.bucket.retention_period,
                    'effective_time': self.bucket.retention_policy_effective_time,
                    'is_locked': self.bucket.retention_policy_locked
                } if self.bucket.retention_period else None
            }

        except Exception as e:
            logger.error(f"Failed to get bucket info: {e}")
            raise

    def __str__(self) -> str:
        return f"GCSConnector(bucket={self.bucket_name}, project={self.project_id})"

    def __repr__(self) -> str:
        return self.__str__()
