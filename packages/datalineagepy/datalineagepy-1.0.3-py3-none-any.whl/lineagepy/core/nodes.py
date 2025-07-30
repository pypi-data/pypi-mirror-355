"""
Node classes for representing data entities in the lineage graph.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Set, List
from dataclasses import dataclass, field


@dataclass
class LineageNode:
    """Base class for all lineage nodes."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Post-initialization processing."""
        if not self.name:
            self.name = f"node_{self.id[:8]}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.__class__.__name__,
            'created_at': self.created_at.isoformat(),
            'metadata': self.metadata
        }

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id[:8]}, name={self.name})"

    def __repr__(self) -> str:
        return self.__str__()


@dataclass
class TableNode(LineageNode):
    """Represents a table/DataFrame in the lineage graph."""

    columns: Set[str] = field(default_factory=set)
    shape: Optional[tuple] = None
    source_type: str = "unknown"  # csv, sql, parquet, etc.
    source_location: Optional[str] = None

    def add_column(self, column_name: str) -> None:
        """Add a column to this table."""
        self.columns.add(column_name)

    def remove_column(self, column_name: str) -> None:
        """Remove a column from this table."""
        self.columns.discard(column_name)

    def has_column(self, column_name: str) -> bool:
        """Check if table has a specific column."""
        return column_name in self.columns

    def to_dict(self) -> Dict[str, Any]:
        """Convert table node to dictionary representation."""
        base_dict = super().to_dict()
        base_dict.update({
            'columns': list(self.columns),
            'shape': self.shape,
            'source_type': self.source_type,
            'source_location': self.source_location
        })
        return base_dict


@dataclass
class ColumnNode(LineageNode):
    """Represents a column in the lineage graph."""

    table_id: str = ""
    data_type: Optional[str] = None
    nullable: Optional[bool] = None
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert column node to dictionary representation."""
        base_dict = super().to_dict()
        base_dict.update({
            'table_id': self.table_id,
            'data_type': self.data_type,
            'nullable': self.nullable,
            'description': self.description
        })
        return base_dict

    @property
    def full_name(self) -> str:
        """Get the full name including table reference."""
        return f"{self.table_id}.{self.name}" if self.table_id else self.name


@dataclass
class FileNode(LineageNode):
    """Represents a file in the lineage graph."""

    file_path: str = ""
    file_type: str = "unknown"  # csv, parquet, json, xlsx, etc.
    size_bytes: int = 0
    columns: Set[str] = field(default_factory=set)
    encoding: Optional[str] = None
    compression: Optional[str] = None
    schema_version: Optional[str] = None

    def add_column(self, column_name: str) -> None:
        """Add a column to this file."""
        self.columns.add(column_name)

    def remove_column(self, column_name: str) -> None:
        """Remove a column from this file."""
        self.columns.discard(column_name)

    def has_column(self, column_name: str) -> bool:
        """Check if file has a specific column."""
        return column_name in self.columns

    @property
    def size_mb(self) -> float:
        """Get file size in megabytes."""
        return round(self.size_bytes / (1024 * 1024), 2)

    @property
    def size_readable(self) -> str:
        """Get human-readable file size."""
        if self.size_bytes < 1024:
            return f"{self.size_bytes} B"
        elif self.size_bytes < 1024 * 1024:
            return f"{round(self.size_bytes / 1024, 1)} KB"
        elif self.size_bytes < 1024 * 1024 * 1024:
            return f"{round(self.size_bytes / (1024 * 1024), 1)} MB"
        else:
            return f"{round(self.size_bytes / (1024 * 1024 * 1024), 1)} GB"

    def to_dict(self) -> Dict[str, Any]:
        """Convert file node to dictionary representation."""
        base_dict = super().to_dict()
        base_dict.update({
            'file_path': self.file_path,
            'file_type': self.file_type,
            'size_bytes': self.size_bytes,
            'size_mb': self.size_mb,
            'size_readable': self.size_readable,
            'columns': list(self.columns),
            'encoding': self.encoding,
            'compression': self.compression,
            'schema_version': self.schema_version
        })
        return base_dict

    def __str__(self) -> str:
        return f"FileNode(id={self.id[:8]}, name={self.name}, type={self.file_type}, size={self.size_readable})"


@dataclass
class APINode(LineageNode):
    """Represents an API endpoint in the lineage graph."""

    endpoint_url: str = ""
    method: str = "GET"  # GET, POST, PUT, DELETE, etc.
    response_format: str = "json"  # json, xml, csv, etc.
    api_version: Optional[str] = None
    authentication_type: Optional[str] = None
    rate_limit: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert API node to dictionary representation."""
        base_dict = super().to_dict()
        base_dict.update({
            'endpoint_url': self.endpoint_url,
            'method': self.method,
            'response_format': self.response_format,
            'api_version': self.api_version,
            'authentication_type': self.authentication_type,
            'rate_limit': self.rate_limit
        })
        return base_dict

    def __str__(self) -> str:
        return f"APINode(id={self.id[:8]}, name={self.name}, method={self.method}, url={self.endpoint_url})"


