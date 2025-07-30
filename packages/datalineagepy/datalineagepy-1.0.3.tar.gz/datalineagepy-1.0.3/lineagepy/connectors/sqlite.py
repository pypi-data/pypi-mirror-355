"""
SQLite database connector with lineage tracking.
"""

import logging
import sqlite3
from typing import Dict, Any, List, Optional, Union
import pandas as pd
import os

from .base import BaseConnector
from .sql_parser import SQLLineageParser
from ..core.dataframe_wrapper import LineageDataFrame

logger = logging.getLogger(__name__)

try:
    from sqlalchemy import create_engine
    from sqlalchemy.engine import Engine
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    logger.warning(
        "SQLAlchemy not available. Some SQLite features will be limited.")


class SQLiteConnector(BaseConnector):
    """
    SQLite database connector with automatic lineage tracking.

    Supports both native sqlite3 and SQLAlchemy backends.
    """

    def __init__(self, database_path: str, use_sqlalchemy: bool = True, **kwargs):
        """
        Initialize SQLite connector.

        Args:
            database_path: Path to SQLite database file or ':memory:' for in-memory
            use_sqlalchemy: Whether to use SQLAlchemy (recommended) or sqlite3
            **kwargs: Additional connection options
        """
        # Convert database_path to connection string format
        if database_path == ':memory:':
            connection_string = 'sqlite:///:memory:'
        else:
            # Ensure absolute path for SQLite
            abs_path = os.path.abspath(database_path)
            connection_string = f'sqlite:///{abs_path}'

        super().__init__(connection_string, **kwargs)
        self.database_path = database_path
        self.use_sqlalchemy = use_sqlalchemy and SQLALCHEMY_AVAILABLE
        self.sql_parser = SQLLineageParser()
        self.engine: Optional[Engine] = None

    def connect(self) -> None:
        """Establish SQLite connection."""
        try:
            if self.use_sqlalchemy:
                # SQLAlchemy connection
                self.engine = create_engine(
                    self.connection_string, **self.options)
                self.connection = self.engine.connect()
                logger.info(
                    f"Connected to SQLite using SQLAlchemy: {self.database_path}")
            else:
                # Native sqlite3 connection
                if self.database_path == ':memory:':
                    self.connection = sqlite3.connect(
                        ':memory:', **self.options)
                else:
                    # Create directory if it doesn't exist
                    db_dir = os.path.dirname(
                        os.path.abspath(self.database_path))
                    if db_dir and not os.path.exists(db_dir):
                        os.makedirs(db_dir)

                    self.connection = sqlite3.connect(
                        self.database_path, **self.options)

                # Enable row factory for dict-like access
                self.connection.row_factory = sqlite3.Row
                logger.info(
                    f"Connected to SQLite using sqlite3: {self.database_path}")

        except Exception as e:
            logger.error(f"Failed to connect to SQLite: {str(e)}")
            raise

    def disconnect(self) -> None:
        """Close SQLite connection."""
        try:
            if self.connection:
                self.connection.close()
                self.connection = None

            if self.engine:
                self.engine.dispose()
                self.engine = None

            logger.info("Disconnected from SQLite")

        except Exception as e:
            logger.error(f"Error disconnecting from SQLite: {str(e)}")

    def read_table(self, table_name: str, schema: Optional[str] = None,
                   **kwargs) -> LineageDataFrame:
        """
        Read SQLite table with lineage tracking.

        Args:
            table_name: Name of the table to read
            schema: Optional schema (not used in SQLite, kept for consistency)
            **kwargs: Additional pandas.read_sql options

        Returns:
            LineageDataFrame with tracked lineage
        """
        if not self.connection:
            self.connect()

        try:
            # SQLite doesn't use schemas like PostgreSQL/MySQL
            query = f'SELECT * FROM "{table_name}"'

            # Read data using pandas
            if self.use_sqlalchemy:
                df = pd.read_sql(query, self.connection, **kwargs)
            else:
                df = pd.read_sql_query(query, self.connection, **kwargs)

            # Create LineageDataFrame with database source tracking
            lineage_df = self._create_lineage_dataframe(df, table_name, schema)

            logger.info(
                f"Read table {table_name}: {df.shape[0]} rows, {df.shape[1]} columns")
            return lineage_df

        except Exception as e:
            logger.error(f"Failed to read table {table_name}: {str(e)}")
            raise

    def execute_query(self, query: str, **kwargs) -> LineageDataFrame:
        """
        Execute SQLite query with lineage tracking.

        Args:
            query: SQL query to execute
            **kwargs: Additional pandas.read_sql options

        Returns:
            LineageDataFrame with query results and lineage
        """
        if not self.connection:
            self.connect()

        try:
            # Parse query for lineage information
            lineage_info = self.sql_parser.parse_query(query)

            # Execute query
            if self.use_sqlalchemy:
                df = pd.read_sql(query, self.connection, **kwargs)
            else:
                df = pd.read_sql_query(query, self.connection, **kwargs)

            # Create LineageDataFrame
            query_name = f"sqlite_query_{hash(query) % 10000}"
            lineage_df = self._create_lineage_dataframe(df, query_name)

            # Track SQL lineage
            self._track_sql_lineage(lineage_info, lineage_df)

            logger.info(
                f"Executed query: {df.shape[0]} rows, {df.shape[1]} columns")
            return lineage_df

        except Exception as e:
            logger.error(f"Failed to execute query: {str(e)}")
            raise

    def get_schema(self, table_name: str, schema: Optional[str] = None) -> Dict[str, str]:
        """
        Get SQLite table schema information.

        Args:
            table_name: Name of the table
            schema: Optional schema (not used in SQLite)

        Returns:
            Dictionary mapping column names to data types
        """
        if not self.connection:
            self.connect()

        try:
            # Use PRAGMA table_info for SQLite
            query = f'PRAGMA table_info("{table_name}")'

            if self.use_sqlalchemy:
                result = self.connection.execute(query)
                columns = result.fetchall()
            else:
                cursor = self.connection.cursor()
                cursor.execute(query)
                columns = cursor.fetchall()
                cursor.close()

            schema_info = {}
            for col in columns:
                if isinstance(col, sqlite3.Row):
                    col_name = col['name']
                    data_type = col['type']
                else:
                    # SQLAlchemy result
                    col_name = col[1]  # name is at index 1
                    data_type = col[2]  # type is at index 2

                schema_info[col_name] = data_type

            return schema_info

        except Exception as e:
            logger.error(
                f"Failed to get schema for table {table_name}: {str(e)}")
            return {}

    def list_tables(self, schema: Optional[str] = None) -> List[str]:
        """
        List all tables in SQLite database.

        Args:
            schema: Optional schema (not used in SQLite)

        Returns:
            List of table names
        """
        if not self.connection:
            self.connect()

        try:
            # Query sqlite_master table
            query = """
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """

            if self.use_sqlalchemy:
                result = self.connection.execute(query)
                tables = [row[0] for row in result.fetchall()]
            else:
                cursor = self.connection.cursor()
                cursor.execute(query)
                tables = [row[0] for row in cursor.fetchall()]
                cursor.close()

            return tables

        except Exception as e:
            logger.error(f"Failed to list tables: {str(e)}")
            return []

    def _write_dataframe(self, df: pd.DataFrame, table_name: str,
                         schema: Optional[str], if_exists: str, **kwargs) -> None:
        """Write DataFrame to SQLite table."""
        if not self.connection:
            self.connect()

        try:
            # Use pandas to_sql for writing
            if self.use_sqlalchemy:
                df.to_sql(
                    table_name,
                    self.connection,
                    if_exists=if_exists,
                    index=False,
                    **kwargs
                )
            else:
                # For sqlite3, we need to create an engine temporarily
                temp_engine = create_engine(self.connection_string)
                df.to_sql(
                    table_name,
                    temp_engine,
                    if_exists=if_exists,
                    index=False,
                    **kwargs
                )
                temp_engine.dispose()

            logger.info(f"Wrote {len(df)} rows to table {table_name}")

        except Exception as e:
            logger.error(
                f"Failed to write DataFrame to table {table_name}: {str(e)}")
            raise

    def _track_sql_lineage(self, lineage_info, result_df: LineageDataFrame) -> None:
        """Track lineage information from SQL parsing."""
        try:
            # Create nodes for source tables
            for table_ref in lineage_info.source_tables:
                table_node_id = f"sqlite_table_{table_ref.full_name}"

                # Check if node already exists
                if table_node_id not in self.tracker.nodes:
                    from ..core.nodes import TableNode

                    # Get schema for the table
                    schema_info = self.get_schema(table_ref.name)

                    table_node = TableNode(
                        id=table_node_id,
                        name=table_ref.full_name,
                        columns=set(schema_info.keys()),
                        source_type="sqlite",
                        source_location=f"{self.database_path}/{table_ref.full_name}"
                    )

                    self.tracker.add_node(table_node)

            # Create lineage edge if we have source tables
            if lineage_info.source_tables:
                from ..core.edges import LineageEdge, TransformationType

                source_node_ids = [
                    f"sqlite_table_{table.full_name}" for table in lineage_info.source_tables]

                edge = LineageEdge(
                    source_node_ids=source_node_ids,
                    target_node_id=result_df._lineage_node_id,
                    transformation_type=TransformationType.CUSTOM,
                    operation_name=f"sqlite_{lineage_info.query_type.lower()}",
                    parameters={
                        'query': lineage_info.raw_query,
                        'query_type': lineage_info.query_type,
                        'operations': lineage_info.operations
                    },
                    input_columns=set(),  # Would need more sophisticated parsing
                    output_columns=set(result_df.columns)
                )

                self.tracker.add_edge(edge)

        except Exception as e:
            logger.error(f"Failed to track SQL lineage: {str(e)}")

    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information and statistics."""
        if not self.connection:
            return {'status': 'disconnected'}

        try:
            info = {
                'status': 'connected',
                'backend': 'sqlalchemy' if self.use_sqlalchemy else 'sqlite3',
                'database_path': self.database_path,
            }

            # Get SQLite version
            if self.use_sqlalchemy:
                result = self.connection.execute("SELECT sqlite_version()")
                version = result.fetchone()[0]
            else:
                cursor = self.connection.cursor()
                cursor.execute("SELECT sqlite_version()")
                version = cursor.fetchone()[0]
                cursor.close()

            info['sqlite_version'] = version

            # Get database file size (if not in-memory)
            if self.database_path != ':memory:' and os.path.exists(self.database_path):
                file_size_bytes = os.path.getsize(self.database_path)
                info['file_size_mb'] = round(
                    file_size_bytes / (1024 * 1024), 2)

            return info

        except Exception as e:
            logger.error(f"Failed to get connection info: {str(e)}")
            return {'status': 'error', 'error': str(e)}

    def test_connection(self) -> bool:
        """Test the SQLite connection."""
        try:
            if not self.connection:
                self.connect()

            # Simple test query
            if self.use_sqlalchemy:
                result = self.connection.execute("SELECT 1")
                result.fetchone()
            else:
                cursor = self.connection.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()

            return True

        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
