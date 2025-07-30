"""
Database connectors for DataLineagePy.

This module provides database connectivity with automatic lineage tracking
for various database systems including PostgreSQL, MySQL, SQLite, and cloud databases.
"""

from .base import BaseConnector, ConnectionManager
from .sql_parser import SQLLineageParser

# Database-specific connectors (will be implemented progressively)
try:
    from .postgresql import PostgreSQLConnector
except ImportError:
    PostgreSQLConnector = None

try:
    from .mysql import MySQLConnector
except ImportError:
    MySQLConnector = None

try:
    from .sqlite import SQLiteConnector
except ImportError:
    SQLiteConnector = None

try:
    from .sqlserver import SQLServerConnector
except ImportError:
    SQLServerConnector = None

# File-based connectors
try:
    from .file_base import FileConnector
except ImportError:
    FileConnector = None

try:
    from .parquet import ParquetConnector
except ImportError:
    ParquetConnector = None

try:
    from .csv import CSVConnector
except ImportError:
    CSVConnector = None

try:
    from .json import JSONConnector
except ImportError:
    JSONConnector = None

# Cloud storage connectors
try:
    from .cloud_base import CloudStorageConnector
except ImportError:
    CloudStorageConnector = None

try:
    from .s3 import S3Connector
except ImportError:
    S3Connector = None

# Streaming connectors
try:
    from .streaming_base import StreamingConnector
except ImportError:
    StreamingConnector = None

try:
    from .kafka import KafkaConnector
except ImportError:
    KafkaConnector = None

# Google Cloud Platform connectors
try:
    from .gcs import GCSConnector
except ImportError:
    GCSConnector = None

# Microsoft Azure connectors
try:
    from .azure_blob import AzureBlobConnector
except ImportError:
    AzureBlobConnector = None

# Data Lake format connectors
try:
    from .delta_lake import DeltaLakeConnector
except ImportError:
    DeltaLakeConnector = None

try:
    from .iceberg import IcebergConnector
except ImportError:
    IcebergConnector = None

__all__ = [
    'BaseConnector',
    'ConnectionManager',
    'SQLLineageParser',
    'PostgreSQLConnector',
    'MySQLConnector',
    'SQLiteConnector',
    'SQLServerConnector',
    'FileConnector',
    'ParquetConnector',
    'CSVConnector',
    'JSONConnector',
    'CloudStorageConnector',
    'S3Connector',
    'StreamingConnector',
    'KafkaConnector',
    'GCSConnector',
    'AzureBlobConnector',
    'DeltaLakeConnector',
    'IcebergConnector',
]