@dataclass
class CloudNode(LineageNode):
    """Represents a cloud storage object in the lineage graph."""

    object_key: str = ""
    bucket_name: str = ""
    cloud_provider: str = ""  # aws, gcp, azure, minio, etc.
    size_bytes: int = 0
    columns: Set[str] = field(default_factory=set)
    content_type: Optional[str] = None
    etag: Optional[str] = None
    last_modified: Optional[datetime] = None
    storage_class: Optional[str] = None
    region: Optional[str] = None

    def add_column(self, column_name: str) -> None:
        """Add a column to this cloud object."""
        self.columns.add(column_name)

    def remove_column(self, column_name: str) -> None:
        """Remove a column from this cloud object."""
        self.columns.discard(column_name)

    def has_column(self, column_name: str) -> bool:
        """Check if cloud object has a specific column."""
        return column_name in self.columns

    @property
    def size_mb(self) -> float:
        """Get object size in megabytes."""
        return round(self.size_bytes / (1024 * 1024), 2)

    @property
    def size_readable(self) -> str:
        """Get human-readable object size."""
        if self.size_bytes < 1024:
            return f"{self.size_bytes} B"
        elif self.size_bytes < 1024 * 1024:
            return f"{round(self.size_bytes / 1024, 1)} KB"
        elif self.size_bytes < 1024 * 1024 * 1024:
            return f"{round(self.size_bytes / (1024 * 1024), 1)} MB"
        else:
            return f"{round(self.size_bytes / (1024 * 1024 * 1024), 1)} GB"

    @property
    def cloud_url(self) -> str:
        """Get the cloud URL for this object."""
        if self.cloud_provider == 'aws':
            return f"s3://{self.bucket_name}/{self.object_key}"
        elif self.cloud_provider == 'gcp':
            return f"gs://{self.bucket_name}/{self.object_key}"
        elif self.cloud_provider == 'azure':
            return f"https://{self.bucket_name}.blob.core.windows.net/{self.object_key}"
        else:
            return f"{self.cloud_provider}://{self.bucket_name}/{self.object_key}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert cloud node to dictionary representation."""
        base_dict = super().to_dict()
        base_dict.update({
            'object_key': self.object_key,
            'bucket_name': self.bucket_name,
            'cloud_provider': self.cloud_provider,
            'size_bytes': self.size_bytes,
            'size_mb': self.size_mb,
            'size_readable': self.size_readable,
            'cloud_url': self.cloud_url,
            'columns': list(self.columns),
            'content_type': self.content_type,
            'etag': self.etag,
            'last_modified': self.last_modified.isoformat() if self.last_modified else None,
            'storage_class': self.storage_class,
            'region': self.region
        })
        return base_dict

    def __str__(self) -> str:
        return f"CloudNode(id={self.id[:8]}, name={self.name}, provider={self.cloud_provider}, url={self.cloud_url}, size={self.size_readable})"


@dataclass
class StreamNode(LineageNode):
    """Represents a streaming data source/sink in the lineage graph."""

    stream_name: str = ""
    platform: str = ""  # kafka, kinesis, pulsar, pubsub, etc.
    topic_partition: Optional[str] = None
    consumer_group: Optional[str] = None
    schema_registry: Optional[str] = None
    message_format: str = "json"  # json, avro, protobuf, etc.
    throughput_msgs_per_sec: Optional[float] = None
    retention_hours: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert stream node to dictionary representation."""
        base_dict = super().to_dict()
        base_dict.update({
            'stream_name': self.stream_name,
            'platform': self.platform,
            'topic_partition': self.topic_partition,
            'consumer_group': self.consumer_group,
            'schema_registry': self.schema_registry,
            'message_format': self.message_format,
            'throughput_msgs_per_sec': self.throughput_msgs_per_sec,
            'retention_hours': self.retention_hours
        })
        return base_dict

    def __str__(self) -> str:
        return f"StreamNode(id={self.id[:8]}, name={self.name}, platform={self.platform}, stream={self.stream_name})"
