"""
Data node classes for representing different types of data sources in the lineage graph.
"""

import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
import os


class DataNode:
    """
    Base class for representing a data node in the lineage graph.

    A data node represents any data entity that can be tracked in the lineage,
    such as DataFrames, files, database tables, etc.
    """

    def __init__(self, name: str, metadata: Optional[Dict] = None):
        """
        Initialize a data node.

        Args:
            name: Human-readable name for the node
            metadata: Additional metadata about the node
        """
        self.id = str(uuid.uuid4())
        self.name = name
        self.created_at = datetime.now()
        self.metadata = metadata or {}
        self.node_type = "data"

        # Schema information
        self.columns: List[str] = []
        self.schema: Dict[str, str] = {}

    def add_column(self, column_name: str, column_type: str = "unknown"):
        """Add a column to this node's schema."""
        if column_name not in self.columns:
            self.columns.append(column_name)
        self.schema[column_name] = column_type

    def set_schema(self, schema: Dict[str, str]):
        """Set the complete schema for this node."""
        self.schema = schema
        self.columns = list(schema.keys())

    def get_schema(self) -> Dict[str, str]:
        """Get the schema information for this node."""
        return self.schema.copy()

    def to_dict(self) -> Dict:
        """Convert node to dictionary representation."""
        return {
            'id': self.id,
            'name': self.name,
            'node_type': self.node_type,
            'created_at': self.created_at.isoformat(),
            'columns': self.columns,
            'schema': self.schema,
            'metadata': self.metadata
        }

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', columns={len(self.columns)})"

    def __repr__(self) -> str:
        return self.__str__()


class FileNode(DataNode):
    """
    Data node representing a file-based data source.

    This includes CSV, JSON, Parquet, Excel files, etc.
    """

    def __init__(self, file_path: str, metadata: Optional[Dict] = None):
        """
        Initialize a file node.

        Args:
            file_path: Path to the file
            metadata: Additional metadata about the file
        """
        super().__init__(file_path, metadata)
        self.node_type = "file"
        self.file_path = file_path

        # File-specific metadata
        self.file_format = self._detect_file_format(file_path)
        self.file_size = self._get_file_size(file_path)
        self.last_modified = self._get_last_modified(file_path)

        # Update metadata with file information
        self.metadata.update({
            'file_format': self.file_format,
            'file_size': self.file_size,
            'last_modified': self.last_modified.isoformat() if self.last_modified else None
        })

    def _detect_file_format(self, file_path: str) -> str:
        """Detect file format from extension."""
        if not file_path:
            return "unknown"

        ext = os.path.splitext(file_path)[1].lower()
        format_map = {
            '.csv': 'csv',
            '.json': 'json',
            '.jsonl': 'jsonl',
            '.parquet': 'parquet',
            '.xlsx': 'excel',
            '.xls': 'excel',
            '.txt': 'text',
            '.tsv': 'tsv'
        }
        return format_map.get(ext, 'unknown')

    def _get_file_size(self, file_path: str) -> Optional[int]:
        """Get file size in bytes."""
        try:
            if os.path.exists(file_path):
                return os.path.getsize(file_path)
        except (OSError, IOError):
            pass
        return None

    def _get_last_modified(self, file_path: str) -> Optional[datetime]:
        """Get file last modified timestamp."""
        try:
            if os.path.exists(file_path):
                timestamp = os.path.getmtime(file_path)
                return datetime.fromtimestamp(timestamp)
        except (OSError, IOError):
            pass
        return None

    def to_dict(self) -> Dict:
        """Convert file node to dictionary representation."""
        base_dict = super().to_dict()
        base_dict.update({
            'file_path': self.file_path,
            'file_format': self.file_format,
            'file_size': self.file_size,
            'last_modified': self.last_modified.isoformat() if self.last_modified else None
        })
        return base_dict


class DatabaseNode(DataNode):
    """
    Data node representing a database table or query result.

    This includes tables from PostgreSQL, MySQL, SQLite, etc.
    """

    def __init__(self, table_name: str, metadata: Optional[Dict] = None):
        """
        Initialize a database node.

        Args:
            table_name: Name of the database table
            metadata: Additional metadata about the table
        """
        super().__init__(table_name, metadata)
        self.node_type = "database"
        self.table_name = table_name

        # Database-specific metadata
        self.database_type = metadata.get(
            'database_type', 'unknown') if metadata else 'unknown'
        self.connection_string = metadata.get(
            'connection_string', '') if metadata else ''
        self.schema_name = metadata.get(
            'schema_name', 'public') if metadata else 'public'
        self.row_count = metadata.get('row_count') if metadata else None

        # Update metadata with database information
        self.metadata.update({
            'database_type': self.database_type,
            'schema_name': self.schema_name,
            'row_count': self.row_count
        })

    def set_row_count(self, count: int):
        """Set the row count for this table."""
        self.row_count = count
        self.metadata['row_count'] = count

    def to_dict(self) -> Dict:
        """Convert database node to dictionary representation."""
        base_dict = super().to_dict()
        base_dict.update({
            'table_name': self.table_name,
            'database_type': self.database_type,
            'schema_name': self.schema_name,
            'row_count': self.row_count
        })
        return base_dict


class CloudNode(DataNode):
    """
    Data node representing cloud storage objects (S3, Azure Blob, GCS).
    """

    def __init__(self, object_path: str, metadata: Optional[Dict] = None):
        """
        Initialize a cloud node.

        Args:
            object_path: Cloud object path (e.g., s3://bucket/key)
            metadata: Additional metadata about the object
        """
        super().__init__(object_path, metadata)
        self.node_type = "cloud"
        self.object_path = object_path

        # Parse cloud path
        self.cloud_provider = self._detect_cloud_provider(object_path)
        self.bucket_name = self._extract_bucket_name(object_path)
        self.object_key = self._extract_object_key(object_path)

        # Update metadata
        self.metadata.update({
            'cloud_provider': self.cloud_provider,
            'bucket_name': self.bucket_name,
            'object_key': self.object_key
        })

    def _detect_cloud_provider(self, path: str) -> str:
        """Detect cloud provider from path."""
        if path.startswith('s3://'):
            return 'aws'
        elif path.startswith('gs://'):
            return 'gcp'
        elif path.startswith('abfs://') or path.startswith('azure://'):
            return 'azure'
        return 'unknown'

    def _extract_bucket_name(self, path: str) -> str:
        """Extract bucket/container name from path."""
        try:
            if '://' in path:
                path_part = path.split('://', 1)[1]
                return path_part.split('/')[0]
        except (IndexError, ValueError):
            pass
        return ''

    def _extract_object_key(self, path: str) -> str:
        """Extract object key from path."""
        try:
            if '://' in path:
                path_part = path.split('://', 1)[1]
                parts = path_part.split('/', 1)
                return parts[1] if len(parts) > 1 else ''
        except (IndexError, ValueError):
            pass
        return ''

    def to_dict(self) -> Dict:
        """Convert cloud node to dictionary representation."""
        base_dict = super().to_dict()
        base_dict.update({
            'object_path': self.object_path,
            'cloud_provider': self.cloud_provider,
            'bucket_name': self.bucket_name,
            'object_key': self.object_key
        })
        return base_dict
