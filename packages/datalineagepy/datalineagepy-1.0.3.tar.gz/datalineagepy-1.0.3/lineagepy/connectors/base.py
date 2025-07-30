"""
Base classes for database connectors with lineage tracking.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from contextlib import contextmanager
from threading import Lock
import pandas as pd

from ..core.dataframe_wrapper import LineageDataFrame
from ..core.tracker import LineageTracker
from ..core.nodes import TableNode
from ..core.edges import LineageEdge, TransformationType

logger = logging.getLogger(__name__)


class BaseConnector(ABC):
    """
    Abstract base class for all database connectors.

    Provides the interface for database connectivity with automatic lineage tracking.
    All database-specific connectors should inherit from this class.
    """

    def __init__(self, connection_string: str, **kwargs):
        """
        Initialize the connector.

        Args:
            connection_string: Database connection string
            **kwargs: Additional connector-specific options
        """
        self.connection_string = connection_string
        self.connection = None
        self.tracker = LineageTracker.get_global_instance()
        self.options = kwargs
        self._lock = Lock()

    @abstractmethod
    def connect(self) -> None:
        """Establish database connection."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close database connection."""
        pass

    @abstractmethod
    def read_table(self, table_name: str, schema: Optional[str] = None,
                   **kwargs) -> LineageDataFrame:
        """
        Read table with lineage tracking.

        Args:
            table_name: Name of the table to read
            schema: Optional schema name
            **kwargs: Additional read options

        Returns:
            LineageDataFrame with tracked lineage
        """
        pass

    @abstractmethod
    def execute_query(self, query: str, **kwargs) -> LineageDataFrame:
        """
        Execute query with lineage tracking.

        Args:
            query: SQL query to execute
            **kwargs: Additional execution options

        Returns:
            LineageDataFrame with query results and lineage
        """
        pass

    @abstractmethod
    def get_schema(self, table_name: str, schema: Optional[str] = None) -> Dict[str, str]:
        """
        Get table schema information.

        Args:
            table_name: Name of the table
            schema: Optional schema name

        Returns:
            Dictionary mapping column names to data types
        """
        pass

    @abstractmethod
    def list_tables(self, schema: Optional[str] = None) -> List[str]:
        """
        List all tables in the database or schema.

        Args:
            schema: Optional schema name

        Returns:
            List of table names
        """
        pass

    def write_table(self, df: Union[pd.DataFrame, LineageDataFrame],
                    table_name: str, schema: Optional[str] = None,
                    if_exists: str = 'fail', **kwargs) -> None:
        """
        Write DataFrame to database table with lineage tracking.

        Args:
            df: DataFrame to write
            table_name: Target table name
            schema: Optional schema name
            if_exists: How to behave if table exists ('fail', 'replace', 'append')
            **kwargs: Additional write options
        """
        # Convert to pandas DataFrame if needed
        pandas_df = df._df if isinstance(df, LineageDataFrame) else df

        # Perform the write operation (implemented by subclasses)
        self._write_dataframe(pandas_df, table_name,
                              schema, if_exists, **kwargs)

        # Track lineage if input was a LineageDataFrame
        if isinstance(df, LineageDataFrame):
            self._track_write_operation(df, table_name, schema)

    @abstractmethod
    def _write_dataframe(self, df: pd.DataFrame, table_name: str,
                         schema: Optional[str], if_exists: str, **kwargs) -> None:
        """Internal method to write DataFrame to database."""
        pass

    def _track_write_operation(self, source_df: LineageDataFrame,
                               table_name: str, schema: Optional[str]) -> None:
        """Track lineage for write operations."""
        try:
            # Create target table node
            full_table_name = f"{schema}.{table_name}" if schema else table_name
            target_node = TableNode(
                id=f"db_table_{full_table_name}",
                name=full_table_name,
                columns=set(source_df.columns),
                source_type=self.__class__.__name__.lower().replace('connector', ''),
                source_location=f"{self.connection_string}/{full_table_name}"
            )

            self.tracker.add_node(target_node)

            # Create lineage edge
            edge = LineageEdge(
                source_node_ids=[source_df._lineage_node_id],
                target_node_id=target_node.id,
                transformation_type=TransformationType.CUSTOM,
                operation_name="database_write",
                parameters={'table_name': table_name, 'schema': schema},
                input_columns=set(source_df.columns),
                output_columns=set(source_df.columns)
            )

            # Add column mappings (1:1 for write operations)
            for col in source_df.columns:
                edge.add_column_mapping(col, {col})

            self.tracker.add_edge(edge)

        except Exception as e:
            logger.error(f"Failed to track write operation: {str(e)}")

    def _create_lineage_dataframe(self, df: pd.DataFrame, table_name: str,
                                  schema: Optional[str] = None) -> LineageDataFrame:
        """
        Create a LineageDataFrame from a pandas DataFrame with database source tracking.

        Args:
            df: Pandas DataFrame
            table_name: Source table name
            schema: Optional schema name

        Returns:
            LineageDataFrame with database source tracking
        """
        full_table_name = f"{schema}.{table_name}" if schema else table_name

        return LineageDataFrame(
            df,
            name=full_table_name,
            source_type=self.__class__.__name__.lower().replace('connector', ''),
            source_location=f"{self.connection_string}/{full_table_name}"
        )

    @contextmanager
    def transaction(self):
        """Context manager for database transactions."""
        if not self.connection:
            self.connect()

        try:
            # Start transaction (implementation depends on database)
            yield self.connection
            # Commit transaction
            self.connection.commit()
        except Exception as e:
            # Rollback on error
            self.connection.rollback()
            raise e

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


class ConnectionManager:
    """
    Manages database connections with pooling and caching.
    """

    def __init__(self, max_connections: int = 10):
        """
        Initialize connection manager.

        Args:
            max_connections: Maximum number of concurrent connections
        """
        self.max_connections = max_connections
        self._connections = {}
        self._lock = Lock()

    def get_connector(self, connector_class, connection_string: str,
                      **kwargs) -> BaseConnector:
        """
        Get or create a database connector.

        Args:
            connector_class: Connector class to instantiate
            connection_string: Database connection string
            **kwargs: Additional connector options

        Returns:
            Database connector instance
        """
        with self._lock:
            key = f"{connector_class.__name__}:{connection_string}"

            if key not in self._connections:
                if len(self._connections) >= self.max_connections:
                    # Remove oldest connection
                    oldest_key = next(iter(self._connections))
                    self._connections[oldest_key].disconnect()
                    del self._connections[oldest_key]

                # Create new connector
                connector = connector_class(connection_string, **kwargs)
                self._connections[key] = connector

            return self._connections[key]

    def close_all(self):
        """Close all managed connections."""
        with self._lock:
            for connector in self._connections.values():
                try:
                    connector.disconnect()
                except Exception as e:
                    logger.error(f"Error closing connection: {str(e)}")

            self._connections.clear()

    def __del__(self):
        """Cleanup on destruction."""
        self.close_all()


# Global connection manager instance
connection_manager = ConnectionManager()
