"""
Base class for cloud storage connectors with lineage tracking.
"""

import logging
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Iterator
from urllib.parse import urlparse
import pandas as pd
from pathlib import Path
import tempfile

from ..core.dataframe_wrapper import LineageDataFrame

logger = logging.getLogger(__name__)


class CloudStorageConnector(ABC):
    """
    Abstract base class for cloud storage connectors.

    Provides common functionality for cloud storage operations with lineage tracking,
    credential management, and universal cloud storage patterns.
    """

    def __init__(self,
                 bucket_name: str = None,
                 region: str = None,
                 credentials: Dict[str, Any] = None,
                 endpoint_url: str = None,
                 **kwargs):
        """
        Initialize cloud storage connector.

        Args:
            bucket_name: Cloud storage bucket/container name
            region: Cloud region (if applicable)
            credentials: Authentication credentials
            endpoint_url: Custom endpoint URL (for S3-compatible services)
            **kwargs: Additional connector options
        """
        self.bucket_name = bucket_name
        self.region = region
        self.credentials = credentials or {}
        self.endpoint_url = endpoint_url
        self.connection = None
        self.client = None

        # Initialize tracker if provided
        from ..core.tracker import LineageTracker
        self.tracker = kwargs.get('tracker', LineageTracker())

        # Parse cloud URL if provided as single parameter
        if isinstance(bucket_name, str) and '://' in bucket_name:
            self._parse_cloud_url(bucket_name)

    def _parse_cloud_url(self, url: str) -> None:
        """Parse cloud storage URL into components."""
        try:
            parsed = urlparse(url)
            self.protocol = parsed.scheme
            self.bucket_name = parsed.netloc
            self.base_path = parsed.path.lstrip('/')

            # Extract credentials from URL if present
            if parsed.username and parsed.password:
                self.credentials.update({
                    'access_key': parsed.username,
                    'secret_key': parsed.password
                })

        except Exception as e:
            logger.warning(f"Failed to parse cloud URL: {str(e)}")

    @abstractmethod
    def connect(self) -> None:
        """Establish connection to cloud storage service."""
        pass

    def disconnect(self) -> None:
        """Close cloud storage connection."""
        if self.client:
            # Most cloud clients don't need explicit disconnect
            self.client = None
        self.connection = None
        logger.info(f"Disconnected from {self.__class__.__name__}")

    @abstractmethod
    def list_objects(self, prefix: str = "", max_objects: int = 1000) -> List[Dict[str, Any]]:
        """
        List objects in cloud storage.

        Args:
            prefix: Object key prefix to filter
            max_objects: Maximum number of objects to return

        Returns:
            List of object metadata dictionaries
        """
        pass

    @abstractmethod
    def object_exists(self, key: str) -> bool:
        """
        Check if object exists in cloud storage.

        Args:
            key: Object key/path

        Returns:
            True if object exists
        """
        pass

    @abstractmethod
    def get_object_metadata(self, key: str) -> Dict[str, Any]:
        """
        Get object metadata.

        Args:
            key: Object key/path

        Returns:
            Object metadata dictionary
        """
        pass

    @abstractmethod
    def download_object(self, key: str, local_path: str = None) -> str:
        """
        Download object from cloud storage.

        Args:
            key: Object key/path to download
            local_path: Local file path (temp file if None)

        Returns:
            Local file path where object was downloaded
        """
        pass

    @abstractmethod
    def upload_object(self, local_path: str, key: str, metadata: Dict[str, Any] = None) -> bool:
        """
        Upload object to cloud storage.

        Args:
            local_path: Local file path to upload
            key: Destination object key/path
            metadata: Additional object metadata

        Returns:
            True if upload successful
        """
        pass

    def read_parquet(self, key: str, **kwargs) -> LineageDataFrame:
        """
        Read Parquet file from cloud storage with lineage tracking.

        Args:
            key: Object key/path
            **kwargs: Additional pandas.read_parquet options

        Returns:
            LineageDataFrame with tracked lineage
        """
        if not self.connection:
            self.connect()

        try:
            # Download to temporary file
            with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as temp_file:
                local_path = self.download_object(key, temp_file.name)

                # Read with pandas
                df = pd.read_parquet(local_path, **kwargs)

                # Create lineage DataFrame
                lineage_df = self._create_cloud_lineage_dataframe(
                    df, key, "parquet_read"
                )

                # Clean up temp file
                Path(local_path).unlink()

                logger.info(
                    f"Read Parquet from cloud: {df.shape[0]} rows, {df.shape[1]} columns")
                return lineage_df

        except Exception as e:
            logger.error(f"Failed to read Parquet from cloud: {str(e)}")
            raise

    def read_csv(self, key: str, **kwargs) -> LineageDataFrame:
        """
        Read CSV file from cloud storage with lineage tracking.

        Args:
            key: Object key/path
            **kwargs: Additional pandas.read_csv options

        Returns:
            LineageDataFrame with tracked lineage
        """
        if not self.connection:
            self.connect()

        try:
            # Download to temporary file
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.csv', delete=False) as temp_file:
                local_path = self.download_object(key, temp_file.name)

                # Read with pandas
                df = pd.read_csv(local_path, **kwargs)

                # Create lineage DataFrame
                lineage_df = self._create_cloud_lineage_dataframe(
                    df, key, "csv_read"
                )

                # Clean up temp file
                Path(local_path).unlink()

                logger.info(
                    f"Read CSV from cloud: {df.shape[0]} rows, {df.shape[1]} columns")
                return lineage_df

        except Exception as e:
            logger.error(f"Failed to read CSV from cloud: {str(e)}")
            raise

    def read_json(self, key: str, **kwargs) -> LineageDataFrame:
        """
        Read JSON file from cloud storage with lineage tracking.

        Args:
            key: Object key/path
            **kwargs: Additional pandas.read_json options

        Returns:
            LineageDataFrame with tracked lineage
        """
        if not self.connection:
            self.connect()

        try:
            # Download to temporary file
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as temp_file:
                local_path = self.download_object(key, temp_file.name)

                # Read with pandas
                df = pd.read_json(local_path, **kwargs)

                # Create lineage DataFrame
                lineage_df = self._create_cloud_lineage_dataframe(
                    df, key, "json_read"
                )

                # Clean up temp file
                Path(local_path).unlink()

                logger.info(
                    f"Read JSON from cloud: {df.shape[0]} rows, {df.shape[1]} columns")
                return lineage_df

        except Exception as e:
            logger.error(f"Failed to read JSON from cloud: {str(e)}")
            raise

    def write_parquet(self, df: pd.DataFrame, key: str, **kwargs) -> bool:
        """
        Write DataFrame to Parquet in cloud storage.

        Args:
            df: DataFrame to write
            key: Destination object key/path
            **kwargs: Additional to_parquet options

        Returns:
            True if write successful
        """
        if not self.connection:
            self.connect()

        try:
            # Write to temporary file
            with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as temp_file:
                df.to_parquet(temp_file.name, **kwargs)

                # Upload to cloud
                success = self.upload_object(temp_file.name, key)

                # Clean up temp file
                Path(temp_file.name).unlink()

                if success:
                    logger.info(f"Wrote Parquet to cloud: {key}")
                return success

        except Exception as e:
            logger.error(f"Failed to write Parquet to cloud: {str(e)}")
            return False

    def write_csv(self, df: pd.DataFrame, key: str, **kwargs) -> bool:
        """
        Write DataFrame to CSV in cloud storage.

        Args:
            df: DataFrame to write
            key: Destination object key/path
            **kwargs: Additional to_csv options

        Returns:
            True if write successful
        """
        if not self.connection:
            self.connect()

        try:
            # Write to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
                df.to_csv(temp_file.name, index=False, **kwargs)

                # Upload to cloud
                success = self.upload_object(temp_file.name, key)

                # Clean up temp file
                Path(temp_file.name).unlink()

                if success:
                    logger.info(f"Wrote CSV to cloud: {key}")
                return success

        except Exception as e:
            logger.error(f"Failed to write CSV to cloud: {str(e)}")
            return False

    def sync_directory(self, local_dir: str, cloud_prefix: str,
                       exclude_patterns: List[str] = None) -> Dict[str, Any]:
        """
        Sync local directory to cloud storage.

        Args:
            local_dir: Local directory path
            cloud_prefix: Cloud storage prefix/path
            exclude_patterns: File patterns to exclude

        Returns:
            Sync results dictionary
        """
        if not self.connection:
            self.connect()

        exclude_patterns = exclude_patterns or []
        local_path = Path(local_dir)

        if not local_path.exists():
            raise ValueError(f"Local directory does not exist: {local_dir}")

        sync_results = {
            'uploaded': [],
            'skipped': [],
            'errors': []
        }

        try:
            for file_path in local_path.rglob('*'):
                if file_path.is_file():
                    # Check exclude patterns
                    skip = False
                    for pattern in exclude_patterns:
                        if file_path.match(pattern):
                            sync_results['skipped'].append(str(file_path))
                            skip = True
                            break

                    if skip:
                        continue

                    # Calculate cloud key
                    relative_path = file_path.relative_to(local_path)
                    cloud_key = f"{cloud_prefix.rstrip('/')}/{relative_path}".replace(
                        '\\', '/')

                    try:
                        success = self.upload_object(str(file_path), cloud_key)
                        if success:
                            sync_results['uploaded'].append(cloud_key)
                        else:
                            sync_results['errors'].append(
                                f"Upload failed: {cloud_key}")
                    except Exception as e:
                        sync_results['errors'].append(
                            f"Error uploading {cloud_key}: {str(e)}")

            logger.info(f"Directory sync complete: {len(sync_results['uploaded'])} uploaded, "
                        f"{len(sync_results['skipped'])} skipped, {len(sync_results['errors'])} errors")

            return sync_results

        except Exception as e:
            logger.error(f"Failed to sync directory: {str(e)}")
            raise

    def _create_cloud_lineage_dataframe(self, df: pd.DataFrame,
                                        object_key: str,
                                        operation_name: str = "cloud_read") -> LineageDataFrame:
        """
        Create LineageDataFrame with cloud object source tracking.

        Args:
            df: Source DataFrame
            object_key: Cloud object key/path
            operation_name: Name of the operation performed

        Returns:
            LineageDataFrame with cloud lineage
        """
        # Create unique node ID for this cloud object
        cloud_node_id = f"cloud_{abs(hash(f'{self.bucket_name}/{object_key}'))}"

        # Create cloud source node if it doesn't exist
        if cloud_node_id not in self.tracker.nodes:
            from ..core.nodes import CloudNode

            # Get object metadata
            try:
                metadata = self.get_object_metadata(object_key)
            except:
                metadata = {}

            cloud_node = CloudNode(
                id=cloud_node_id,
                name=Path(object_key).name,
                object_key=object_key,
                bucket_name=self.bucket_name,
                cloud_provider=self.__class__.__name__.replace(
                    'Connector', '').lower(),
                size_bytes=metadata.get('size', 0),
                columns=set(df.columns),
                metadata=metadata
            )

            self.tracker.add_node(cloud_node)

        # Create LineageDataFrame
        lineage_df = LineageDataFrame(
            df,
            tracker=self.tracker,
            operation_name=operation_name,
            source_node_ids=[cloud_node_id]
        )

        return lineage_df

    def test_connection(self) -> bool:
        """Test cloud storage connectivity."""
        try:
            if not self.connection:
                self.connect()

            # Try to list objects (limited)
            objects = self.list_objects(max_objects=1)
            return True

        except Exception as e:
            logger.error(f"Cloud connection test failed: {str(e)}")
            return False

    def get_connection_info(self) -> Dict[str, Any]:
        """Get cloud storage connection information."""
        if not hasattr(self, 'connection') or not self.connection:
            return {'status': 'disconnected'}

        try:
            info = {
                'status': 'connected',
                'connector_type': 'cloud_storage',
                'cloud_provider': self.__class__.__name__.replace('Connector', '').lower(),
                'bucket_name': self.bucket_name,
                'region': self.region,
                'endpoint_url': self.endpoint_url,
            }

            return info

        except Exception as e:
            logger.error(f"Failed to get connection info: {str(e)}")
            return {'status': 'error', 'error': str(e)}

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(bucket='{self.bucket_name}')"

    def __repr__(self) -> str:
        return self.__str__()
