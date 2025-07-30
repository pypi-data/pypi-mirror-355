"""
PostgreSQL database connector with lineage tracking.
"""

import logging
from typing import Dict, Any, List, Optional, Union
import pandas as pd

from .base import BaseConnector
from .sql_parser import SQLLineageParser
from ..core.dataframe_wrapper import LineageDataFrame

logger = logging.getLogger(__name__)

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    logger.warning(
        "psycopg2 not available. PostgreSQL connector will be disabled.")

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import Engine
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    logger.warning(
        "SQLAlchemy not available. Some PostgreSQL features will be limited.")


class PostgreSQLConnector(BaseConnector):
    """
    PostgreSQL database connector with automatic lineage tracking.

    Supports both psycopg2 and SQLAlchemy backends for maximum flexibility.
    """

    def __init__(self, connection_string: str, use_sqlalchemy: bool = True, **kwargs):
        """
        Initialize PostgreSQL connector.

        Args:
            connection_string: PostgreSQL connection string
            use_sqlalchemy: Whether to use SQLAlchemy (recommended) or psycopg2
            **kwargs: Additional connection options
        """
        if not PSYCOPG2_AVAILABLE and not SQLALCHEMY_AVAILABLE:
            raise ImportError(
                "Either psycopg2 or SQLAlchemy is required for PostgreSQL connector")

        super().__init__(connection_string, **kwargs)
        self.use_sqlalchemy = use_sqlalchemy and SQLALCHEMY_AVAILABLE
        self.sql_parser = SQLLineageParser()
        self.engine: Optional[Engine] = None

    def connect(self) -> None:
        """Establish PostgreSQL connection."""
        try:
            if self.use_sqlalchemy:
                self.engine = create_engine(
                    self.connection_string, **self.options)
                self.connection = self.engine.connect()
                logger.info("Connected to PostgreSQL using SQLAlchemy")
            else:
                self.connection = psycopg2.connect(
                    self.connection_string, **self.options)
                logger.info("Connected to PostgreSQL using psycopg2")

        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {str(e)}")
            raise

    def disconnect(self) -> None:
        """Close PostgreSQL connection."""
        try:
            if self.connection:
                self.connection.close()
                self.connection = None

            if self.engine:
                self.engine.dispose()
                self.engine = None

            logger.info("Disconnected from PostgreSQL")

        except Exception as e:
            logger.error(f"Error disconnecting from PostgreSQL: {str(e)}")

    def read_table(self, table_name: str, schema: Optional[str] = None,
                   **kwargs) -> LineageDataFrame:
        """
        Read PostgreSQL table with lineage tracking.

        Args:
            table_name: Name of the table to read
            schema: Optional schema name (defaults to 'public')
            **kwargs: Additional pandas.read_sql options

        Returns:
            LineageDataFrame with tracked lineage
        """
        if not self.connection:
            self.connect()

        try:
            # Build table reference
            full_table_name = f'"{schema}"."{table_name}"' if schema else f'"{table_name}"'
            query = f"SELECT * FROM {full_table_name}"

            # Read data using pandas
            if self.use_sqlalchemy:
                df = pd.read_sql(query, self.connection, **kwargs)
            else:
                df = pd.read_sql_query(query, self.connection, **kwargs)

            # Create LineageDataFrame with database source tracking
            lineage_df = self._create_lineage_dataframe(df, table_name, schema)

            logger.info(
                f"Read table {full_table_name}: {df.shape[0]} rows, {df.shape[1]} columns")
            return lineage_df

        except Exception as e:
            logger.error(f"Failed to read table {table_name}: {str(e)}")
            raise

    def execute_query(self, query: str, **kwargs) -> LineageDataFrame:
        """
        Execute PostgreSQL query with lineage tracking.

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
            query_name = f"query_{hash(query) % 10000}"
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
        Get PostgreSQL table schema information.

        Args:
            table_name: Name of the table
            schema: Optional schema name (defaults to 'public')

        Returns:
            Dictionary mapping column names to data types
        """
        if not self.connection:
            self.connect()

        schema = schema or 'public'

        try:
            query = """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = %s AND table_schema = %s
                ORDER BY ordinal_position
            """

            if self.use_sqlalchemy:
                result = self.connection.execute(query, (table_name, schema))
                columns = result.fetchall()
            else:
                cursor = self.connection.cursor(cursor_factory=RealDictCursor)
                cursor.execute(query, (table_name, schema))
                columns = cursor.fetchall()
                cursor.close()

            schema_info = {}
            for col in columns:
                col_name = col['column_name'] if isinstance(
                    col, dict) else col[0]
                data_type = col['data_type'] if isinstance(
                    col, dict) else col[1]
                schema_info[col_name] = data_type

            return schema_info

        except Exception as e:
            logger.error(
                f"Failed to get schema for table {table_name}: {str(e)}")
            return {}

    def list_tables(self, schema: Optional[str] = None) -> List[str]:
        """
        List all tables in PostgreSQL database or schema.

        Args:
            schema: Optional schema name (defaults to 'public')

        Returns:
            List of table names
        """
        if not self.connection:
            self.connect()

        schema = schema or 'public'

        try:
            query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = %s AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """

            if self.use_sqlalchemy:
                result = self.connection.execute(query, (schema,))
                tables = [row[0] for row in result.fetchall()]
            else:
                cursor = self.connection.cursor()
                cursor.execute(query, (schema,))
                tables = [row[0] for row in cursor.fetchall()]
                cursor.close()

            return tables

        except Exception as e:
            logger.error(f"Failed to list tables in schema {schema}: {str(e)}")
            return []

    def _write_dataframe(self, df: pd.DataFrame, table_name: str,
                         schema: Optional[str], if_exists: str, **kwargs) -> None:
        """Write DataFrame to PostgreSQL table."""
        if not self.connection:
            self.connect()

        try:
            # Use pandas to_sql for writing
            if self.use_sqlalchemy:
                df.to_sql(
                    table_name,
                    self.connection,
                    schema=schema,
                    if_exists=if_exists,
                    index=False,
                    **kwargs
                )
            else:
                # For psycopg2, we need to create an engine temporarily
                from sqlalchemy import create_engine
                temp_engine = create_engine(self.connection_string)
                df.to_sql(
                    table_name,
                    temp_engine,
                    schema=schema,
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
                table_node_id = f"pg_table_{table_ref.full_name}"

                # Check if node already exists
                if table_node_id not in self.tracker.nodes:
                    from ..core.nodes import TableNode

                    # Get schema for the table
                    schema_info = self.get_schema(
                        table_ref.name, table_ref.schema)

                    table_node = TableNode(
                        id=table_node_id,
                        name=table_ref.full_name,
                        columns=set(schema_info.keys()),
                        source_type="postgresql",
                        source_location=f"{self.connection_string}/{table_ref.full_name}"
                    )

                    self.tracker.add_node(table_node)

            # Create lineage edge if we have source tables
            if lineage_info.source_tables:
                from ..core.edges import LineageEdge, TransformationType

                source_node_ids = [
                    f"pg_table_{table.full_name}" for table in lineage_info.source_tables]

                edge = LineageEdge(
                    source_node_ids=source_node_ids,
                    target_node_id=result_df._lineage_node_id,
                    transformation_type=TransformationType.CUSTOM,
                    operation_name=f"sql_{lineage_info.query_type.lower()}",
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
                'backend': 'sqlalchemy' if self.use_sqlalchemy else 'psycopg2',
                # Hide credentials
                'connection_string': self.connection_string.split('@')[-1],
            }

            # Get PostgreSQL version
            if self.use_sqlalchemy:
                result = self.connection.execute("SELECT version()")
                version = result.fetchone()[0]
            else:
                cursor = self.connection.cursor()
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                cursor.close()

            info['postgresql_version'] = version.split()[1]

            return info

        except Exception as e:
            logger.error(f"Failed to get connection info: {str(e)}")
            return {'status': 'error', 'error': str(e)}

    def test_connection(self) -> bool:
        """Test the PostgreSQL connection."""
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
