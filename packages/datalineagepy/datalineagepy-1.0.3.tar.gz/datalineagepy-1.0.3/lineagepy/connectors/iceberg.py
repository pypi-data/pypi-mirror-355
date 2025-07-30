"""
Apache Iceberg connector for schema evolution, snapshot isolation, and metadata tracking.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
import pandas as pd

try:
    from pyiceberg.catalog import load_catalog
    from pyiceberg.exceptions import NoSuchTableError, NoSuchNamespaceError
    from pyiceberg.table import Table
    from pyiceberg.expressions import GreaterThanOrEqual, LessThan, EqualTo
    ICEBERG_AVAILABLE = True
except ImportError:
    ICEBERG_AVAILABLE = False

from ..core.dataframe_wrapper import LineageDataFrame
from .cloud_base import CloudStorageConnector

try:
    from pyiceberg.table import Table
except ImportError:
    Table = None

logger = logging.getLogger(__name__)


class IcebergConnector(CloudStorageConnector):
    """
    Apache Iceberg connector with comprehensive table format operations.

    Features:
    - Schema evolution with backward/forward compatibility
    - Snapshot isolation for concurrent operations
    - Partition evolution and time travel
    - Metadata table access for debugging
    - Branch and tag support for Git-like versioning
    - ACID guarantees with optimistic concurrency
    """

    def __init__(self,
                 catalog_uri: str,
                 warehouse: str = None,
                 catalog_properties: Dict[str, str] = None,
                 **kwargs):
        """
        Initialize Iceberg connector.

        Args:
            catalog_uri: Iceberg catalog URI (e.g., 'thrift://localhost:9083')
            warehouse: Warehouse location for tables
            catalog_properties: Additional catalog configuration
            **kwargs: Additional connector options
        """
        if not ICEBERG_AVAILABLE:
            raise ImportError(
                "pyiceberg is required for Iceberg connector. "
                "Install with: pip install pyiceberg"
            )

        super().__init__(None, None, None, **kwargs)

        self.catalog_uri = catalog_uri
        self.warehouse = warehouse
        self.catalog_properties = catalog_properties or {}
        self.catalog = None

        # Iceberg-specific configuration
        self.default_format_version = kwargs.get('format_version', 2)
        self.snapshot_timeout_ms = kwargs.get(
            'snapshot_timeout_ms', 300000)  # 5 minutes

    def connect(self) -> None:
        """Establish connection to Iceberg catalog."""
        try:
            # Set up catalog properties
            properties = {
                'uri': self.catalog_uri,
                **self.catalog_properties
            }

            if self.warehouse:
                properties['warehouse'] = self.warehouse

            # Load catalog
            self.catalog = load_catalog(properties)
            self.connection = True

            logger.info(f"Connected to Iceberg catalog: {self.catalog_uri}")

        except Exception as e:
            raise ConnectionError(
                f"Failed to connect to Iceberg catalog: {str(e)}")

    def create_namespace(self, namespace: str,
                         properties: Dict[str, str] = None) -> bool:
        """Create Iceberg namespace."""
        if not self.connection:
            self.connect()

        try:
            self.catalog.create_namespace(namespace, properties or {})
            logger.info(f"Created Iceberg namespace: {namespace}")
            return True

        except Exception as e:
            logger.error(f"Failed to create namespace: {str(e)}")
            raise

    def create_table(self, identifier: str, schema: Any,
                     location: str = None,
                     partition_spec: List[str] = None,
                     sort_order: List[str] = None,
                     properties: Dict[str, str] = None) -> bool:
        """
        Create new Iceberg table.

        Args:
            identifier: Table identifier (e.g., 'namespace.table_name')
            schema: PyArrow schema or Iceberg schema
            location: Table location (optional)
            partition_spec: Partition specification
            sort_order: Sort order specification
            properties: Table properties

        Returns:
            True if successful
        """
        if not self.connection:
            self.connect()

        try:
            # Create table
            table = self.catalog.create_table(
                identifier=identifier,
                schema=schema,
                location=location,
                partition_spec=partition_spec,
                sort_order=sort_order,
                properties=properties or {}
            )

            # Track table creation
            if self.tracker:
                self._track_iceberg_operation("create_table", {
                    'identifier': identifier,
                    'location': location,
                    'partition_spec': partition_spec,
                    'sort_order': sort_order
                })

            logger.info(f"Created Iceberg table: {identifier}")
            return True

        except Exception as e:
            logger.error(f"Failed to create table: {str(e)}")
            raise

    def read_table(self, identifier: str,
                   snapshot_id: Optional[int] = None,
                   branch: Optional[str] = None,
                   tag: Optional[str] = None,
                   timestamp: Optional[datetime] = None,
                   selected_fields: List[str] = None,
                   row_filter: Any = None,
                   limit: Optional[int] = None) -> LineageDataFrame:
        """
        Read Iceberg table with advanced filtering and time travel.

        Args:
            identifier: Table identifier
            snapshot_id: Specific snapshot to read
            branch: Branch to read from
            tag: Tag to read from
            timestamp: Timestamp for time travel
            selected_fields: Columns to select
            row_filter: Row-level filters
            limit: Maximum rows to return

        Returns:
            LineageDataFrame with tracked lineage
        """
        if not self.connection:
            self.connect()

        try:
            # Load table
            table = self.catalog.load_table(identifier)

            # Apply time travel
            if snapshot_id:
                table = table.snapshot_as_of_snapshot_id(snapshot_id)
            elif branch:
                table = table.snapshot_as_of_branch(branch)
            elif tag:
                table = table.snapshot_as_of_tag(tag)
            elif timestamp:
                table = table.snapshot_as_of_timestamp(timestamp)

            # Build scan
            scan = table.scan()

            # Apply filters and selections
            if selected_fields:
                scan = scan.select(*selected_fields)

            if row_filter:
                scan = scan.filter(row_filter)

            if limit:
                scan = scan.limit(limit)

            # Convert to DataFrame
            arrow_table = scan.to_arrow()
            df = arrow_table.to_pandas()

            # Create lineage DataFrame
            lineage_df = self._create_iceberg_lineage_dataframe(
                df, table, "iceberg_read"
            )

            logger.info(
                f"Read Iceberg table {identifier}: {df.shape[0]} rows, {df.shape[1]} columns")
            return lineage_df

        except NoSuchTableError:
            raise FileNotFoundError(f"Iceberg table not found: {identifier}")
        except Exception as e:
            logger.error(f"Failed to read Iceberg table: {str(e)}")
            raise

    def write_table(self, identifier: str, df: pd.DataFrame,
                    mode: str = "append",
                    overwrite_filter: Any = None) -> bool:
        """
        Write DataFrame to Iceberg table.

        Args:
            identifier: Table identifier
            df: DataFrame to write
            mode: Write mode (append, overwrite)
            overwrite_filter: Filter for conditional overwrite

        Returns:
            True if successful
        """
        if not self.connection:
            self.connect()

        try:
            # Load table
            table = self.catalog.load_table(identifier)

            # Convert DataFrame to PyArrow
            arrow_table = pa.Table.from_pandas(df)

            # Write data
            if mode == "append":
                table.append(arrow_table)
            elif mode == "overwrite":
                if overwrite_filter:
                    table.overwrite(arrow_table, overwrite_filter)
                else:
                    table.overwrite(arrow_table)
            else:
                raise ValueError(f"Unsupported write mode: {mode}")

            # Track write operation
            if self.tracker:
                self._track_iceberg_operation("write", {
                    'identifier': identifier,
                    'mode': mode,
                    'rows_written': len(df),
                    'columns_written': len(df.columns),
                    'has_overwrite_filter': overwrite_filter is not None
                })

            logger.info(f"Wrote {len(df)} rows to Iceberg table {identifier}")
            return True

        except Exception as e:
            logger.error(f"Failed to write to Iceberg table: {str(e)}")
            raise

    def evolve_schema(self, identifier: str,
                      add_columns: List[tuple] = None,
                      rename_columns: Dict[str, str] = None,
                      drop_columns: List[str] = None,
                      update_columns: Dict[str, Any] = None) -> bool:
        """
        Evolve table schema with backward compatibility.

        Args:
            identifier: Table identifier
            add_columns: List of (column_name, data_type) tuples to add
            rename_columns: Dict of old_name -> new_name mappings
            drop_columns: List of column names to drop
            update_columns: Dict of column updates

        Returns:
            True if successful
        """
        if not self.connection:
            self.connect()

        try:
            # Load table
            table = self.catalog.load_table(identifier)

            # Start schema evolution transaction
            with table.update_schema() as update:
                # Add columns
                if add_columns:
                    for col_name, col_type in add_columns:
                        update.add_column(col_name, col_type)

                # Rename columns
                if rename_columns:
                    for old_name, new_name in rename_columns.items():
                        update.rename_column(old_name, new_name)

                # Drop columns
                if drop_columns:
                    for col_name in drop_columns:
                        update.delete_column(col_name)

                # Update columns (type changes, etc.)
                if update_columns:
                    for col_name, new_type in update_columns.items():
                        update.update_column(col_name, field_type=new_type)

            # Track schema evolution
            if self.tracker:
                self._track_iceberg_operation("schema_evolution", {
                    'identifier': identifier,
                    'add_columns': add_columns,
                    'rename_columns': rename_columns,
                    'drop_columns': drop_columns,
                    'update_columns': update_columns
                })

            logger.info(f"Evolved schema for Iceberg table {identifier}")
            return True

        except Exception as e:
            logger.error(f"Failed to evolve schema: {str(e)}")
            raise

    def evolve_partition(self, identifier: str,
                         add_partitions: List[str] = None,
                         drop_partitions: List[str] = None) -> bool:
        """
        Evolve table partition specification.

        Args:
            identifier: Table identifier
            add_partitions: List of partition transforms to add
            drop_partitions: List of partition names to drop

        Returns:
            True if successful
        """
        if not self.connection:
            self.connect()

        try:
            # Load table
            table = self.catalog.load_table(identifier)

            # Update partition spec
            with table.update_spec() as update:
                if add_partitions:
                    for partition in add_partitions:
                        update.add_field(partition)

                if drop_partitions:
                    for partition in drop_partitions:
                        update.remove_field(partition)

            # Track partition evolution
            if self.tracker:
                self._track_iceberg_operation("partition_evolution", {
                    'identifier': identifier,
                    'add_partitions': add_partitions,
                    'drop_partitions': drop_partitions
                })

            logger.info(f"Evolved partitions for Iceberg table {identifier}")
            return True

        except Exception as e:
            logger.error(f"Failed to evolve partitions: {str(e)}")
            raise

    def create_branch(self, identifier: str, branch_name: str,
                      snapshot_id: Optional[int] = None) -> bool:
        """Create branch from current or specified snapshot."""
        if not self.connection:
            self.connect()

        try:
            table = self.catalog.load_table(identifier)

            if snapshot_id:
                table.manage_snapshots().create_branch(branch_name, snapshot_id)
            else:
                table.manage_snapshots().create_branch(branch_name)

            # Track branch creation
            if self.tracker:
                self._track_iceberg_operation("create_branch", {
                    'identifier': identifier,
                    'branch_name': branch_name,
                    'snapshot_id': snapshot_id
                })

            logger.info(f"Created branch {branch_name} for table {identifier}")
            return True

        except Exception as e:
            logger.error(f"Failed to create branch: {str(e)}")
            raise

    def create_tag(self, identifier: str, tag_name: str,
                   snapshot_id: Optional[int] = None) -> bool:
        """Create tag from current or specified snapshot."""
        if not self.connection:
            self.connect()

        try:
            table = self.catalog.load_table(identifier)

            if snapshot_id:
                table.manage_snapshots().create_tag(tag_name, snapshot_id)
            else:
                table.manage_snapshots().create_tag(tag_name)

            # Track tag creation
            if self.tracker:
                self._track_iceberg_operation("create_tag", {
                    'identifier': identifier,
                    'tag_name': tag_name,
                    'snapshot_id': snapshot_id
                })

            logger.info(f"Created tag {tag_name} for table {identifier}")
            return True

        except Exception as e:
            logger.error(f"Failed to create tag: {str(e)}")
            raise

    def get_snapshots(self, identifier: str) -> List[Dict[str, Any]]:
        """Get all snapshots for table."""
        if not self.connection:
            self.connect()

        try:
            table = self.catalog.load_table(identifier)
            snapshots = []

            for snapshot in table.snapshots():
                snapshots.append({
                    'snapshot_id': snapshot.snapshot_id,
                    'timestamp': snapshot.timestamp_ms,
                    'operation': snapshot.summary.get('operation'),
                    'summary': dict(snapshot.summary)
                })

            return snapshots

        except Exception as e:
            logger.error(f"Failed to get snapshots: {str(e)}")
            raise

    def get_metadata_tables(self, identifier: str) -> Dict[str, LineageDataFrame]:
        """
        Get Iceberg metadata tables for debugging and analysis.

        Args:
            identifier: Table identifier

        Returns:
            Dict of metadata table name -> DataFrame
        """
        if not self.connection:
            self.connect()

        try:
            table = self.catalog.load_table(identifier)
            metadata_tables = {}

            # Available metadata tables
            metadata_types = [
                'snapshots', 'manifests', 'data_files',
                'delete_files', 'partitions', 'files'
            ]

            for metadata_type in metadata_types:
                try:
                    # This would require specific pyiceberg API support
                    # For now, we'll create placeholder
                    metadata_tables[metadata_type] = self._get_metadata_table(
                        table, metadata_type
                    )
                except:
                    # Skip if metadata table not available
                    pass

            return metadata_tables

        except Exception as e:
            logger.error(f"Failed to get metadata tables: {str(e)}")
            raise

    def _get_metadata_table(self, table: 'Table', metadata_type: str) -> LineageDataFrame:
        """Get specific metadata table."""
        # This is a placeholder - would need specific pyiceberg implementation
        import pandas as pd

        if metadata_type == 'snapshots':
            data = []
            for snapshot in table.snapshots():
                data.append({
                    'snapshot_id': snapshot.snapshot_id,
                    'timestamp': snapshot.timestamp_ms,
                    'operation': snapshot.summary.get('operation', 'unknown'),
                    'data_files_count': snapshot.summary.get('added-data-files', 0),
                    'records_count': snapshot.summary.get('added-records', 0)
                })
            df = pd.DataFrame(data)
        else:
            # Placeholder for other metadata tables
            df = pd.DataFrame({'placeholder': ['not_implemented']})

        return LineageDataFrame(df, tracker=self.tracker)

    def get_table_info(self, identifier: str) -> Dict[str, Any]:
        """Get comprehensive table information."""
        if not self.connection:
            self.connect()

        try:
            table = self.catalog.load_table(identifier)

            return {
                'identifier': identifier,
                'location': table.location(),
                'current_snapshot_id': table.current_snapshot().snapshot_id if table.current_snapshot() else None,
                'schema': str(table.schema()),
                'partition_spec': str(table.spec()),
                'sort_order': str(table.sort_order()),
                'properties': dict(table.properties()),
                'snapshots_count': len(table.snapshots()),
                'format_version': table.metadata.format_version
            }

        except Exception as e:
            logger.error(f"Failed to get table info: {str(e)}")
            raise

    def _create_iceberg_lineage_dataframe(self, df: pd.DataFrame, table: Table,
                                          operation_name: str) -> LineageDataFrame:
        """Create LineageDataFrame with Iceberg table lineage."""
        lineage_df = LineageDataFrame(df, tracker=self.tracker)

        if self.tracker:
            from ..core.nodes import CloudNode

            snapshot_id = table.current_snapshot().snapshot_id if table.current_snapshot() else 0

            # Create Iceberg table node
            table_node = CloudNode(
                node_id=f"iceberg_{hash(table.identifier)}_{snapshot_id}",
                name=f"Iceberg Table: {table.identifier} (snapshot: {snapshot_id})",
                bucket_name="iceberg",
                object_key=str(table.identifier),
                cloud_provider="iceberg",
                metadata={
                    'snapshot_id': snapshot_id,
                    'table_location': table.location(),
                    'operation': operation_name
                }
            )

            self.tracker.add_node(table_node)
            lineage_df._add_source_node(table_node)

        return lineage_df

    def _track_iceberg_operation(self, operation: str, context: Dict[str, Any]) -> None:
        """Track Iceberg operation in lineage."""
        if self.tracker:
            self.tracker.add_operation_context(
                operation_name=f"iceberg_{operation}",
                context={
                    'catalog_uri': self.catalog_uri,
                    'timestamp': datetime.now().isoformat(),
                    **context
                }
            )

    def __str__(self) -> str:
        return f"IcebergConnector(catalog_uri={self.catalog_uri})"

    def __repr__(self) -> str:
        return self.__str__()
