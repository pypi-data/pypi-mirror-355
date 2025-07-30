"""
Base class for file-based connectors with lineage tracking.
"""

import logging
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
import pandas as pd
from pathlib import Path

from ..core.dataframe_wrapper import LineageDataFrame

logger = logging.getLogger(__name__)


class FileConnector(ABC):
    """
    Abstract base class for file-based connectors.

    Provides common functionality for reading files with lineage tracking,
    schema detection, and metadata extraction.
    """

    def __init__(self, file_path: Union[str, Path], **kwargs):
        """
        Initialize file connector.

        Args:
            file_path: Path to the file or directory
            **kwargs: Additional connector options
        """
        self.file_path = Path(file_path) if isinstance(
            file_path, str) else file_path
        self.connection_string = str(self.file_path)
        self.metadata_cache = {}
        self.connection = None  # Connection state

        # Initialize tracker if provided
        from ..core.tracker import LineageTracker
        self.tracker = kwargs.get('tracker', LineageTracker())

    def connect(self) -> None:
        """Validate file path and accessibility."""
        try:
            if not self.file_path.exists():
                raise FileNotFoundError(f"File not found: {self.file_path}")

            if not self.file_path.is_file() and not self.file_path.is_dir():
                raise ValueError(
                    f"Path is neither file nor directory: {self.file_path}")

            # Set connection flag
            self.connection = True
            logger.info(f"Connected to file: {self.file_path}")

        except Exception as e:
            logger.error(
                f"Failed to connect to file {self.file_path}: {str(e)}")
            raise

    def disconnect(self) -> None:
        """Close file connection."""
        self.connection = None
        self.metadata_cache.clear()
        logger.info(f"Disconnected from file: {self.file_path}")

    @abstractmethod
    def read_file(self, **kwargs) -> LineageDataFrame:
        """
        Read file with lineage tracking.

        Returns:
            LineageDataFrame with tracked lineage
        """
        pass

    @abstractmethod
    def get_schema(self) -> Dict[str, str]:
        """
        Get file schema information.

        Returns:
            Dictionary mapping column names to data types
        """
        pass

    def get_file_metadata(self) -> Dict[str, Any]:
        """
        Get comprehensive file metadata.

        Returns:
            Dictionary with file information
        """
        if not self.file_path.exists():
            return {'exists': False}

        try:
            stat = self.file_path.stat()

            metadata = {
                'exists': True,
                'path': str(self.file_path.absolute()),
                'name': self.file_path.name,
                'size_bytes': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'modified_time': stat.st_mtime,
                'created_time': stat.st_ctime,
                'is_file': self.file_path.is_file(),
                'is_directory': self.file_path.is_dir(),
                'extension': self.file_path.suffix.lower(),
                'parent_directory': str(self.file_path.parent),
            }

            # Add permissions info
            metadata.update({
                'readable': os.access(self.file_path, os.R_OK),
                'writable': os.access(self.file_path, os.W_OK),
                'executable': os.access(self.file_path, os.X_OK),
            })

            return metadata

        except Exception as e:
            logger.error(f"Failed to get file metadata: {str(e)}")
            return {'exists': True, 'error': str(e)}

    def _create_file_lineage_dataframe(self, df: pd.DataFrame,
                                       operation_name: str = "file_read") -> LineageDataFrame:
        """
        Create LineageDataFrame with file source tracking.

        Args:
            df: Source DataFrame
            operation_name: Name of the operation performed

        Returns:
            LineageDataFrame with file lineage
        """
        # Create unique node ID for this file
        file_node_id = f"file_{abs(hash(str(self.file_path)))}"

        # Create file source node if it doesn't exist
        if file_node_id not in self.tracker.nodes:
            from ..core.nodes import FileNode

            metadata = self.get_file_metadata()
            schema_info = self.get_schema() if hasattr(self, 'get_schema') else {}

            file_node = FileNode(
                id=file_node_id,
                name=self.file_path.name,
                file_path=str(self.file_path),
                file_type=self.file_path.suffix.lower().lstrip('.'),
                size_bytes=metadata.get('size_bytes', 0),
                columns=set(schema_info.keys()
                            ) if schema_info else set(df.columns),
                metadata=metadata
            )

            self.tracker.add_node(file_node)

        # Create LineageDataFrame
        lineage_df = LineageDataFrame(
            df,
            tracker=self.tracker,
            operation_name=operation_name,
            source_node_ids=[file_node_id]
        )

        return lineage_df

    def test_connection(self) -> bool:
        """Test file accessibility."""
        try:
            if not self.file_path.exists():
                return False

            # Try to read basic metadata
            self.get_file_metadata()
            return True

        except Exception as e:
            logger.error(f"File connection test failed: {str(e)}")
            return False

    def get_connection_info(self) -> Dict[str, Any]:
        """Get file connection information."""
        if not hasattr(self, 'connection') or not self.connection:
            return {'status': 'disconnected'}

        try:
            metadata = self.get_file_metadata()

            info = {
                'status': 'connected',
                'connector_type': 'file',
                'file_path': str(self.file_path),
                'file_exists': metadata.get('exists', False),
                'file_size_mb': metadata.get('size_mb', 0),
                'file_type': metadata.get('extension', 'unknown'),
                'readable': metadata.get('readable', False),
            }

            return info

        except Exception as e:
            logger.error(f"Failed to get connection info: {str(e)}")
            return {'status': 'error', 'error': str(e)}

    def list_files(self, pattern: str = "*") -> List[str]:
        """
        List files in directory (if path is directory).

        Args:
            pattern: Glob pattern for file matching

        Returns:
            List of file paths
        """
        try:
            if self.file_path.is_file():
                return [str(self.file_path)]
            elif self.file_path.is_dir():
                files = list(self.file_path.glob(pattern))
                return [str(f) for f in files if f.is_file()]
            else:
                return []

        except Exception as e:
            logger.error(f"Failed to list files: {str(e)}")
            return []

    def validate_file_format(self) -> bool:
        """
        Validate that file format matches connector expectations.

        Returns:
            True if file format is compatible
        """
        # Default implementation - can be overridden by specific connectors
        return True

    def get_sample_data(self, n_rows: int = 5) -> pd.DataFrame:
        """
        Get sample data from file for preview.

        Args:
            n_rows: Number of rows to sample

        Returns:
            Sample DataFrame
        """
        try:
            # This should be implemented by specific connectors
            full_df = self.read_file()
            return full_df.head(n_rows)

        except Exception as e:
            logger.error(f"Failed to get sample data: {str(e)}")
            return pd.DataFrame()

    def estimate_memory_usage(self) -> Dict[str, Any]:
        """
        Estimate memory usage for loading the file.

        Returns:
            Dictionary with memory estimates
        """
        try:
            metadata = self.get_file_metadata()
            file_size_mb = metadata.get('size_mb', 0)

            # Rough estimates (can be refined by specific connectors)
            estimates = {
                'file_size_mb': file_size_mb,
                'estimated_memory_mb': file_size_mb * 2,  # Conservative estimate
                'recommended_chunksize': max(1000, int(100000 / max(1, file_size_mb))),
                'can_load_in_memory': file_size_mb < 500,  # 500MB threshold
            }

            return estimates

        except Exception as e:
            logger.error(f"Failed to estimate memory usage: {str(e)}")
            return {'error': str(e)}

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(path='{self.file_path}')"

    def __repr__(self) -> str:
        return self.__str__()
